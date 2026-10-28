"""Visor de riesgo de apagon: escenarios precalculados por combinacion de controles (entidad, repositorio, adaptador, API)."""
from dataclasses import replace
from datetime import datetime

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from application.use_cases.modelo_analitico import ObtenerCatalogoEscenariosApagonUseCase, ObtenerEscenarioApagonUseCase
from domain.entities.escenario_apagon import FRANJAS, EscenarioApagon, FuenteEscenarios, MesEscenario, valores_oni
from domain.repositories.modelo_analitico_repository import EscenarioApagonRepository
from infrastructure.ingesta.resultados_modelos.comun import SalidaModeloInvalidaError
from infrastructure.ingesta.resultados_modelos.escenarios_apagon import combinaciones, escenario_desde_resultado
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_escenario_apagon_repository import DuckDBEscenarioApagonRepository
from presentation.api import dependencies as dep
from presentation.api.main import app


def mes(m="2026-10", **sobre) -> MesEscenario:
    base = dict(
        mes=m, indice_riesgo=12.5, probabilidad_deficit=0.3, probabilidad_apagon_severo=0.08, semaforo="ROJO",
        oni_p10=0.5, oni_p50=1.0, oni_p90=1.5, embalse_pct_p10=40.0, embalse_pct_p50=55.0, embalse_pct_p90=70.0,
        demanda_mwh_p10=6.9e6, demanda_mwh_p50=7.0e6, demanda_mwh_p90=7.1e6, oferta_mwh_p10=6.8e6, oferta_mwh_p50=7.1e6,
        oferta_mwh_p90=7.4e6, deficit_mwh_p50=100.0, deficit_mwh_p90=900.0, margen_reserva_pct_p50=0.12,
        deficit_por_franja_mwh=(10.0, 20.0, 30.0, 40.0, 25.0),
    )
    return MesEscenario(**{**base, **sobre})


def escenario(modo="manual", oni=1.0, simulaciones=2000, horizonte=12) -> EscenarioApagon:
    meses = tuple(mes(f"2026-{m:02d}") for m in range(1, 13)) + tuple(mes(f"2027-{m:02d}") for m in range(1, horizonte - 11))
    return EscenarioApagon(modo=modo, oni=None if modo == "probabilistico" else oni, simulaciones=simulaciones, horizonte=horizonte, meses=meses[:horizonte])


FUENTE = FuenteEscenarios(generado_en=datetime(2026, 10, 27, 9, 0), origen="Modelo de prueba", ultimo_oni_observado=1.8, ultimo_mes_demanda="2026-08-01", semilla=7)


class TestEntidad:
    def test_el_deslizador_tiene_51_valores_de_menos_2_5_a_2_5(self):
        v = valores_oni()
        assert len(v) == 51 and v[0] == -2.5 and v[-1] == 2.5 and 0.0 in v and 1.1 in v

    def test_las_combinaciones_son_468(self):
        c = combinaciones()
        assert len(c) == 468 and len(set(c)) == 468
        assert sum(1 for m, *_ in c if m == "probabilistico") == 9

    @pytest.mark.parametrize("cambio", [
        {"semaforo": "AZUL"}, {"mes": "2026/10"}, {"probabilidad_deficit": 1.5}, {"deficit_por_franja_mwh": (1.0, 2.0)},
    ])
    def test_un_mes_invalido_se_rechaza(self, cambio):
        with pytest.raises(ValueError):
            mes(**cambio)

    @pytest.mark.parametrize("args", [
        dict(modo="otro"), dict(modo="manual", oni=3.0), dict(modo="manual", oni=1.05), dict(simulaciones=10), dict(horizonte=7),
    ])
    def test_un_escenario_invalido_se_rechaza(self, args):
        with pytest.raises(ValueError):
            escenario(**args)

    def test_modo_probabilistico_no_lleva_oni_y_manual_si(self):
        with pytest.raises(ValueError):
            EscenarioApagon(modo="probabilistico", oni=1.0, simulaciones=2000, horizonte=12, meses=escenario().meses)
        with pytest.raises(ValueError):
            EscenarioApagon(modo="manual", oni=None, simulaciones=2000, horizonte=12, meses=escenario().meses)

    def test_los_meses_deben_coincidir_con_el_horizonte(self):
        with pytest.raises(ValueError):
            replace(escenario(), meses=escenario().meses[:5])


@pytest.fixture
def repo(tmp_path):
    return DuckDBEscenarioApagonRepository(DuckDBConnection(str(tmp_path / "e.duckdb")))


class TestRepositorio:
    def test_sin_importar_no_hay_escenario_ni_fuente(self, repo):
        assert repo.obtener("manual", 1.0, 2000, 12) is None and repo.fuente() is None

    def test_ida_y_vuelta_exacta(self, repo):
        e, p = escenario(), escenario("probabilistico", horizonte=18)
        repo.reemplazar([e, p], FUENTE)
        assert repo.obtener("manual", 1.0, 2000, 12) == e
        assert repo.obtener("probabilistico", None, 2000, 18) == p
        assert repo.obtener("manual", 1.1, 2000, 12) is None
        assert repo.fuente() == FUENTE

    def test_reemplazar_sustituye_toda_la_tanda(self, repo):
        repo.reemplazar([escenario(), escenario(oni=0.0)], FUENTE)
        repo.reemplazar([escenario(oni=2.0)], FUENTE)
        assert repo.obtener("manual", 1.0, 2000, 12) is None and repo.obtener("manual", 2.0, 2000, 12) is not None

    def test_una_falla_a_la_mitad_no_deja_la_tanda_a_medias(self, repo):
        repo.reemplazar([escenario()], FUENTE)
        malo = object()  # sin .clave: falla al insertar
        with pytest.raises(Exception):
            repo.reemplazar([escenario(oni=0.0), malo], FUENTE)  # type: ignore[list-item]
        assert repo.obtener("manual", 1.0, 2000, 12) is not None and repo.obtener("manual", 0.0, 2000, 12) is None


def _resultado(meses=("2026-09-01", "2026-10-01"), sin_franja=False, sin_columna=None):
    n = len(meses)
    columnas = {
        "mes": list(meses), "oni_p10": [0.1] * n, "oni_p50": [1.0] * n, "oni_p90": [1.9] * n, "embalse_pct_p10": [40.0] * n,
        "embalse_pct_p50": [50.0] * n, "embalse_pct_p90": [60.0] * n, "demanda_mwh_p10": [1.0] * n, "demanda_mwh_p50": [2.0] * n,
        "demanda_mwh_p90": [3.0] * n, "oferta_total_mwh_p10": [1.0] * n, "oferta_total_mwh_p50": [2.5] * n, "oferta_total_mwh_p90": [3.5] * n,
        "deficit_mwh_p50": [5.0] * n, "deficit_mwh_p90": [50.0] * n, "probabilidad_deficit": [0.2] * n, "probabilidad_apagon_severo": [0.05] * n,
        "margen_reserva_pct_p50": [0.1] * n, "indice_riesgo_0_100": [8.0] * n, "semaforo": ["Amarillo"] * n,
    }
    if sin_columna:
        columnas.pop(sin_columna)
    filas = [(m, f, 0.2, 100.0, 10.0 + i) for m in meses for i, f in enumerate(FRANJAS if not sin_franja else FRANJAS[:3])]
    franjas = pd.DataFrame(filas, columns=["mes", "franja", "probabilidad_deficit_horas", "deficit_medio_mwh_condicional", "deficit_esperado_mwh"])
    return {"resumen_mensual": pd.DataFrame(columnas), "detalle_franjas_horarias": franjas}


class TestAdaptador:
    def test_convierte_la_salida_del_modelo(self):
        e = escenario_desde_resultado(_resultado(tuple(f"2026-{m:02d}-01" for m in range(1, 13))), "manual", 1.0, 2000, 12)
        assert e.meses[0].mes == "2026-01" and e.meses[0].semaforo == "AMARILLO"
        assert e.meses[0].deficit_por_franja_mwh == (10.0, 11.0, 12.0, 13.0, 14.0)
        assert e.meses[0].oferta_mwh_p50 == 2.5 and e.meses[0].indice_riesgo == 8.0

    def test_falta_una_columna_del_modelo(self):
        with pytest.raises(SalidaModeloInvalidaError, match="deficit_mwh_p90"):
            escenario_desde_resultado(_resultado(tuple(f"2026-{m:02d}-01" for m in range(1, 13)), sin_columna="deficit_mwh_p90"), "manual", 1.0, 2000, 12)

    def test_falta_una_franja_horaria(self):
        with pytest.raises(SalidaModeloInvalidaError, match="franjas"):
            escenario_desde_resultado(_resultado(tuple(f"2026-{m:02d}-01" for m in range(1, 13)), sin_franja=True), "manual", 1.0, 2000, 12)


class EscenariosEnMemoria(EscenarioApagonRepository):
    def __init__(self, *escenarios, fuente=FUENTE):
        self.datos = {(e.modo, e.oni, e.simulaciones, e.horizonte): e for e in escenarios}
        self._fuente = fuente if escenarios else None

    def obtener(self, modo, oni, simulaciones, horizonte):
        return self.datos.get((modo, oni, simulaciones, horizonte))

    def fuente(self):
        return self._fuente

    def reemplazar(self, escenarios, fuente):
        raise NotImplementedError


def _cliente(*escenarios):
    repo = EscenariosEnMemoria(*escenarios)
    app.dependency_overrides[dep.obtener_catalogo_escenarios_apagon_use_case] = lambda: ObtenerCatalogoEscenariosApagonUseCase(repo)
    app.dependency_overrides[dep.obtener_escenario_apagon_use_case] = lambda: ObtenerEscenarioApagonUseCase(repo)
    return TestClient(app)


@pytest.fixture
def cliente():
    yield _cliente(escenario(), escenario("probabilistico"))
    app.dependency_overrides.clear()


@pytest.fixture
def cliente_vacio():
    yield _cliente()
    app.dependency_overrides.clear()


U = "/api/v1/modelos/apagon"


class TestApi:
    def test_catalogo_con_las_opciones_de_los_controles(self, cliente):
        c = cliente.get(f"{U}/escenarios").json()
        assert c["disponible"] and c["modos"] == ["probabilistico", "manual"]
        assert (c["oni_minimo"], c["oni_maximo"], c["oni_paso"]) == (-2.5, 2.5, 0.1)
        assert c["simulaciones"] == [1000, 2000, 5000] and c["horizontes"] == [12, 18, 24] and len(c["franjas"]) == 5
        assert c["fuente"]["semilla"] == 7 and c["fuente"]["ultimo_mes_demanda"] == "2026-08-01"

    def test_sin_importar_el_catalogo_dice_no_disponible_y_el_escenario_es_404(self, cliente_vacio):
        assert cliente_vacio.get(f"{U}/escenarios").json()["disponible"] is False
        r = cliente_vacio.get(f"{U}/escenario?modo=manual&oni=1.0&simulaciones=2000&horizonte=12")
        assert r.status_code == 404

    def test_escenario_manual_y_probabilistico(self, cliente):
        r = cliente.get(f"{U}/escenario?modo=manual&oni=1.0&simulaciones=2000&horizonte=12").json()
        assert r["oni"] == 1.0 and len(r["meses"]) == 12 and len(r["meses"][0]["deficit_por_franja_mwh"]) == 5
        p = cliente.get(f"{U}/escenario?modo=probabilistico&simulaciones=2000&horizonte=12").json()
        assert p["oni"] is None and p["modo"] == "probabilistico"

    def test_el_oni_se_ignora_en_modo_probabilistico(self, cliente):
        assert cliente.get(f"{U}/escenario?modo=probabilistico&oni=2.0&horizonte=12").status_code == 200

    @pytest.mark.parametrize("consulta", [
        "modo=otro", "modo=manual&oni=3", "modo=manual&oni=1.05", "modo=manual&oni=abc", "simulaciones=10", "horizonte=7", "modo=MANUAL",
    ])
    def test_parametros_fuera_de_las_opciones_son_422(self, cliente, consulta):
        assert cliente.get(f"{U}/escenario?{consulta}").status_code == 422

    def test_solo_get(self, cliente):
        assert cliente.post(f"{U}/escenario").status_code == 405
        assert cliente.delete(f"{U}/escenarios").status_code == 405
