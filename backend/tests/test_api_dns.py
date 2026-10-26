"""Contrato HTTP de /api/v1/dns/*: formas del JSON, filtros y errores."""
import pytest
from fastapi.testclient import TestClient

from application.use_cases.modelo_dns import (
    ObtenerCambiosReporteDnsUseCase,
    ObtenerCatalogoDnsUseCase,
    ObtenerCausasDnsUseCase,
    ObtenerModeloDnsUseCase,
    ObtenerPatronesDnsUseCase,
    ObtenerResumenDnsUseCase,
    ObtenerSerieDnsUseCase,
    ObtenerZonasDnsUseCase,
)
from presentation.api import dependencies as dep
from presentation.api.main import app
from tests.fakes import ModeloDnsRepositoryEnMemoria, crear_paquete_dns

CASOS = {
    dep.obtener_catalogo_dns_use_case: ObtenerCatalogoDnsUseCase,
    dep.obtener_resumen_dns_use_case: ObtenerResumenDnsUseCase,
    dep.obtener_serie_dns_use_case: ObtenerSerieDnsUseCase,
    dep.obtener_zonas_dns_use_case: ObtenerZonasDnsUseCase,
    dep.obtener_patrones_dns_use_case: ObtenerPatronesDnsUseCase,
    dep.obtener_causas_dns_use_case: ObtenerCausasDnsUseCase,
    dep.obtener_cambios_reporte_dns_use_case: ObtenerCambiosReporteDnsUseCase,
    dep.obtener_modelo_dns_use_case: ObtenerModeloDnsUseCase,
}
RUTAS = ["catalogo", "resumen", "serie", "zonas", "patrones", "causas", "cambios-reporte", "modelo"]
CON_PERIODO = ["resumen", "serie", "patrones", "causas"]
CON_AMBITO = ["resumen", "serie", "zonas", "patrones", "causas", "cambios-reporte", "modelo"]


def _cliente(paquete):
    repo = ModeloDnsRepositoryEnMemoria(paquete)
    for proveedor, caso in CASOS.items():
        app.dependency_overrides[proveedor] = lambda caso=caso: caso(repo)
    return TestClient(app)


@pytest.fixture
def cliente():
    yield _cliente(crear_paquete_dns())
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_sin_datos():
    yield _cliente(None)
    app.dependency_overrides.clear()


def get(cliente, ruta, **params):
    return cliente.get(f"/api/v1/dns/{ruta}", params=params)


class TestFormas:
    def test_catalogo(self, cliente):
        c = get(cliente, "catalogo").json()
        assert set(c) == {"origen", "fecha_inicio", "fecha_corte", "mes_corte_parcial", "regiones", "subareas", "periodo_pronostico"}
        assert set(c["subareas"][0]) == {"codigo", "nombre", "region", "departamentos"}

    def test_resumen(self, cliente):
        r = get(cliente, "resumen", periodo_meses=12).json()
        assert set(r) == {
            "periodo_meses", "desde", "hasta", "eventos", "energia_gwh", "pct_criticos", "pct_no_programados",
            "variacion_eventos_pct", "variacion_energia_pct", "causa_mas_frecuente", "causa_mas_frecuente_eventos", "eventos_edac",
        }
        assert r["eventos"] == 5 and r["energia_gwh"] == pytest.approx(0.42)

    def test_serie(self, cliente):
        s = get(cliente, "serie", periodo_meses=12).json()
        assert set(s) == {"meses", "pronostico", "nota_pronostico"}
        assert set(s["meses"][0]) == {"mes", "eventos", "energia_gwh", "eventos_no_programados", "parcial"}
        assert set(s["pronostico"]) == {"mes", "eventos", "energia_gwh", "subareas"}

    def test_zonas_patrones_causas_cambios_modelo(self, cliente):
        assert set(get(cliente, "zonas").json()["zonas"][0]) == {
            "ranking", "codigo", "nombre", "region", "indice_priorizacion", "energia_total_gwh", "n_eventos", "pct_criticos", "variacion_pct"}
        p = get(cliente, "patrones").json()
        assert set(p) == {"por_hora", "dias", "por_dia_semana", "franjas", "eventos_usados", "eventos_hora_desconocida"}
        assert set(get(cliente, "causas").json()) == {"total", "causas", "origen_de_la_causa", "tipos_evento", "niveles_red"}
        assert set(get(cliente, "cambios-reporte").json()["cambios"][0]) == {
            "codigo", "nombre", "region", "periodo_quiebre", "direccion", "pct_generica_antes", "pct_generica_despues",
            "pct_causa_conocida_antes", "pct_causa_conocida_despues"}
        m = get(cliente, "modelo").json()
        assert set(m) == {"periodo_pronostico", "metricas", "importancia", "pronostico"}
        assert set(m["metricas"][0]) == {"modelo", "variable", "mae", "rmse", "mejora_vs_persistencia_pct"}


class TestFiltros:
    def test_valores_por_defecto_son_36_meses(self, cliente):
        assert get(cliente, "resumen").json()["periodo_meses"] == 36

    def test_region_subarea_y_origen(self, cliente):
        assert get(cliente, "resumen", periodo_meses=12, region="Norte").json()["eventos"] == 4
        assert get(cliente, "resumen", periodo_meses=12, subarea="Are0003").json()["eventos"] == 1
        assert get(cliente, "resumen", periodo_meses=12, origen="programada").json()["eventos"] == 2

    @pytest.mark.parametrize("ruta", CON_PERIODO)
    @pytest.mark.parametrize("valor", [7, 24, -1, "abc", "12; DROP TABLE dns_eventos"])
    def test_periodo_fuera_de_la_lista_da_422(self, cliente, ruta, valor):
        r = get(cliente, ruta, periodo_meses=valor)
        assert r.status_code == 422

    def test_el_422_del_periodo_dice_los_valores_permitidos(self, cliente):
        assert "12, 36, 60, 0" in get(cliente, "resumen", periodo_meses=7).json()["detail"]

    @pytest.mark.parametrize("ruta", ["resumen", "serie", "patrones", "causas"])
    def test_origen_invalido_da_422(self, cliente, ruta):
        r = get(cliente, ruta, origen="otro")
        assert r.status_code == 422 and "programada" in r.json()["detail"]

    @pytest.mark.parametrize("ruta", CON_AMBITO)
    def test_region_inexistente_da_422_con_detalle(self, cliente, ruta):
        r = get(cliente, ruta, region="Marte")
        assert r.status_code == 422 and "Marte" in r.json()["detalle"]

    @pytest.mark.parametrize("ruta", CON_AMBITO)
    def test_subarea_inexistente_da_422(self, cliente, ruta):
        assert get(cliente, ruta, subarea="Are9999").status_code == 422

    @pytest.mark.parametrize("subarea", ["Are 1", "Are'1", "Are0001;--", "../etc", "a" * 21])
    def test_subarea_con_caracteres_o_largo_invalidos_da_422(self, cliente, subarea):
        assert get(cliente, "resumen", subarea=subarea).status_code == 422

    def test_region_demasiado_larga_da_422(self, cliente):
        assert get(cliente, "resumen", region="x" * 41).status_code == 422


class TestSeguridadYEstado:
    @pytest.mark.parametrize("ruta", RUTAS)
    def test_sin_corrida_cargada_da_404_con_la_instruccion(self, cliente_sin_datos, ruta):
        r = get(cliente_sin_datos, ruta)
        assert r.status_code == 404 and "importar_modelo_dns" in r.json()["detalle"]

    @pytest.mark.parametrize("metodo", ["post", "put", "delete", "patch"])
    def test_solo_lectura_los_demas_metodos_dan_405(self, cliente, metodo):
        assert getattr(cliente, metodo)("/api/v1/dns/resumen").status_code == 405

    def test_la_documentacion_openapi_lista_los_ocho_endpoints(self, cliente):
        rutas = [r for r in cliente.get("/openapi.json").json()["paths"] if r.startswith("/api/v1/dns")]
        assert sorted(rutas) == sorted(f"/api/v1/dns/{r}" for r in RUTAS)
