"""Base externa (Postgres): traduccion del esquema y, si hay un servidor de prueba (TEST_DATABASE_URL), los mismos repositorios sobre Postgres
y la migracion desde DuckDB. Sin TEST_DATABASE_URL las pruebas que necesitan servidor se omiten."""
import os
from datetime import datetime

import pytest

from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_escenario_apagon_repository import DuckDBEscenarioApagonRepository
from infrastructure.persistence.duckdb_modelo_carbon_repository import DuckDBModeloCarbonRepository
from infrastructure.persistence.duckdb_modelo_dns_repository import DuckDBModeloDnsRepository
from infrastructure.persistence.duckdb_modelo_resultado_repository import DuckDBModeloResultadoRepository
from infrastructure.persistence.migrar_a_postgres import migrar, tablas_a_migrar
from infrastructure.persistence.postgres_connection import PostgresConnection, adaptar_consulta, esquema_postgres
from infrastructure.persistence.sql_seguridad_repository import SqlAuditoriaRepository, SqlSesionRepository, SqlUsuarioRepository
from domain.entities.seguridad import CredencialUsuario, RegistroAuditoria, Sesion, Usuario
from tests.fakes import crear_paquete_carbon, crear_paquete_dns, crear_resultado_modelo
from tests.test_escenarios_apagon import FUENTE, escenario

DSN = os.environ.get("TEST_DATABASE_URL")
requiere_postgres = pytest.mark.skipif(not DSN, reason="define TEST_DATABASE_URL para probar contra un Postgres")


class TestTraduccion:
    def test_los_marcadores_y_el_porcentaje_se_adaptan(self):
        assert adaptar_consulta("SELECT * FROM t WHERE a = ? AND b LIKE '50%' LIMIT ?") == "SELECT * FROM t WHERE a = %s AND b LIKE '50%%' LIMIT %s"

    def test_el_esquema_trae_solo_modelos_y_seguridad_con_tipos_de_postgres(self):
        ddl = esquema_postgres()
        for tabla in ("carbon_meta", "dns_eventos", "modelo_resultados", "modelo_escenarios", "seg_usuarios", "seg_sesiones", "seg_auditoria"):
            assert f"CREATE TABLE IF NOT EXISTS {tabla}" in ddl
        for tabla in ("mediciones", "embalses", "fuente_datos"):  # embalses sigue en el DuckDB empaquetado
            assert f"CREATE TABLE IF NOT EXISTS {tabla}" not in ddl
        assert "DOUBLE PRECISION" in ddl and " DOUBLE " not in ddl.replace("DOUBLE PRECISION", "")
        assert "DOUBLE PRECISION PRECISION" not in ddl


@pytest.fixture
def pg():
    conexion = PostgresConnection(DSN)
    tablas = [f[0] for f in conexion.obtener_filas("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")]
    for t in tablas:
        conexion.ejecutar(f"DROP TABLE IF EXISTS {t}")
    conexion.ejecutar_script(esquema_postgres())
    yield conexion
    conexion.cerrar()


@requiere_postgres
class TestRepositoriosSobrePostgres:
    def test_resultados_de_modelos(self, pg):
        repo = DuckDBModeloResultadoRepository(pg)
        assert repo.obtener("apagon") is None
        r = crear_resultado_modelo("apagon")
        repo.reemplazar(r)
        assert repo.obtener("apagon") == r
        repo.reemplazar(crear_resultado_modelo("apagon"))
        assert pg.obtener_una_fila("SELECT COUNT(*) FROM modelo_resultados")[0] == 1

    def test_escenarios_del_visor(self, pg):
        repo = DuckDBEscenarioApagonRepository(pg)
        e = escenario()
        repo.reemplazar([e], FUENTE)
        assert repo.obtener("manual", 1.0, 2000, 12) == e and repo.fuente() == FUENTE

    def test_modelo_dns_ida_y_vuelta(self, pg):
        repo = DuckDBModeloDnsRepository(pg)
        p = crear_paquete_dns()
        repo.reemplazar(p)
        leido = repo.obtener()
        assert leido.eventos == sorted(p.eventos, key=lambda e: e.fecha_hora) and sorted(leido.zonas, key=lambda z: z.ranking) == sorted(p.zonas, key=lambda z: z.ranking)
        assert sorted(leido.pronostico, key=lambda f: f.codigo_subarea) == sorted(p.pronostico, key=lambda f: f.codigo_subarea)

    def test_modelo_carbon_ida_y_vuelta(self, pg):
        repo = DuckDBModeloCarbonRepository(pg)
        p = crear_paquete_carbon()
        repo.reemplazar(p)
        leido = repo.obtener()
        assert leido.proyeccion == p.proyeccion and leido.historico == p.historico and leido.veredicto == p.veredicto

    def test_un_reemplazo_que_falla_no_deja_la_tabla_a_medias(self, pg):
        repo = DuckDBModeloResultadoRepository(pg)
        repo.reemplazar(crear_resultado_modelo("gas"))
        class Malo:
            modelo_id = "gas"
            generado_en = datetime(2026, 1, 1)
        with pytest.raises(Exception):
            repo.reemplazar(Malo())  # type: ignore[arg-type]
        assert repo.obtener("gas") is not None

    def test_seguridad_usuarios_sesiones_y_bitacora(self, pg):
        usuarios, sesiones, aud = SqlUsuarioRepository(pg), SqlSesionRepository(pg), SqlAuditoriaRepository(pg)
        usuarios.guardar(CredencialUsuario(Usuario("ana", "Ana", "cargador", ("gas", "dns")), "hash"))
        c = usuarios.obtener("ana")
        assert c.usuario.tableros_permitidos == ("gas", "dns") and c.intentos_fallidos == 0
        usuarios.registrar_resultado_acceso("ana", 3, datetime(2026, 1, 1, 10))
        assert usuarios.obtener("ana").intentos_fallidos == 3 and usuarios.obtener("ana").bloqueado_hasta == datetime(2026, 1, 1, 10)
        ahora = datetime(2026, 1, 1, 9)
        s = Sesion("h" * 64, "ana", "csrf", ahora, ahora, "1.1.1.1")
        sesiones.crear(s)
        assert sesiones.obtener("h" * 64) == s
        sesiones.registrar_actividad("h" * 64, datetime(2026, 1, 1, 9, 5))
        assert sesiones.obtener("h" * 64).ultima_actividad == datetime(2026, 1, 1, 9, 5)
        sesiones.revocar_de_usuario("ana")
        assert sesiones.obtener("h" * 64) is None
        aud.registrar(RegistroAuditoria(ahora, "ana", "inicio_sesion_fallido", None, "rechazado", "x", "2.2.2.2"))
        assert aud.contar_fallos_desde_ip("2.2.2.2", datetime(2026, 1, 1)) == 1
        assert aud.listar(5)[0].ip == "2.2.2.2"

    def test_reconecta_si_la_conexion_se_cayo(self, pg):
        pg._conexion.close()  # simula que la base serverless cerro la conexion por inactividad
        assert pg.obtener_una_fila("SELECT 1")[0] == 1


@requiere_postgres
class TestMigracion:
    def test_copia_modelos_y_usuarios_pero_no_embalses_ni_sesiones(self, pg, tmp_path):
        origen = DuckDBConnection(str(tmp_path / "o.duckdb"))
        DuckDBModeloDnsRepository(origen).reemplazar(crear_paquete_dns())
        DuckDBModeloResultadoRepository(origen).reemplazar(crear_resultado_modelo("apagon"))
        DuckDBEscenarioApagonRepository(origen).reemplazar([escenario()], FUENTE)
        SqlUsuarioRepository(origen).guardar(CredencialUsuario(Usuario("ana", "Ana", "administrador", ()), "hash"))
        ahora = datetime(2026, 1, 1)
        SqlSesionRepository(origen).crear(Sesion("h" * 64, "ana", "c", ahora, ahora, "ip"))
        assert "seg_sesiones" not in tablas_a_migrar(origen) and "mediciones" not in tablas_a_migrar(origen)
        copiadas = migrar(origen, pg)
        assert copiadas["dns_eventos"] == len(crear_paquete_dns().eventos) and copiadas["seg_usuarios"] == 1
        assert DuckDBModeloDnsRepository(pg).obtener().eventos == DuckDBModeloDnsRepository(origen).obtener().eventos
        assert DuckDBModeloResultadoRepository(pg).obtener("apagon") is not None
        assert DuckDBEscenarioApagonRepository(pg).obtener("manual", 1.0, 2000, 12) is not None
        assert SqlUsuarioRepository(pg).obtener("ana").hash_contrasena == "hash"
        assert pg.obtener_una_fila("SELECT COUNT(*) FROM seg_sesiones")[0] == 0

    def test_migrar_dos_veces_no_duplica(self, pg, tmp_path):
        origen = DuckDBConnection(str(tmp_path / "o.duckdb"))
        DuckDBModeloDnsRepository(origen).reemplazar(crear_paquete_dns())
        migrar(origen, pg)
        migrar(origen, pg)
        assert pg.obtener_una_fila("SELECT COUNT(*) FROM dns_meta")[0] == 1
