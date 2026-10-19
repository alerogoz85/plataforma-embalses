"""Contrato HTTP de /api/v1/carbon/*: formas del JSON, filtros y errores."""
import pytest
from fastapi.testclient import TestClient

from application.use_cases.modelo_carbon import (
    ObtenerComparacionXmUseCase,
    ObtenerInventarioCarbonUseCase,
    ObtenerResumenCarbonUseCase,
    ObtenerSerieCarbonUseCase,
    ObtenerValidacionCarbonUseCase,
)
from presentation.api import dependencies as dep
from presentation.api.main import app
from tests.fakes import ModeloCarbonRepositoryEnMemoria, crear_paquete_carbon

CASOS = {
    dep.obtener_resumen_carbon_use_case: ObtenerResumenCarbonUseCase,
    dep.obtener_serie_carbon_use_case: ObtenerSerieCarbonUseCase,
    dep.obtener_inventario_carbon_use_case: ObtenerInventarioCarbonUseCase,
    dep.obtener_comparacion_xm_use_case: ObtenerComparacionXmUseCase,
    dep.obtener_validacion_carbon_use_case: ObtenerValidacionCarbonUseCase,
}


def _cliente(paquete):
    repo = ModeloCarbonRepositoryEnMemoria(paquete)
    for proveedor, caso in CASOS.items():
        app.dependency_overrides[proveedor] = lambda caso=caso: caso(repo)
    return TestClient(app)


@pytest.fixture
def cliente():
    yield _cliente(crear_paquete_carbon())
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_sin_datos():
    yield _cliente(None)
    app.dependency_overrides.clear()


class TestResumen:
    def test_forma_del_json(self, cliente):
        cuerpo = cliente.get("/api/v1/carbon/resumen").json()
        assert set(cuerpo) == {
            "origen", "poder_calorifico_mbtu_t", "techo_gbtu_dia", "maximo_historico", "ultimo_observado",
            "horizonte_meses", "pico", "inventario_pico", "trimestres", "criterios_cumplidos", "criterios_total",
        }
        assert set(cuerpo["pico"]) == {"fecha", "carbon_gbtu_dia", "uso_techo_p50_pct", "prob_supera_maximo_pct"}
        assert set(cuerpo["pico"]["carbon_gbtu_dia"]) == {"p10", "p50", "p90"}
        assert set(cuerpo["trimestres"][0]) == {"trimestre", "meses", "carbon_mt", "dentro_del_horizonte"}

    def test_valores_por_defecto(self, cliente):
        cuerpo = cliente.get("/api/v1/carbon/resumen").json()
        assert cuerpo["horizonte_meses"] == 9 and cuerpo["pico"]["fecha"] == "2027-02-01"
        assert cuerpo["inventario_pico"]["dias_inventario"] == 45
        assert (cuerpo["criterios_cumplidos"], cuerpo["criterios_total"]) == (3, 4)

    def test_filtros(self, cliente):
        cuerpo = cliente.get("/api/v1/carbon/resumen", params={"horizonte_meses": 3, "dias": 15}).json()
        assert cuerpo["horizonte_meses"] == 3 and cuerpo["pico"]["fecha"] == "2026-12-01"
        assert cuerpo["inventario_pico"]["dias_inventario"] == 15


class TestSerie:
    def test_historia_y_proyeccion(self, cliente):
        cuerpo = cliente.get("/api/v1/carbon/serie", params={"historia_meses": 12, "horizonte_meses": 6}).json()
        assert len(cuerpo["historico"]) == 12 and len(cuerpo["proyeccion"]) == 6
        assert cuerpo["techo_gbtu_dia"] == 400.0 and cuerpo["maximo_historico_gbtu_dia"] == 310.0
        assert set(cuerpo["proyeccion"][0]) == {
            "fecha", "dias", "roni", "aportes_pct_media", "uso_techo_pct", "carbon_gbtu_dia", "carbon_kt_mes",
            "prob_supera_maximo_pct", "observado_parcial_gbtu_dia",
        }

    def test_un_dato_no_publicado_sale_como_null_no_como_cero(self, cliente):
        historico = cliente.get("/api/v1/carbon/serie", params={"historia_meses": 12}).json()["historico"]
        assert any(h["roni"] is None for h in historico) and not any(h["roni"] == 0 for h in historico)

    def test_toda_la_historia_con_cero(self, cliente):
        assert len(cliente.get("/api/v1/carbon/serie", params={"historia_meses": 0}).json()["historico"]) == 24


class TestOtrosEndpoints:
    def test_inventario(self, cliente):
        filas = cliente.get("/api/v1/carbon/inventario", params={"dias": 60, "horizonte_meses": 3}).json()
        assert len(filas) == 3 and all(f["dias_inventario"] == 60 for f in filas)
        assert set(filas[0]) == {"fecha", "dias_inventario", "kt_p50", "kt_p90"}

    def test_comparacion_con_xm(self, cliente):
        filas = cliente.get("/api/v1/carbon/comparacion-xm", params={"horizonte_meses": 3}).json()
        assert len(filas) == 3
        assert set(filas[0]) == {
            "fecha", "modelo", "techo_gbtu_dia", "xm_estocastico_gbtu_dia", "xm_historicas_min_gbtu_dia",
            "xm_historicas_max_gbtu_dia",
        }

    def test_validacion(self, cliente):
        cuerpo = cliente.get("/api/v1/carbon/validacion").json()
        assert set(cuerpo) == {"errores_horizonte", "episodios", "criterios_cumplidos", "criterios_total", "veredicto", "supuestos"}
        assert [e["horizonte_meses"] for e in cuerpo["errores_horizonte"]] == [1, 3, 6, 9]


class TestParametrosInvalidos:
    """Cada parametro se valida contra una lista cerrada: nada de texto libre."""

    @pytest.mark.parametrize("ruta", ["resumen", "serie", "inventario", "comparacion-xm"])
    @pytest.mark.parametrize("horizonte", [0, 2, 12, -1])
    def test_horizonte_no_permitido(self, cliente, ruta, horizonte):
        respuesta = cliente.get(f"/api/v1/carbon/{ruta}", params={"horizonte_meses": horizonte})
        assert respuesta.status_code == 422 and "1, 3, 6, 9" in respuesta.json()["detail"]

    @pytest.mark.parametrize("ruta", ["resumen", "inventario"])
    @pytest.mark.parametrize("dias", [0, 10, 90])
    def test_dias_de_inventario_no_permitidos(self, cliente, ruta, dias):
        respuesta = cliente.get(f"/api/v1/carbon/{ruta}", params={"dias": dias})
        assert respuesta.status_code == 422 and "15, 30, 45, 60" in respuesta.json()["detail"]

    @pytest.mark.parametrize("historia", [1, 24, 100])
    def test_historia_no_permitida(self, cliente, historia):
        respuesta = cliente.get("/api/v1/carbon/serie", params={"historia_meses": historia})
        assert respuesta.status_code == 422 and "0, 12, 36, 60" in respuesta.json()["detail"]

    @pytest.mark.parametrize("valor", ["x", "1; DROP TABLE carbon_historico", "9 OR 1=1"])
    def test_texto_o_intentos_de_inyeccion_dan_422(self, cliente, valor):
        assert cliente.get("/api/v1/carbon/resumen", params={"horizonte_meses": valor}).status_code == 422
        assert cliente.get("/api/v1/carbon/serie", params={"historia_meses": valor}).status_code == 422


class TestSeguridadYErrores:
    @pytest.mark.parametrize("ruta", ["resumen", "serie", "inventario", "comparacion-xm", "validacion"])
    def test_sin_corrida_cargada_da_404_con_detalle(self, cliente_sin_datos, ruta):
        respuesta = cliente_sin_datos.get(f"/api/v1/carbon/{ruta}")
        assert respuesta.status_code == 404 and "importar_modelo_carbon" in respuesta.json()["detalle"]

    @pytest.mark.parametrize("metodo", ["post", "put", "delete", "patch"])
    def test_solo_lectura_los_demas_metodos_dan_405(self, cliente, metodo):
        assert getattr(cliente, metodo)("/api/v1/carbon/resumen").status_code == 405

    def test_la_documentacion_openapi_lista_los_cinco_endpoints(self, cliente):
        rutas = [r for r in cliente.get("/openapi.json").json()["paths"] if r.startswith("/api/v1/carbon")]
        assert sorted(rutas) == sorted(f"/api/v1/carbon/{r}" for r in ["resumen", "serie", "inventario", "comparacion-xm", "validacion"])
