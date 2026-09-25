"""Pruebas de los endpoints HTTP sobre la app real de FastAPI.

Se usan los casos de uso reales, conectados por `dependency_overrides` a
repositorios en memoria: se prueba el contrato HTTP (rutas, parametros,
codigos de estado, forma del JSON, CSV, CORS) sin base de datos ni red.
"""
import csv
import io
import math
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from application.use_cases.generar_prediccion import GenerarPrediccionUseCase
from application.use_cases.listar_embalses import ListarEmbalsesUseCase
from application.use_cases.obtener_detalle_embalse import ObtenerDetalleEmbalseUseCase
from application.use_cases.obtener_fuente_datos import ObtenerFuenteDatosUseCase
from application.use_cases.obtener_resumen_nacional import ObtenerResumenNacionalUseCase
from application.use_cases.obtener_senda_volumen import ObtenerSendaVolumenUseCase
from domain.entities.metadatos_datos import MetadatosDatos
from domain.entities.region import NombreRegion
from infrastructure.ml.holt_winters_forecasting_service import HoltWintersForecastingService
from presentation.api import dependencies as dep
from presentation.api.main import app
from tests.fakes import (
    EmbalseRepositoryEnMemoria,
    ForecastingPersistencia,
    MedicionRepositoryEnMemoria,
    MetadatosRepositoryEnMemoria,
    ProyeccionSendaRepositoryEnMemoria,
    caudal,
    crear_embalse,
    crear_medicion,
    crear_proyeccion_publicada,
)

FIN = date(2026, 9, 22)
DIAS_LARGOS = 430  # ~14 meses: suficiente para la senda mensual


def _pct(i: int) -> float:
    return round(55 + 20 * math.sin(i / 20), 2)


def _serie_larga(embalse, dias=DIAS_LARGOS):
    inicio = FIN - timedelta(days=dias - 1)
    mediciones = []
    for i in range(dias):
        opcionales = {}
        if i % 2 == 0:  # aportes solo en dias pares: los impares deben salir como null
            opcionales = dict(
                aportes=caudal(40.0),
                aportes_media_historica_m3s=80.0,
                turbinado=caudal(20.0),
                vertimientos=caudal(0.0),
            )
        mediciones.append(
            crear_medicion(embalse, inicio + timedelta(days=i), _pct(i), 200.0, **opcionales)
        )
    return mediciones


@pytest.fixture
def datos():
    a = crear_embalse("AAA", NombreRegion.ANTIOQUIA)
    b = crear_embalse("BBB", NombreRegion.CARIBE)
    sin_datos = crear_embalse("CCC", NombreRegion.VALLE)
    agregado = crear_embalse("AGG", NombreRegion.CENTRO, es_agregado=True)
    mediciones = (
        _serie_larga(a)
        # B es corta: <30 registros (sin prediccion) y <9 meses (sin senda).
        + [crear_medicion(b, FIN - timedelta(days=i), 30.0, 100.0) for i in range(20)]
        + [crear_medicion(agregado, FIN, 10.0, 100.0)]
    )
    return [a, b, sin_datos, agregado], mediciones


@pytest.fixture
def cliente(datos):
    embalses, mediciones = datos
    repo_e = EmbalseRepositoryEnMemoria(embalses)
    repo_m = MedicionRepositoryEnMemoria(mediciones)
    metadatos = MetadatosRepositoryEnMemoria()
    forecasting = ForecastingPersistencia()

    casos = {
        dep.obtener_resumen_nacional_use_case: ObtenerResumenNacionalUseCase(repo_e, repo_m),
        dep.obtener_listar_embalses_use_case: ListarEmbalsesUseCase(repo_e, repo_m),
        dep.obtener_detalle_embalse_use_case: ObtenerDetalleEmbalseUseCase(repo_e, repo_m),
        dep.obtener_generar_prediccion_use_case: GenerarPrediccionUseCase(repo_e, repo_m, forecasting),
        dep.obtener_senda_volumen_use_case: ObtenerSendaVolumenUseCase(repo_e, repo_m, forecasting),
        dep.obtener_fuente_datos_use_case: ObtenerFuenteDatosUseCase(metadatos),
    }
    for proveedor, caso in casos.items():
        app.dependency_overrides[proveedor] = lambda caso=caso: caso

    cliente = TestClient(app)
    cliente.metadatos = metadatos  # para probar /fuente-datos
    yield cliente
    app.dependency_overrides.clear()


class TestSalud:
    def test_responde_ok(self, cliente):
        respuesta = cliente.get("/api/v1/salud")
        assert respuesta.status_code == 200
        assert respuesta.json() == {"estado": "ok"}


class TestResumen:
    def test_devuelve_kpis_regiones_y_embalses(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/resumen")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert set(cuerpo) == {"kpis", "regiones", "embalses"}
        assert cuerpo["kpis"]["total_embalses"] == 3  # CCC no tiene mediciones
        assert cuerpo["kpis"]["fecha_corte"] == FIN.isoformat()
        assert {e["id"] for e in cuerpo["embalses"]} == {"AAA", "BBB", "AGG"}

    def test_resumen_no_se_confunde_con_un_id_de_embalse(self, cliente):
        # Si la ruta /{embalse_id} se registrara antes, "resumen" daria 404.
        assert cliente.get("/api/v1/embalses/resumen").status_code == 200

    def test_los_campos_no_publicados_salen_como_null(self, cliente):
        agregado = next(
            e for e in cliente.get("/api/v1/embalses/resumen").json()["embalses"] if e["id"] == "AGG"
        )
        assert agregado["es_agregado"] is True
        assert agregado["aportes_m3s"] is None
        assert agregado["aportes_pct_media"] is None
        assert agregado["turbinado_m3s"] is None
        assert agregado["dias_autonomia"] is None

    def test_pondera_el_kpi_nacional_por_energia(self, cliente):
        # AAA 55-75% (200 GWh), BBB 30% (100), AGG 10% (100): promedio ponderado por GWh.
        kpi = cliente.get("/api/v1/embalses/resumen").json()["kpis"]["pct_volumen_util_nacional"]
        ultimo_a = _pct(DIAS_LARGOS - 1)
        esperado = (ultimo_a * 200 + 30 * 100 + 10 * 100) / 400
        assert kpi == pytest.approx(esperado, abs=0.02)

    def test_filtra_por_region_repetible(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/resumen", params=[("region", "Caribe"), ("region", "Centro")])
        ids = {e["id"] for e in respuesta.json()["embalses"]}
        assert ids == {"BBB", "AGG"}

    def test_filtra_por_embalse(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/resumen", params={"embalse": "BBB"})
        assert [e["id"] for e in respuesta.json()["embalses"]] == ["BBB"]

    def test_acepta_una_fecha_de_corte(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/resumen", params={"fecha": (FIN - timedelta(days=5)).isoformat()})
        assert respuesta.status_code == 200
        assert respuesta.json()["kpis"]["fecha_corte"] == (FIN - timedelta(days=5)).isoformat()

    def test_una_fecha_mal_formada_da_422(self, cliente):
        assert cliente.get("/api/v1/embalses/resumen", params={"fecha": "ayer"}).status_code == 422

    def test_una_region_desconocida_devuelve_un_resumen_vacio(self, cliente):
        cuerpo = cliente.get("/api/v1/embalses/resumen", params={"region": "Atlantida"}).json()
        assert cuerpo["embalses"] == [] and cuerpo["kpis"]["total_embalses"] == 0


class TestRegiones:
    def test_lista_el_agregado_por_region(self, cliente):
        respuesta = cliente.get("/api/v1/regiones")
        assert respuesta.status_code == 200
        regiones = {r["region"]: r for r in respuesta.json()}
        assert set(regiones) == {"Antioquia", "Caribe", "Centro"}
        assert regiones["Caribe"]["pct_volumen_util"] == 30.0
        assert regiones["Caribe"]["nivel_riesgo"] == "CRITICO"  # 30 % < 50 %
        assert regiones["Centro"]["nivel_riesgo"] == "CRITICO"


class TestDetalleEmbalse:
    def test_devuelve_resumen_y_serie_historica(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/AAA")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["resumen"]["id"] == "AAA"
        assert cuerpo["resumen"]["fecha"] == FIN.isoformat()
        assert 0 < len(cuerpo["serie_historica"]) <= 181  # por defecto, ~180 dias

    def test_respeta_el_rango_de_fechas(self, cliente):
        respuesta = cliente.get(
            "/api/v1/embalses/AAA",
            params={"fecha_inicio": "2026-09-01", "fecha_fin": "2026-09-10"},
        )
        fechas = [p["fecha"] for p in respuesta.json()["serie_historica"]]
        assert fechas[0] == "2026-09-01" and fechas[-1] == "2026-09-10" and len(fechas) == 10

    def test_los_puntos_sin_aportes_llevan_null_no_cero(self, cliente):
        serie = cliente.get("/api/v1/embalses/AAA").json()["serie_historica"]
        assert any(p["aportes_m3s"] is None for p in serie)
        assert any(p["aportes_m3s"] == 40.0 for p in serie)
        assert all(p["aportes_pct_media"] in (None, 50.0) for p in serie)

    def test_embalse_inexistente_da_404_con_detalle(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/NOPE")
        assert respuesta.status_code == 404
        assert "NOPE" in respuesta.json()["detalle"]

    def test_embalse_sin_mediciones_da_404(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/CCC")
        assert respuesta.status_code == 404
        assert "mediciones" in respuesta.json()["detalle"]


class TestListado:
    def test_lista_los_embalses_con_datos(self, cliente):
        respuesta = cliente.get("/api/v1/embalses")
        assert respuesta.status_code == 200
        assert {d["resumen"]["id"] for d in respuesta.json()} == {"AAA", "BBB", "AGG"}

    def test_sin_fechas_no_incluye_la_serie(self, cliente):
        assert all(d["serie_historica"] == [] for d in cliente.get("/api/v1/embalses").json())

    def test_con_fechas_incluye_la_serie_y_filtra_por_region(self, cliente):
        respuesta = cliente.get(
            "/api/v1/embalses",
            params={"region": "Antioquia", "fecha_inicio": "2026-09-01"},
        )
        detalles = respuesta.json()
        assert [d["resumen"]["id"] for d in detalles] == ["AAA"]
        assert len(detalles[0]["serie_historica"]) == 22


class TestAgregados:
    """'Todos los embalses' (TOTAL) y 'Todos los embalses de una region' (REGION:<nombre>)."""

    def test_detalle_del_total_nacional(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/TOTAL")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["resumen"]["id"] == "TOTAL" and cuerpo["resumen"]["es_agregado"] is True
        assert len(cuerpo["serie_historica"]) > 100
        assert set(cuerpo["serie_historica"][0]) >= {"fecha", "pct_volumen_util", "aportes_pct_media"}

    def test_detalle_de_una_region_con_dos_puntos_en_la_ruta(self, cliente):
        cuerpo = cliente.get("/api/v1/embalses/REGION%3AAntioquia").json()
        assert cuerpo["resumen"]["id"] == "REGION:Antioquia" and cuerpo["resumen"]["nombre"] == "Región Antioquia"

    def test_una_region_inexistente_da_404(self, cliente):
        assert cliente.get("/api/v1/embalses/REGION%3AMarte").status_code == 404

    def test_prediccion_del_total_y_de_una_region(self, cliente):
        for id_ in ("TOTAL", "REGION%3AAntioquia"):
            respuesta = cliente.get(f"/api/v1/embalses/{id_}/prediccion", params={"horizonte": 30})
            assert respuesta.status_code == 200 and len(respuesta.json()["puntos"]) == 30

    def test_el_total_coincide_con_el_kpi_nacional(self, cliente):
        kpi = cliente.get("/api/v1/embalses/resumen").json()["kpis"]["pct_volumen_util_nacional"]
        assert cliente.get("/api/v1/embalses/TOTAL").json()["resumen"]["pct_volumen_util"] == kpi


class TestPrediccion:
    @pytest.mark.parametrize("horizonte", [30, 90, 180, 360])  # 1, 3, 6 y 12 meses
    def test_devuelve_tantos_puntos_como_el_horizonte(self, cliente, horizonte):
        respuesta = cliente.get("/api/v1/embalses/AAA/prediccion", params={"horizonte": horizonte})
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["horizonte_dias"] == horizonte and len(cuerpo["puntos"]) == horizonte
        assert cuerpo["nivel_confianza"] == 0.95
        assert cuerpo["metodo"] == "Persistencia de prueba"
        assert cuerpo["puntos"][0]["fecha"] == (FIN + timedelta(days=1)).isoformat()

    def test_la_forma_del_json_incluye_origen_y_confianza(self, cliente):
        cuerpo = cliente.get("/api/v1/embalses/AAA/prediccion").json()
        assert set(cuerpo) == {
            "embalse_id", "horizonte_dias", "nivel_confianza", "generado_en", "metodo", "puntos", "origen",
        }
        assert cuerpo["origen"] == "holt_winters" and cuerpo["nivel_confianza"] == 0.95

    def test_con_proyeccion_de_outputs_el_pronostico_diario_la_usa_y_no_tiene_ic(self, cliente, datos):
        embalses, mediciones = datos
        caso = GenerarPrediccionUseCase(
            EmbalseRepositoryEnMemoria(embalses),
            MedicionRepositoryEnMemoria(mediciones),
            ForecastingPersistencia(),
            ProyeccionSendaRepositoryEnMemoria(crear_proyeccion_publicada("AAA", inicio=date(2026, 10, 1))),
        )
        app.dependency_overrides[dep.obtener_generar_prediccion_use_case] = lambda: caso
        cuerpo = cliente.get("/api/v1/embalses/AAA/prediccion", params={"horizonte": 90}).json()
        assert cuerpo["origen"] == "outputs" and cuerpo["nivel_confianza"] is None
        assert len(cuerpo["puntos"]) == 90 and "interpolación diaria" in cuerpo["metodo"]

    def test_por_defecto_proyecta_30_dias(self, cliente):
        assert len(cliente.get("/api/v1/embalses/AAA/prediccion").json()["puntos"]) == 30

    @pytest.mark.parametrize("horizonte", [0, 15, 45, 60, 365])
    def test_un_horizonte_no_permitido_da_422(self, cliente, horizonte):
        respuesta = cliente.get("/api/v1/embalses/AAA/prediccion", params={"horizonte": horizonte})
        assert respuesta.status_code == 422
        assert "30, 90, 180 o 360" in respuesta.json()["detail"]

    def test_un_horizonte_no_numerico_da_422(self, cliente):
        assert cliente.get("/api/v1/embalses/AAA/prediccion", params={"horizonte": "x"}).status_code == 422

    def test_embalse_inexistente_da_404(self, cliente):
        assert cliente.get("/api/v1/embalses/NOPE/prediccion").status_code == 404

    def test_historia_insuficiente_da_422_con_los_conteos(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/BBB/prediccion")
        assert respuesta.status_code == 422
        assert "30" in respuesta.json()["detalle"] and "20" in respuesta.json()["detalle"]

    @pytest.mark.parametrize("horizonte", [30, 90, 180, 360])
    def test_con_el_modelo_real_el_intervalo_es_coherente_y_esta_acotado(self, datos, horizonte):
        embalses, mediciones = datos
        repo_e, repo_m = EmbalseRepositoryEnMemoria(embalses), MedicionRepositoryEnMemoria(mediciones)
        caso = GenerarPrediccionUseCase(repo_e, repo_m, HoltWintersForecastingService())
        app.dependency_overrides[dep.obtener_generar_prediccion_use_case] = lambda: caso
        try:
            puntos = TestClient(app).get("/api/v1/embalses/AAA/prediccion", params={"horizonte": horizonte}).json()["puntos"]
        finally:
            app.dependency_overrides.clear()
        assert len(puntos) == horizonte
        for p in puntos:
            assert 0 <= p["limite_inferior"] <= p["valor_esperado"] <= p["limite_superior"] <= 100


class TestReporte:
    def test_csv_tiene_encabezado_tipo_y_nombre_de_archivo(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/AAA/reporte", params={"fecha_inicio": "2026-09-01"})
        assert respuesta.status_code == 200
        assert respuesta.headers["content-type"].startswith("text/csv")
        assert 'filename="AAA_reporte.csv"' in respuesta.headers["content-disposition"]
        filas = list(csv.reader(io.StringIO(respuesta.text)))
        assert filas[0] == [
            "fecha", "pct_volumen_util", "energia_util_gwh", "aportes_m3s",
            "aportes_pct_media", "vertimientos_m3s", "turbinado_m3s",
        ]
        assert len(filas) == 1 + 22

    def test_csv_deja_vacias_las_celdas_sin_dato_en_lugar_de_ceros(self, cliente):
        filas = list(csv.DictReader(io.StringIO(
            cliente.get("/api/v1/embalses/AAA/reporte", params={"fecha_inicio": "2026-09-20"}).text
        )))
        con_aportes = [f for f in filas if f["aportes_m3s"] != ""]
        sin_aportes = [f for f in filas if f["aportes_m3s"] == ""]
        assert con_aportes and sin_aportes
        assert all(f["turbinado_m3s"] == "" and f["vertimientos_m3s"] == "" for f in sin_aportes)
        assert all(f["aportes_m3s"] == "40.0" for f in con_aportes)

    def test_json_es_descargable_y_tiene_la_misma_forma_que_el_detalle(self, cliente):
        respuesta = cliente.get("/api/v1/embalses/AAA/reporte", params={"formato": "json", "fecha_inicio": "2026-09-01"})
        assert respuesta.status_code == 200
        assert respuesta.headers["content-type"].startswith("application/json")
        assert 'filename="AAA_reporte.json"' in respuesta.headers["content-disposition"]
        assert set(respuesta.json()) == {"resumen", "serie_historica"}

    def test_un_formato_desconocido_da_422(self, cliente):
        assert cliente.get("/api/v1/embalses/AAA/reporte", params={"formato": "xml"}).status_code == 422

    def test_embalse_inexistente_da_404(self, cliente):
        assert cliente.get("/api/v1/embalses/NOPE/reporte").status_code == 404


class TestSendaVolumen:
    def test_por_defecto_es_el_total_nacional_a_12_meses(self, cliente):
        respuesta = cliente.get("/api/v1/senda-volumen")
        assert respuesta.status_code == 200
        cuerpo = respuesta.json()
        assert cuerpo["embalse_id"] == "TOTAL" and cuerpo["nombre"] == "Total nacional"
        assert len(cuerpo["proyeccion"]) == 12
        assert len(cuerpo["validacion"]) == 2

    @pytest.mark.parametrize("meses", [1, 3, 6, 12])
    def test_horizontes_permitidos(self, cliente, meses):
        respuesta = cliente.get("/api/v1/senda-volumen", params={"embalse": "AAA", "horizonte_meses": meses})
        assert respuesta.status_code == 200
        assert len(respuesta.json()["proyeccion"]) == meses

    @pytest.mark.parametrize("meses", [0, 2, 18, 24])
    def test_horizontes_no_permitidos_dan_422(self, cliente, meses):
        respuesta = cliente.get("/api/v1/senda-volumen", params={"horizonte_meses": meses})
        assert respuesta.status_code == 422
        assert "1, 3, 6 o 12" in respuesta.json()["detail"]

    def test_la_forma_del_json_incluye_todo_lo_que_consume_el_frontend(self, cliente):
        cuerpo = cliente.get("/api/v1/senda-volumen", params={"embalse": "AAA"}).json()
        assert set(cuerpo) == {
            "embalse_id", "nombre", "metodo", "generado_en", "ultimo_observado",
            "minimo_proyectado", "historico", "proyeccion", "validacion",
            "origen_proyeccion", "horizonte_efectivo_meses",
        }
        assert set(cuerpo["ultimo_observado"]) == {"mes", "pct_volumen_util"}
        assert set(cuerpo["proyeccion"][0]) == {"mes", "valor_esperado", "limite_inferior", "limite_superior"}
        assert set(cuerpo["validacion"][0]) == {"modelo", "mae", "r2"}
        assert cuerpo["ultimo_observado"]["mes"] == FIN.strftime("%Y-%m")

    def test_con_proyeccion_de_outputs_lo_informa_y_limita_el_horizonte_a_lo_publicado(self, cliente, datos):
        embalses, mediciones = datos
        caso = ObtenerSendaVolumenUseCase(
            EmbalseRepositoryEnMemoria(embalses),
            MedicionRepositoryEnMemoria(mediciones),
            ForecastingPersistencia(),
            ProyeccionSendaRepositoryEnMemoria(crear_proyeccion_publicada("AAA", meses=6)),
        )
        app.dependency_overrides[dep.obtener_senda_volumen_use_case] = lambda: caso
        cuerpo = cliente.get("/api/v1/senda-volumen", params={"embalse": "AAA", "horizonte_meses": 12}).json()
        assert cuerpo["origen_proyeccion"] == "outputs"
        assert cuerpo["horizonte_efectivo_meses"] == 6 and len(cuerpo["proyeccion"]) == 6
        assert cuerpo["validacion"] == []
        assert cuerpo["metodo"] == "Modelo de prueba"

    def test_sin_proyeccion_de_outputs_informa_el_respaldo(self, cliente):
        cuerpo = cliente.get("/api/v1/senda-volumen", params={"embalse": "AAA"}).json()
        assert cuerpo["origen_proyeccion"] == "holt_winters"
        assert cuerpo["horizonte_efectivo_meses"] == 12

    def test_embalse_inexistente_da_404(self, cliente):
        assert cliente.get("/api/v1/senda-volumen", params={"embalse": "NOPE"}).status_code == 404

    def test_embalse_sin_mediciones_da_404(self, cliente):
        assert cliente.get("/api/v1/senda-volumen", params={"embalse": "CCC"}).status_code == 404

    def test_historia_insuficiente_da_422(self, cliente):
        respuesta = cliente.get("/api/v1/senda-volumen", params={"embalse": "BBB"})
        assert respuesta.status_code == 422
        assert "9" in respuesta.json()["detalle"]


class TestFuenteDatos:
    def test_sin_datos_no_afirma_que_sean_reales(self, cliente):
        cuerpo = cliente.get("/api/v1/fuente-datos").json()
        assert cuerpo["fuente"] == "Sin datos"
        assert cuerpo["es_real"] is False
        assert cuerpo["fecha_corte"] is None

    def test_informa_procedencia_y_fecha_de_corte(self, cliente):
        cliente.metadatos.guardar(
            MetadatosDatos("SIMEM / XM", "desc", date(2026, 9, 22), datetime(2026, 9, 23, 17, 0, tzinfo=timezone.utc), True)
        )
        cuerpo = cliente.get("/api/v1/fuente-datos").json()
        assert cuerpo["fuente"] == "SIMEM / XM"
        assert cuerpo["es_real"] is True
        assert cuerpo["fecha_corte"] == "2026-09-22"
        assert cuerpo["actualizado_en"].startswith("2026-09-23T17:00")


class TestContratoGeneral:
    def test_una_ruta_inexistente_da_404(self, cliente):
        assert cliente.get("/api/v1/no-existe").status_code == 404

    def test_solo_se_permiten_lecturas(self, cliente):
        assert cliente.post("/api/v1/embalses/resumen").status_code == 405
        assert cliente.delete("/api/v1/embalses/AAA").status_code == 405

    def test_la_documentacion_openapi_expone_todos_los_endpoints(self, cliente):
        rutas = set(cliente.get("/openapi.json").json()["paths"])
        assert rutas >= {
            "/api/v1/salud",
            "/api/v1/embalses/resumen",
            "/api/v1/embalses",
            "/api/v1/embalses/{embalse_id}",
            "/api/v1/embalses/{embalse_id}/prediccion",
            "/api/v1/embalses/{embalse_id}/reporte",
            "/api/v1/regiones",
            "/api/v1/senda-volumen",
            "/api/v1/fuente-datos",
        }


class TestCors:
    ORIGEN_PERMITIDO = "http://localhost:3000"

    def test_permite_el_origen_del_frontend(self, cliente):
        respuesta = cliente.get("/api/v1/salud", headers={"Origin": self.ORIGEN_PERMITIDO})
        assert respuesta.headers["access-control-allow-origin"] == self.ORIGEN_PERMITIDO

    def test_no_habilita_otros_origenes(self, cliente):
        respuesta = cliente.get("/api/v1/salud", headers={"Origin": "https://sitio-ajeno.example"})
        assert "access-control-allow-origin" not in respuesta.headers

    def test_el_preflight_del_frontend_se_acepta_para_get(self, cliente):
        respuesta = cliente.options(
            "/api/v1/embalses/resumen",
            headers={"Origin": self.ORIGEN_PERMITIDO, "Access-Control-Request-Method": "GET"},
        )
        assert respuesta.status_code == 200
        assert "GET" in respuesta.headers["access-control-allow-methods"]

    def test_el_preflight_rechaza_metodos_de_escritura(self, cliente):
        respuesta = cliente.options(
            "/api/v1/embalses/resumen",
            headers={"Origin": self.ORIGEN_PERMITIDO, "Access-Control-Request-Method": "DELETE"},
        )
        assert respuesta.status_code == 400
