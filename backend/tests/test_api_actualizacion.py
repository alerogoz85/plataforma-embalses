"""Contrato HTTP del modulo de actualizacion (/api/v1/admin): sesion por cookie, CSRF, permisos y el flujo validar -> aplicar."""
import json

import pytest
from fastapi.testclient import TestClient

from application.use_cases.actualizacion import ActualizarTableroUseCase, ListarTablerosActualizablesUseCase
from application.use_cases.seguridad import (
    CerrarSesionUseCase,
    IniciarSesionUseCase,
    ListarAuditoriaUseCase,
    ObtenerSesionUseCase,
)
from domain.entities.seguridad import CredencialUsuario, Usuario
from infrastructure.actualizacion.tableros import construir_adaptadores
from infrastructure.archivos.area_trabajo import AreaTemporal
from infrastructure.archivos.validador import limite_de_bytes, validar_archivo
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_escenario_apagon_repository import DuckDBEscenarioApagonRepository
from infrastructure.persistence.duckdb_modelo_carbon_repository import DuckDBModeloCarbonRepository
from infrastructure.persistence.duckdb_modelo_dns_repository import DuckDBModeloDnsRepository
from infrastructure.persistence.duckdb_modelo_resultado_repository import DuckDBModeloResultadoRepository
from infrastructure.persistence.sql_seguridad_repository import SqlAuditoriaRepository, SqlSesionRepository, SqlUsuarioRepository
from infrastructure.seguridad import contrasenas
from presentation.api import dependencies as dep
from presentation.api.main import app
from tests.test_modelos_analiticos import escribir_apagon
from tests.test_seguridad_actualizacion import CONTRASENA, RelojFalso, _Contrasenas

U = "/api/v1/admin"
JSON_OPT = {"classification": "INSUFFICIENT_RISK_SAMPLE", "publishable": False, "etapas": 82}


class Entorno:
    def __init__(self, tmp_path, persistente=True):
        self.db = DuckDBConnection(str(tmp_path / "a.duckdb"))
        self.reloj = RelojFalso()
        usuarios, sesiones, self.auditoria = SqlUsuarioRepository(self.db), SqlSesionRepository(self.db), SqlAuditoriaRepository(self.db)
        h = contrasenas.hashear(CONTRASENA)
        usuarios.guardar(CredencialUsuario(Usuario("ana", "Ana", "administrador", ()), h))
        usuarios.guardar(CredencialUsuario(Usuario("luis", "Luis", "cargador", ("optimizacion",)), h))
        self.resultados = DuckDBModeloResultadoRepository(self.db)
        self.adaptadores = construir_adaptadores(DuckDBModeloCarbonRepository(self.db), DuckDBModeloDnsRepository(self.db), self.resultados, DuckDBEscenarioApagonRepository(self.db))
        ids = list(self.adaptadores)
        persiste = lambda: persistente  # noqa: E731
        app.dependency_overrides.update({
            dep.obtener_iniciar_sesion_use_case: lambda: IniciarSesionUseCase(usuarios, sesiones, self.auditoria, _Contrasenas(), self.reloj),
            dep.obtener_sesion_use_case: lambda: ObtenerSesionUseCase(usuarios, sesiones, self.reloj),
            dep.obtener_cerrar_sesion_use_case: lambda: CerrarSesionUseCase(sesiones, self.auditoria, self.reloj),
            dep.obtener_listar_auditoria_use_case: lambda: ListarAuditoriaUseCase(self.auditoria),
            dep.obtener_listar_tableros_use_case: lambda: ListarTablerosActualizablesUseCase(self.adaptadores, lambda: (limite_de_bytes(), 4_400_000, 60 * 1024 * 1024), persiste),
            dep.obtener_actualizar_tablero_use_case: lambda: ActualizarTableroUseCase(self.adaptadores, AreaTemporal(), validar_archivo, self.auditoria, self.reloj, persiste),
            dep.obtener_ids_tableros_actualizables: lambda: ids,
        })


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    monkeypatch.setattr(contrasenas, "N", 2**10)
    yield Entorno(tmp_path)
    app.dependency_overrides.clear()


@pytest.fixture
def sin_persistencia(tmp_path, monkeypatch):
    monkeypatch.setattr(contrasenas, "N", 2**10)
    yield Entorno(tmp_path, persistente=False)
    app.dependency_overrides.clear()


def entrar(usuario="ana", contrasena=CONTRASENA):
    c = TestClient(app)
    r = c.post(f"{U}/sesion", json={"usuario": usuario, "contrasena": contrasena})
    return c, r


def csrf(c_r):
    return {"X-CSRF-Token": c_r[1].json()["token_csrf"]}


def archivos_opt(resumen=JSON_OPT, nombre="resumen.json"):
    return {"files": [("archivos", (nombre, json.dumps(resumen).encode(), "application/json"))], "data": {"claves": ["resumen"]}}


class TestSesionHttp:
    def test_inicio_correcto_cookie_httponly_samesite_estricta_y_ruta_acotada(self, entorno):
        c, r = entrar()
        assert r.status_code == 200
        cookie = r.headers["set-cookie"].lower()
        assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api/v1/admin" in cookie
        cuerpo = r.json()
        assert cuerpo["usuario"]["nombre_usuario"] == "ana" and cuerpo["token_csrf"] and cuerpo["vence_en"].endswith("Z")
        assert "contrasena" not in json.dumps(cuerpo).lower() and "hash" not in json.dumps(cuerpo).lower()
        assert r.headers["cache-control"] == "no-store" and r.headers["x-content-type-options"] == "nosniff"

    def test_credenciales_incorrectas_401_sin_cookie(self, entorno):
        c, r = entrar("ana", "incorrecta")
        assert r.status_code == 401 and "set-cookie" not in r.headers and r.json()["detalle"] == "Usuario o contraseña incorrectos"

    def test_bloqueo_responde_429_con_retry_after(self, entorno):
        for _ in range(4):
            assert entrar("ana", "mala")[1].status_code == 401
        r = entrar("ana", "mala")[1]
        assert r.status_code == 429 and int(r.headers["retry-after"]) == 900

    def test_sin_sesion_todo_es_401(self, entorno):
        c = TestClient(app)
        assert c.get(f"{U}/sesion").status_code == 401
        assert c.get(f"{U}/tableros").status_code == 401
        assert c.get(f"{U}/auditoria").status_code == 401
        assert c.post(f"{U}/tableros/gas/validar", files=[("archivos", ("a.csv", b"a", "text/csv"))], data={"claves": ["x"]}).status_code == 401

    def test_cookie_falsa_no_sirve(self, entorno):
        c = TestClient(app)
        c.cookies.set("sesion_tableros", "inventada", path="/api/v1/admin")
        assert c.get(f"{U}/sesion").status_code == 401

    def test_cerrar_sesion_exige_csrf_y_la_invalida(self, entorno):
        cr = entrar()
        c = cr[0]
        assert c.delete(f"{U}/sesion").status_code == 401  # sin CSRF
        assert c.get(f"{U}/sesion").status_code == 200
        assert c.delete(f"{U}/sesion", headers=csrf(cr)).status_code == 204
        assert c.get(f"{U}/sesion").status_code == 401

    def test_entradas_invalidas_son_422_no_500(self, entorno):
        c = TestClient(app)
        assert c.post(f"{U}/sesion", json={"usuario": "", "contrasena": "x"}).status_code == 422
        assert c.post(f"{U}/sesion", json={"usuario": "a" * 500, "contrasena": "x"}).status_code == 422
        assert c.post(f"{U}/sesion", content=b"no-json").status_code == 422


class TestPermisosHttp:
    def test_el_cargador_solo_ve_su_tablero(self, entorno):
        c, _ = entrar("luis")
        assert [t["id"] for t in c.get(f"{U}/tableros").json()["tableros"]] == ["optimizacion"]

    def test_el_admin_ve_todos_con_sus_archivos_y_el_limite(self, entorno):
        c, _ = entrar()
        cat = c.get(f"{U}/tableros").json()
        assert {t["id"] for t in cat["tableros"]} == {"carbon", "dns", "gas", "optimizacion", "apagon", "apagon_visor"}
        assert cat["limite_bytes"] == 4 * 1024 * 1024 and cat["almacenamiento_persistente"] is True
        gas = next(t for t in cat["tableros"] if t["id"] == "gas")
        assert gas["archivos"][0]["clave"] == "v2" and gas["archivos"][0]["obligatorio"] and gas["archivos"][0]["formatos"] == ["xlsx"]

    def test_el_cargador_no_puede_tocar_otro_tablero_y_queda_en_bitacora(self, entorno):
        cr = entrar("luis")
        c = cr[0]
        r = c.post(f"{U}/tableros/gas/validar", headers=csrf(cr), **archivos_opt())
        assert r.status_code == 403
        r = c.post(f"{U}/tableros/gas/aplicar", headers=csrf(cr), data={"claves": ["resumen"], "huellas": ["x"]}, files=archivos_opt()["files"])
        assert r.status_code == 403
        assert entorno.auditoria.listar(1)[0].accion == "acceso_denegado"
        assert entorno.resultados.obtener("gas") is None

    def test_tablero_inexistente_404(self, entorno):
        cr = entrar()
        assert cr[0].post(f"{U}/tableros/embalses/validar", headers=csrf(cr), **archivos_opt()).status_code == 404
        assert cr[0].post(f"{U}/tableros/..%2f..%2fetc/validar", headers=csrf(cr), **archivos_opt()).status_code in (404, 422)

    def test_la_bitacora_es_solo_del_admin(self, entorno):
        assert entrar()[0].get(f"{U}/auditoria").status_code == 200
        assert entrar("luis")[0].get(f"{U}/auditoria").status_code == 403


class TestCargaHttp:
    def test_post_sin_csrf_se_rechaza_aunque_haya_sesion(self, entorno):
        c, _ = entrar()
        assert c.post(f"{U}/tableros/optimizacion/validar", **archivos_opt()).status_code == 401
        assert c.post(f"{U}/tableros/optimizacion/validar", headers={"X-CSRF-Token": "falso"}, **archivos_opt()).status_code == 401

    def test_validar_no_escribe_y_devuelve_el_resumen_con_las_huellas(self, entorno):
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), **archivos_opt())
        assert r.status_code == 200
        d = r.json()
        assert d["valido"] and not d["aplicada"] and d["errores"] == [] and d["huellas"][0]["clave"] == "resumen" and len(d["huellas"][0]["sha256"]) == 64
        assert any(x["etiqueta"] == "Indicadores" for x in d["resumen"])
        assert entorno.resultados.obtener("optimizacion") is None  # validar nunca escribe

    def test_flujo_completo_validar_y_aplicar_actualiza_el_tablero(self, entorno):
        cr = entrar()
        c, h = cr[0], csrf(cr)
        v = c.post(f"{U}/tableros/optimizacion/validar", headers=h, **archivos_opt()).json()
        r = c.post(f"{U}/tableros/optimizacion/aplicar", headers=h, files=archivos_opt()["files"],
                   data={"claves": ["resumen"], "huellas": [v["huellas"][0]["sha256"]]})
        assert r.status_code == 200 and r.json()["aplicada"] is True
        assert entorno.resultados.obtener("optimizacion").indicadores
        acciones = [(x.accion, x.resultado) for x in entorno.auditoria.listar(5)]
        assert ("actualizacion", "ok") in acciones and ("validacion", "ok") in acciones
        detalle = next(x for x in entorno.auditoria.listar(5) if x.accion == "actualizacion").detalle
        assert "resumen:" in detalle  # queda la huella de lo cargado

    def test_aplicar_con_archivos_distintos_a_los_validados_se_rechaza(self, entorno):
        cr = entrar()
        c, h = cr[0], csrf(cr)
        v = c.post(f"{U}/tableros/optimizacion/validar", headers=h, **archivos_opt()).json()
        otro = archivos_opt({**JSON_OPT, "etapas": 999})
        r = c.post(f"{U}/tableros/optimizacion/aplicar", headers=h, files=otro["files"], data={"claves": ["resumen"], "huellas": [v["huellas"][0]["sha256"]]})
        assert r.status_code == 422 and "no coinciden" in r.json()["detalle"]
        assert entorno.resultados.obtener("optimizacion") is None

    def test_aplicar_revalida_aunque_las_huellas_coincidan(self, entorno):
        cr = entrar()
        c, h = cr[0], csrf(cr)
        malo = archivos_opt({"solo": "texto"})  # JSON valido pero sin valores simples utiles? el lector lo decide
        malo["files"] = [("archivos", ("resumen.json", b"[]", "application/json"))]
        import hashlib
        huella = hashlib.sha256(b"[]").hexdigest()
        r = c.post(f"{U}/tableros/optimizacion/aplicar", headers=h, files=malo["files"], data={"claves": ["resumen"], "huellas": [huella]})
        assert r.status_code == 422 and r.json()["errores"]
        assert entorno.resultados.obtener("optimizacion") is None

    @pytest.mark.parametrize("nombre,contenido,motivo", [
        ("resumen.exe", b"MZ", "no admitido"),
        ("resumen.json", b"{no es json", "JSON"),
        ("../resumen.json", b"{}", "caracteres no permitidos"),
        ("resumen.json", b"", "vacío"),
    ])
    def test_archivos_invalidos_se_reportan_sin_leerse(self, entorno, nombre, contenido, motivo):
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), files=[("archivos", (nombre, contenido, "x/y"))], data={"claves": ["resumen"]})
        assert r.status_code == 200 and not r.json()["valido"] and motivo in " ".join(r.json()["errores"])

    def test_falta_un_archivo_obligatorio_y_archivo_no_esperado(self, entorno):
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), files=[("archivos", ("a.json", b"{}", "x/y"))], data={"claves": ["otro"]}).json()
        assert not r["valido"]
        assert any("no esperado" in e for e in r["errores"]) and any("obligatorio" in e for e in r["errores"])

    def test_archivo_repetido(self, entorno):
        cr = entrar()
        f = [("archivos", ("a.json", b"{}", "x/y")), ("archivos", ("b.json", b"{}", "x/y"))]
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), files=f, data={"claves": ["resumen", "resumen"]}).json()
        assert any("más de una vez" in e for e in r["errores"])

    def test_cantidad_de_claves_distinta_a_la_de_archivos_es_422(self, entorno):
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), files=[("archivos", ("a.json", b"{}", "x/y"))], data={"claves": ["resumen", "validacion"]})
        assert r.status_code == 422

    def test_un_archivo_enorme_se_rechaza_sin_cargarse_entero(self, entorno, monkeypatch):
        monkeypatch.setenv("MAX_UPLOAD_BYTES", "1000")
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), files=[("archivos", ("resumen.json", b'{"a":"' + b"x" * 50_000 + b'"}', "x/y"))], data={"claves": ["resumen"]})
        assert r.status_code == 422 and "pesa más de" in r.json()["detalle"] and ".gz" in r.json()["detalle"]  # nunca se acepta un archivo truncado

    def test_cuerpo_declarado_gigante_se_corta_antes_de_leerlo(self, entorno, monkeypatch):
        monkeypatch.setenv("MAX_UPLOAD_BYTES", "1000")
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers={**csrf(cr), "Content-Length": "99999999999"}, **archivos_opt())
        assert r.status_code == 422

    def test_apagon_resumen_csv_se_carga(self, entorno, tmp_path):
        carpeta = escribir_apagon(tmp_path / "p", ruta=("resultados_modelo_riesgo_apagon",))
        base = carpeta / "resultados_modelo_riesgo_apagon"
        files = [("archivos", ("resumen_mensual.csv", (base / "resumen_mensual.csv").read_bytes(), "text/csv")), ("archivos", ("d.csv", (base / "detalle_franjas_horarias.csv").read_bytes(), "text/csv"))]
        cr = entrar()
        v = cr[0].post(f"{U}/tableros/apagon/validar", headers=csrf(cr), files=files, data={"claves": ["resumen", "franjas"]}).json()
        assert v["valido"], v["errores"]
        h = [x["sha256"] for x in v["huellas"]]
        r = cr[0].post(f"{U}/tableros/apagon/aplicar", headers=csrf(cr), files=files, data={"claves": ["resumen", "franjas"], "huellas": h})
        assert r.status_code == 200 and entorno.resultados.obtener("apagon") is not None

    def test_un_csv_con_columnas_equivocadas_se_explica(self, entorno):
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/apagon/validar", headers=csrf(cr), files=[("archivos", ("r.csv", b"a,b\n1,2\n", "text/csv"))], data={"claves": ["resumen"]}).json()
        assert not r["valido"] and r["errores"] and "columna" in r["errores"][0].lower()

    def test_un_xlsx_corrupto_no_rompe_el_servicio(self, entorno):
        import io, zipfile
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("[Content_Types].xml", "<Types/>")
            z.writestr("xl/workbook.xml", "<workbook/>")
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/gas/validar", headers=csrf(cr), files=[("archivos", ("g.xlsx", b.getvalue(), "x/y"))], data={"claves": ["v2"]})
        assert r.status_code == 200 and not r.json()["valido"] and r.json()["errores"]


class TestSinAlmacenamientoPersistente:
    def test_validar_funciona_pero_aplicar_dice_503(self, sin_persistencia):
        cr = entrar()
        c, h = cr[0], csrf(cr)
        assert c.get(f"{U}/tableros", headers=h).json()["almacenamiento_persistente"] is False
        v = c.post(f"{U}/tableros/optimizacion/validar", headers=h, **archivos_opt()).json()
        r = c.post(f"{U}/tableros/optimizacion/aplicar", headers=h, files=archivos_opt()["files"], data={"claves": ["resumen"], "huellas": [v["huellas"][0]["sha256"]]})
        assert r.status_code == 503 and "DATABASE_URL" in r.json()["detalle"]
        assert sin_persistencia.resultados.obtener("optimizacion") is None


class TestRestoDeLaApiSigueSiendoDeSoloLectura:
    def test_post_fuera_del_modulo_sigue_siendo_405(self):
        c = TestClient(app)
        for ruta in ("/api/v1/embalses/resumen", "/api/v1/carbon/resumen", "/api/v1/modelos/apagon/ficha", "/api/v1/modelos/apagon/escenario"):
            assert c.post(ruta).status_code == 405
            assert c.delete(ruta).status_code == 405


class TestArchivosComprimidos:
    def _gz(self, datos: bytes) -> bytes:
        import gzip
        return gzip.compress(datos)

    def test_un_csv_mas_grande_que_el_limite_de_red_llega_comprimido(self, entorno, monkeypatch):
        monkeypatch.setenv("MAX_UPLOAD_BYTES", "2000")  # lo que viaja por la red
        csv = ("a,b\n" + "1,2\n" * 5000).encode()  # ~20 KB descomprimido, pocos bytes comprimidos
        assert len(csv) > 2000 and len(self._gz(csv)) < 2000
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/apagon/validar", headers=csrf(cr), files=[("archivos", ("resumen_mensual.csv.gz", self._gz(csv), "application/gzip"))], data={"claves": ["resumen"]})
        assert r.status_code == 200
        errores = " ".join(r.json()["errores"])
        assert "pesa" not in errores and "gz" not in errores and "columna" in errores.lower()  # paso los topes de tamaño; el lector dice que faltan columnas
        plano = cr[0].post(f"{U}/tableros/apagon/validar", headers=csrf(cr), files=[("archivos", ("resumen_mensual.csv", csv, "text/csv"))], data={"claves": ["resumen"]})
        assert plano.status_code == 422 and "comprimidos" in plano.json()["detalle"]

    def test_gzip_dañado_o_falso(self, entorno):
        cr = entrar()
        for contenido in (b"no es gzip", self._gz(b"a,b\n1,2\n")[:-6]):
            r = cr[0].post(f"{U}/tableros/apagon/validar", headers=csrf(cr), files=[("archivos", ("resumen_mensual.csv.gz", contenido, "x/y"))], data={"claves": ["resumen"]})
            assert r.status_code == 422 and "gz" in r.json()["detalle"]

    def test_bomba_gzip_se_corta_al_llegar_al_tope(self, entorno, monkeypatch):
        monkeypatch.setenv("MAX_CONTENT_BYTES", "10000")
        bomba = self._gz(b"0" * 5_000_000)
        assert len(bomba) < 10_000
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/apagon/validar", headers=csrf(cr), files=[("archivos", ("resumen_mensual.csv.gz", bomba, "x/y"))], data={"claves": ["resumen"]})
        assert r.status_code == 422 and "máximo" in r.json()["detalle"]

    def test_la_suma_de_los_archivos_tiene_tope(self, entorno, monkeypatch):
        monkeypatch.setenv("MAX_UPLOAD_TOTAL_BYTES", "100")
        cr = entrar()
        files = [("archivos", ("resumen.json", b'{"a":"' + b"x" * 80 + b'"}', "x/y")), ("archivos", ("manifest.json", b'{"a":"' + b"y" * 80 + b'"}', "x/y"))]
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), files=files, data={"claves": ["resumen", "manifest"]})
        assert r.status_code == 422 and "suman" in r.json()["detalle"]

    def test_el_catalogo_informa_los_limites(self, entorno):
        c, _ = entrar()
        cat = c.get(f"{U}/tableros").json()
        assert (cat["limite_bytes"], cat["limite_total_bytes"], cat["limite_contenido_bytes"]) == (4 * 1024 * 1024, 4_400_000, 60 * 1024 * 1024)


class TestNoFiltraRutasDelServidor:
    def test_el_error_de_un_lector_no_muestra_la_carpeta_temporal(self, entorno):
        cr = entrar()
        # DNS pide varios archivos; con solo el mapeo (vacio de datos) el lector se queja de uno que falta o de columnas.
        files = [("archivos", ("mapeo.csv", b"a,b\n1,2\n", "text/csv"))]
        r = cr[0].post(f"{U}/tableros/dns/validar", headers=csrf(cr), files=files, data={"claves": ["mapeo"]}).json()
        texto = " ".join(r["errores"])
        assert r["errores"] and "/tmp" not in texto and "actualizacion_" not in texto and "/var/" not in texto

    def test_un_error_de_lectura_inesperado_no_filtra_detalles(self, entorno, monkeypatch):
        def explota(_carpeta):
            raise KeyError("/ruta/secreta/del/servidor")
        monkeypatch.setattr(entorno.adaptadores["optimizacion"], "leer", explota)
        cr = entrar()
        r = cr[0].post(f"{U}/tableros/optimizacion/validar", headers=csrf(cr), **archivos_opt()).json()
        assert not r["valido"] and "secreta" not in " ".join(r["errores"]) and "estructura" in " ".join(r["errores"])
