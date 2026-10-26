"""Contrato HTTP de /api/v1/modelos/{modelo_id}/*: forma del JSON, estados y seguridad."""
import pytest
from fastapi.testclient import TestClient

from application.use_cases.modelo_analitico import ObtenerFichaModeloUseCase, ObtenerResultadosModeloUseCase
from domain.entities.modelo_analitico import MODELOS_CON_FICHA
from infrastructure.fichas.catalogo import FichasEnCodigo
from presentation.api import dependencies as dep
from presentation.api.main import app
from tests.fakes import ResultadoModeloRepositoryEnMemoria, crear_resultado_modelo


def _cliente(*resultados):
    repo = ResultadoModeloRepositoryEnMemoria(*resultados)
    app.dependency_overrides[dep.obtener_ficha_modelo_use_case] = lambda: ObtenerFichaModeloUseCase(FichasEnCodigo(), repo)
    app.dependency_overrides[dep.obtener_resultados_modelo_use_case] = lambda: ObtenerResultadosModeloUseCase(repo)
    return TestClient(app)


@pytest.fixture
def cliente():
    yield _cliente()
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_con_apagon():
    yield _cliente(crear_resultado_modelo("apagon"))
    app.dependency_overrides.clear()


class TestFicha:
    @pytest.mark.parametrize("modelo", MODELOS_CON_FICHA)
    def test_forma_del_json(self, cliente, modelo):
        f = cliente.get(f"/api/v1/modelos/{modelo}/ficha").json()
        assert set(f) == {
            "id", "titulo", "resumen", "estado", "estado_detalle", "documentos", "pregunta", "secciones",
            "datos_documentados", "archivos_esperados", "comando_importacion", "carpeta_proyecto",
        }
        assert f["id"] == modelo and set(f["secciones"][0]) == {"titulo", "items"}
        assert set(f["datos_documentados"][0]) == {"etiqueta", "valor", "detalle", "documento"}

    def test_estados_documentados(self, cliente):
        estado = lambda m: cliente.get(f"/api/v1/modelos/{m}/ficha").json()["estado"]  # noqa: E731
        assert (estado("gas"), estado("optimizacion"), estado("apagon")) == ("sin_resultados", "prueba_tecnica", "sin_resultados")

    def test_con_resultado_importado_el_estado_cambia(self, cliente_con_apagon):
        assert cliente_con_apagon.get("/api/v1/modelos/apagon/ficha").json()["estado"] == "con_resultados"
        assert cliente_con_apagon.get("/api/v1/modelos/gas/ficha").json()["estado"] == "sin_resultados"


class TestResultados:
    def test_sin_resultado_es_200_con_disponible_falso(self, cliente):
        r = cliente.get("/api/v1/modelos/gas/resultados")
        assert r.status_code == 200 and r.json() == {"modelo_id": "gas", "disponible": False, "resultado": None}

    def test_con_resultado_trae_todo_el_contenido(self, cliente_con_apagon):
        r = cliente_con_apagon.get("/api/v1/modelos/apagon/resultados").json()
        assert r["disponible"] and set(r["resultado"]) == {
            "generado_en", "origen", "configuracion", "indicadores", "series", "tablas", "advertencias"}
        assert r["resultado"]["indicadores"][0] == {"etiqueta": "Meses en rojo", "valor": "2", "detalle": "de 3 meses", "nivel": "critico"}
        assert r["resultado"]["series"][1]["puntos"][0] == {"x": "2026-10", "y": 60.0, "p10": 50.0, "p90": 70.0}
        assert r["resultado"]["series"][0]["puntos"][0]["p10"] is None
        assert r["resultado"]["tablas"][0]["filas"][1] == ["2026-11", "Amarillo", None]


class TestSeguridad:
    @pytest.mark.parametrize("ruta", ["ficha", "resultados"])
    @pytest.mark.parametrize("modelo", ["dns", "carbon", "otro"])
    def test_modelo_fuera_de_la_lista_da_404(self, cliente, modelo, ruta):
        r = cliente.get(f"/api/v1/modelos/{modelo}/{ruta}")
        assert r.status_code == 404 and modelo in r.json()["detalle"]

    @pytest.mark.parametrize("modelo", ["Gas", "gas1", "gas;", "a" * 21, "gas%27%20OR%201=1"])
    def test_identificador_con_caracteres_o_largo_invalidos_da_422(self, cliente, modelo):
        assert cliente.get(f"/api/v1/modelos/{modelo}/ficha").status_code == 422

    @pytest.mark.parametrize("metodo", ["post", "put", "delete", "patch"])
    @pytest.mark.parametrize("ruta", ["ficha", "resultados"])
    def test_solo_lectura(self, cliente, metodo, ruta):
        assert getattr(cliente, metodo)(f"/api/v1/modelos/gas/{ruta}").status_code == 405

    def test_openapi_lista_los_dos_endpoints(self, cliente):
        rutas = [r for r in cliente.get("/openapi.json").json()["paths"] if r.startswith("/api/v1/modelos")]
        assert sorted(rutas) == ["/api/v1/modelos/{modelo_id}/ficha", "/api/v1/modelos/{modelo_id}/resultados"]
