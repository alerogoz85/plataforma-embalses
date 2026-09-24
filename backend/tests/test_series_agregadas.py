from datetime import date, timedelta

import pytest

from application.series_agregadas import SeriesAgregadas
from application.use_cases.generar_prediccion import GenerarPrediccionUseCase
from application.use_cases.obtener_detalle_embalse import ObtenerDetalleEmbalseUseCase
from domain.entities.region import NombreRegion
from domain.exceptions import DatosHistoricosInsuficientesError, SinMedicionesError
from tests.fakes import (
    EmbalseRepositoryEnMemoria,
    ForecastingPersistencia,
    MedicionRepositoryEnMemoria,
    ProyeccionSendaRepositoryEnMemoria,
    caudal,
    crear_embalse,
    crear_medicion,
    crear_proyeccion_publicada,
)

FIN = date(2026, 9, 22)
DIAS = 40


def _serie(embalse, pct, capacidad_energia, dias=DIAS, **opcionales):
    return [
        crear_medicion(embalse, FIN - timedelta(days=i), pct, capacidad_energia, **opcionales)
        for i in range(dias)
    ]


@pytest.fixture
def mundo():
    # Grande (Centro, peso 300, 80%), pequeno (Centro, peso 100, 40%) y otro (Valle, 50%).
    grande = crear_embalse("G", NombreRegion.CENTRO)
    pequeno = crear_embalse("P", NombreRegion.CENTRO)
    valle = crear_embalse("V", NombreRegion.VALLE)
    mediciones = (
        _serie(grande, 80.0, 300.0, aportes=caudal(30.0), aportes_media_historica_m3s=60.0)
        + _serie(pequeno, 40.0, 100.0, aportes=caudal(10.0), aportes_media_historica_m3s=20.0)
        + _serie(valle, 50.0, 100.0)
    )
    return [grande, pequeno, valle], mediciones


@pytest.fixture
def agregadas(mundo):
    embalses, mediciones = mundo
    return SeriesAgregadas(EmbalseRepositoryEnMemoria(embalses), MedicionRepositoryEnMemoria(mediciones))


class TestResolver:
    def test_total_incluye_todos_los_embalses(self, agregadas):
        grupo = agregadas.resolver("TOTAL")
        assert grupo.nombre == "Total nacional" and {e.id for e in grupo.embalses} == {"G", "P", "V"}

    def test_region_incluye_solo_los_de_esa_region(self, agregadas):
        grupo = agregadas.resolver("REGION:Centro")
        assert grupo.id == "REGION:Centro" and grupo.nombre == "Región Centro"
        assert {e.id for e in grupo.embalses} == {"G", "P"}

    def test_la_region_no_distingue_mayusculas(self, agregadas):
        assert agregadas.resolver("REGION:centro").id == "REGION:Centro"

    @pytest.mark.parametrize("id_", ["G", "REGION:Marte", "REGION:", "total"])
    def test_lo_demas_no_es_un_agregado(self, agregadas, id_):
        assert agregadas.resolver(id_) is None


class TestSerie:
    def test_pondera_el_pct_por_la_capacidad_en_energia(self, agregadas):
        punto = agregadas.serie(agregadas.resolver("REGION:Centro"))[-1]
        # (80*300 + 40*100) / 400 = 70; un promedio simple daria 60.
        assert punto.pct_volumen_util == pytest.approx(70.0)

    def test_total_pondera_los_tres(self, agregadas):
        punto = agregadas.serie(agregadas.resolver("TOTAL"))[-1]
        assert punto.pct_volumen_util == pytest.approx((80 * 300 + 40 * 100 + 50 * 100) / 500)

    def test_aportes_son_total_sobre_total_solo_entre_quienes_publican(self, agregadas):
        punto = agregadas.serie(agregadas.resolver("TOTAL"))[-1]  # V no publica aportes
        assert punto.aportes_pct_media == pytest.approx((30 + 10) / (60 + 20) * 100)
        assert punto.aportes_m3s == 40.0

    def test_sin_aportes_publicados_es_none_no_cero(self, agregadas):
        punto = agregadas.serie(agregadas.resolver("REGION:Valle"))[-1]
        assert punto.aportes_pct_media is None and punto.aportes_m3s is None

    def test_suma_volumen_y_capacidad(self, agregadas):
        punto = agregadas.serie(agregadas.resolver("REGION:Centro"))[-1]
        assert punto.capacidad_util_mm3 == 200.0 and punto.volumen_util_mm3 == pytest.approx(120.0)

    def test_una_serie_por_dia_ordenada(self, agregadas):
        fechas = [p.fecha for p in agregadas.serie(agregadas.resolver("TOTAL"))]
        assert fechas == sorted(set(fechas)) and len(fechas) == DIAS

    def test_respeta_el_rango_de_fechas(self, agregadas):
        puntos = agregadas.serie(agregadas.resolver("TOTAL"), FIN - timedelta(days=4), FIN - timedelta(days=2))
        assert [p.fecha for p in puntos] == [FIN - timedelta(days=d) for d in (4, 3, 2)]


class TestDetalleAgregado:
    def _caso(self, mundo):
        embalses, mediciones = mundo
        return ObtenerDetalleEmbalseUseCase(
            EmbalseRepositoryEnMemoria(embalses), MedicionRepositoryEnMemoria(mediciones)
        )

    def test_total_devuelve_resumen_y_serie(self, mundo):
        detalle = self._caso(mundo).ejecutar("TOTAL")
        assert detalle.resumen.id == "TOTAL" and detalle.resumen.es_agregado
        assert detalle.resumen.nombre == "Total nacional" and detalle.resumen.region == "Nacional"
        assert detalle.resumen.fecha == FIN
        assert detalle.resumen.pct_volumen_util == pytest.approx(66.0)  # (24000+4000+5000)/500
        assert len(detalle.serie_historica) == DIAS

    def test_el_rango_recorta_la_serie_pero_los_deltas_siguen_disponibles(self, mundo):
        detalle = self._caso(mundo).ejecutar("REGION:Centro", fecha_inicio=FIN - timedelta(days=2), fecha_fin=FIN)
        assert [p.fecha for p in detalle.serie_historica][0] == FIN - timedelta(days=2)
        assert detalle.resumen.delta_diario_pct == 0.0  # serie constante: existe el dia previo

    def test_sin_datos_da_error_de_dominio(self):
        caso = ObtenerDetalleEmbalseUseCase(
            EmbalseRepositoryEnMemoria([crear_embalse("G")]), MedicionRepositoryEnMemoria([])
        )
        with pytest.raises(SinMedicionesError):
            caso.ejecutar("TOTAL")


class TestPrediccionAgregada:
    def _caso(self, mundo, publicada=()):
        embalses, mediciones = mundo
        self.forecasting = ForecastingPersistencia()
        return GenerarPrediccionUseCase(
            EmbalseRepositoryEnMemoria(embalses),
            MedicionRepositoryEnMemoria(mediciones),
            self.forecasting,
            ProyeccionSendaRepositoryEnMemoria(list(publicada)),
        )

    def test_total_usa_la_proyeccion_de_outputs_si_existe(self, mundo):
        pred = self._caso(mundo, crear_proyeccion_publicada("TOTAL", inicio=date(2026, 10, 1))).ejecutar("TOTAL", 90)
        assert pred.origen == "outputs" and pred.nivel_confianza is None and len(pred.puntos) == 90

    def test_una_region_sin_proyeccion_publicada_usa_el_respaldo_sobre_la_serie_agregada(self, mundo):
        pred = self._caso(mundo, crear_proyeccion_publicada("TOTAL", inicio=date(2026, 10, 1))).ejecutar("REGION:Centro", 30)
        assert pred.origen == "holt_winters" and pred.embalse_id == "REGION:Centro"
        assert self.forecasting.llamadas[0]["serie"][-1] == pytest.approx(70.0)

    def test_historia_insuficiente_del_agregado(self):
        g = crear_embalse("G")
        caso = GenerarPrediccionUseCase(
            EmbalseRepositoryEnMemoria([g]),
            MedicionRepositoryEnMemoria(_serie(g, 50.0, 100.0, dias=10)),
            ForecastingPersistencia(),
        )
        with pytest.raises(DatosHistoricosInsuficientesError):
            caso.ejecutar("TOTAL", 30)
