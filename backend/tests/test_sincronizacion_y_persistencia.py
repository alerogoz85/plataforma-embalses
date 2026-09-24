from datetime import date, datetime, timedelta, timezone

import duckdb
import pytest

from application.ports.output.fuente_mediciones_port import DescargaMediciones, FuenteMedicionesPort
from application.use_cases.obtener_fuente_datos import ObtenerFuenteDatosUseCase
from application.use_cases.sincronizar_datos import DIAS_REVISION, SincronizarDatosUseCase
from domain.entities.metadatos_datos import MetadatosDatos
from domain.entities.region import NombreRegion
from domain.exceptions import EsquemaIncompatibleError
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_embalse_repository import DuckDBEmbalseRepository
from infrastructure.persistence.duckdb_medicion_repository import DuckDBMedicionRepository
from infrastructure.persistence.duckdb_metadatos_repository import DuckDBMetadatosRepository
from tests.fakes import (
    EmbalseRepositoryEnMemoria,
    MedicionRepositoryEnMemoria,
    MetadatosRepositoryEnMemoria,
    caudal,
    crear_embalse,
    crear_medicion,
)

EMBALSE = crear_embalse("A", NombreRegion.CALDAS)


class FuenteFalsa(FuenteMedicionesPort):
    def __init__(self, es_real=True, mediciones=None):
        self.llamadas = []
        self.es_real = es_real
        self._mediciones = mediciones

    def descargar(self, desde, hasta):
        self.llamadas.append((desde, hasta))
        mediciones = self._mediciones
        if mediciones is None:
            n = (hasta - desde).days + 1
            mediciones = [crear_medicion(EMBALSE, desde + timedelta(days=i), 50.0) for i in range(n)]
        return DescargaMediciones([EMBALSE], mediciones, "Fuente de prueba", "desc", self.es_real)


def _caso(fuente=None, mediciones=()):
    fuente = fuente or FuenteFalsa()
    repos = (
        EmbalseRepositoryEnMemoria([]),
        MedicionRepositoryEnMemoria(list(mediciones)),
        MetadatosRepositoryEnMemoria(),
    )
    return SincronizarDatosUseCase(fuente, *repos), fuente, repos


class TestSincronizarDatos:
    def test_primera_carga_usa_la_fecha_inicial_por_defecto(self):
        caso, fuente, _ = _caso()
        caso.ejecutar(desde_por_defecto=date(2026, 1, 1), hasta=date(2026, 1, 10))
        assert fuente.llamadas == [(date(2026, 1, 1), date(2026, 1, 10))]

    def test_carga_incremental_repite_los_ultimos_dias_para_recoger_revisiones(self):
        previas = [crear_medicion(EMBALSE, date(2026, 1, 20), 50.0)]
        caso, fuente, _ = _caso(mediciones=previas)
        caso.ejecutar(desde_por_defecto=date(2020, 1, 1), hasta=date(2026, 1, 25))
        assert fuente.llamadas[0][0] == date(2026, 1, 20) - timedelta(days=DIAS_REVISION)

    def test_un_desde_explicito_tiene_prioridad(self):
        previas = [crear_medicion(EMBALSE, date(2026, 1, 20), 50.0)]
        caso, fuente, _ = _caso(mediciones=previas)
        caso.ejecutar(desde_por_defecto=date(2020, 1, 1), desde=date(2025, 6, 1), hasta=date(2026, 1, 25))
        assert fuente.llamadas[0][0] == date(2025, 6, 1)

    def test_guarda_embalses_mediciones_y_procedencia(self):
        caso, _, (embalses, mediciones, metadatos) = _caso()
        resultado = caso.ejecutar(desde_por_defecto=date(2026, 1, 1), hasta=date(2026, 1, 5))

        assert resultado.mediciones == 5 and resultado.fecha_corte == date(2026, 1, 5)
        assert embalses.obtener_por_id("A") is not None
        assert mediciones.obtener_ultima_fecha() == date(2026, 1, 5)
        assert metadatos.guardado.fecha_corte == date(2026, 1, 5)
        assert metadatos.guardado.fuente == "Fuente de prueba"
        assert metadatos.guardado.es_real is True

    def test_registra_cuando_los_datos_no_son_reales(self):
        caso, _, (_, _, metadatos) = _caso(FuenteFalsa(es_real=False))
        caso.ejecutar(desde_por_defecto=date(2026, 1, 1), hasta=date(2026, 1, 2))
        assert metadatos.guardado.es_real is False

    def test_es_idempotente_no_duplica_mediciones(self):
        caso, _, (_, mediciones, _) = _caso()
        for _ in range(2):
            caso.ejecutar(desde_por_defecto=date(2026, 1, 1), desde=date(2026, 1, 1), hasta=date(2026, 1, 5))
        assert len(mediciones.obtener_serie("A")) == 5

    def test_la_fecha_de_corte_es_la_de_la_base_no_la_del_rango_pedido(self):
        caso, _, (_, _, metadatos) = _caso(FuenteFalsa(mediciones=[crear_medicion(EMBALSE, date(2026, 1, 3), 50.0)]))
        caso.ejecutar(desde_por_defecto=date(2026, 1, 1), hasta=date(2026, 1, 30))
        assert metadatos.guardado.fecha_corte == date(2026, 1, 3)


class TestObtenerFuenteDatos:
    def test_sin_datos_lo_dice_y_no_afirma_que_sean_reales(self):
        dto = ObtenerFuenteDatosUseCase(MetadatosRepositoryEnMemoria()).ejecutar()
        assert dto.fuente == "Sin datos" and dto.es_real is False and dto.fecha_corte is None

    def test_informa_la_procedencia_guardada(self):
        repo = MetadatosRepositoryEnMemoria()
        repo.guardar(MetadatosDatos("SIMEM", "d", date(2026, 9, 22), datetime(2026, 9, 23, tzinfo=timezone.utc), True))
        dto = ObtenerFuenteDatosUseCase(repo).ejecutar()
        assert (dto.fuente, dto.es_real, dto.fecha_corte) == ("SIMEM", True, date(2026, 9, 22))


@pytest.fixture
def conexion(tmp_path):
    conexion = DuckDBConnection(str(tmp_path / "prueba.duckdb"))
    yield conexion
    conexion.cerrar()


class TestPersistenciaDuckDB:
    def test_los_datos_opcionales_no_publicados_se_guardan_como_nulos(self, conexion):
        repo = DuckDBMedicionRepository(conexion)
        repo.guardar_lote([crear_medicion(EMBALSE, date(2026, 1, 1), 40.0, energia_util_gwh=None)])
        leida = repo.obtener_ultima_medicion("A")
        assert leida.aportes is None and leida.turbinado is None and leida.vertimientos is None
        assert leida.aportes_media_historica_m3s is None and leida.energia_util_gwh is None

    def test_ida_y_vuelta_conserva_todos_los_campos(self, conexion):
        repo = DuckDBMedicionRepository(conexion)
        original = crear_medicion(
            EMBALSE, date(2026, 1, 1), 40.0, capacidad_energia_gwh=250.0,
            aportes=caudal(12.5), aportes_media_historica_m3s=20.0,
            vertimientos=caudal(1.5), turbinado=caudal(30.0),
        )
        repo.guardar_lote([original])
        assert repo.obtener_medicion_en_fecha("A", date(2026, 1, 1)) == original

    def test_reescribir_la_misma_fecha_actualiza_en_lugar_de_duplicar(self, conexion):
        repo = DuckDBMedicionRepository(conexion)
        repo.guardar_lote([crear_medicion(EMBALSE, date(2026, 1, 1), 40.0)])
        repo.guardar_lote([crear_medicion(EMBALSE, date(2026, 1, 1), 55.0)])
        serie = repo.obtener_serie("A")
        assert len(serie) == 1
        assert serie[0].volumen_util.valor_mm3 == pytest.approx(55.0)

    def test_filtra_la_serie_por_rango_y_devuelve_la_ultima_fecha(self, conexion):
        repo = DuckDBMedicionRepository(conexion)
        repo.guardar_lote([crear_medicion(EMBALSE, date(2026, 1, d), 50.0) for d in range(1, 11)])
        assert [m.fecha.day for m in repo.obtener_serie("A", date(2026, 1, 3), date(2026, 1, 5))] == [3, 4, 5]
        assert repo.obtener_ultima_fecha() == date(2026, 1, 10)

    def test_ultima_fecha_es_none_con_la_base_vacia(self, conexion):
        assert DuckDBMedicionRepository(conexion).obtener_ultima_fecha() is None

    def test_embalses_ida_y_vuelta_y_filtro_por_region(self, conexion):
        repo = DuckDBEmbalseRepository(conexion)
        repo.guardar(EMBALSE)
        repo.guardar(crear_embalse("B", NombreRegion.CARIBE, es_agregado=True))
        assert repo.obtener_por_id("A") == EMBALSE
        assert [e.id for e in repo.listar(NombreRegion.CARIBE)] == ["B"]
        assert repo.obtener_por_id("B").es_agregado is True

    def test_procedencia_se_guarda_y_se_actualiza_con_hora_utc(self, conexion):
        repo = DuckDBMetadatosRepository(conexion)
        assert repo.obtener() is None
        momento = datetime(2026, 9, 23, 17, 46, tzinfo=timezone.utc)
        repo.guardar(MetadatosDatos("SIMEM", "d", date(2026, 9, 22), momento, True))
        repo.guardar(MetadatosDatos("SIMEM", "d2", date(2026, 9, 23), momento, True))
        leido = repo.obtener()
        assert leido.descripcion == "d2" and leido.fecha_corte == date(2026, 9, 23)
        assert leido.actualizado_en == momento


class TestEsquemaHeredado:
    def _crear_base_antigua(self, ruta):
        con = duckdb.connect(ruta)
        con.execute("CREATE TABLE mediciones (embalse_id VARCHAR, fecha DATE, cota_actual DOUBLE)")
        con.execute("INSERT INTO mediciones VALUES ('X', DATE '2026-01-01', 1.0)")
        con.close()

    def test_una_base_con_el_esquema_sintetico_anterior_se_rechaza_explicitamente(self, tmp_path):
        ruta = str(tmp_path / "vieja.duckdb")
        self._crear_base_antigua(ruta)
        with pytest.raises(EsquemaIncompatibleError, match="--reiniciar"):
            DuckDBConnection(ruta)

    def test_reiniciar_reemplaza_el_esquema_anterior(self, tmp_path):
        ruta = str(tmp_path / "vieja.duckdb")
        self._crear_base_antigua(ruta)
        conexion = DuckDBConnection(ruta, reiniciar=True)
        DuckDBMedicionRepository(conexion).guardar_lote([crear_medicion(EMBALSE, date(2026, 1, 1), 50.0)])
        assert DuckDBMedicionRepository(conexion).obtener_ultima_fecha() == date(2026, 1, 1)
        conexion.cerrar()

    def test_una_base_nueva_o_actual_abre_sin_reiniciar(self, tmp_path):
        ruta = str(tmp_path / "nueva.duckdb")
        DuckDBConnection(ruta).cerrar()
        DuckDBConnection(ruta).cerrar()
