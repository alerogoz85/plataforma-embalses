from datetime import date

import pytest

from application.use_cases.obtener_resumen_nacional import ObtenerResumenNacionalUseCase
from domain.entities.region import NombreRegion
from domain.services.calculo_hidrico_service import CalculoHidricoService
from tests.fakes import (
    EmbalseRepositoryEnMemoria,
    MedicionRepositoryEnMemoria,
    caudal,
    crear_embalse,
    crear_medicion,
)


class TestAgregarPctMensual:
    def test_promedia_los_valores_diarios_de_cada_mes(self):
        serie = [
            (date(2024, 1, 1), 10.0),
            (date(2024, 1, 2), 20.0),
            (date(2024, 2, 1), 40.0),
        ]
        resultado = CalculoHidricoService.agregar_pct_mensual(serie)
        assert [valor for _, valor in resultado] == [15.0, 40.0]

    def test_representa_cada_mes_con_su_ultimo_dia_observado(self):
        serie = [(date(2024, 1, 3), 10.0), (date(2024, 1, 20), 20.0)]
        assert CalculoHidricoService.agregar_pct_mensual(serie)[0][0] == date(2024, 1, 20)

    def test_ordena_por_fecha_aunque_la_entrada_venga_desordenada(self):
        serie = [
            (date(2024, 3, 1), 30.0),
            (date(2024, 1, 1), 10.0),
            (date(2024, 2, 1), 20.0),
        ]
        fechas = [fecha for fecha, _ in CalculoHidricoService.agregar_pct_mensual(serie)]
        assert fechas == sorted(fechas)

    def test_separa_el_mismo_mes_de_anios_distintos(self):
        serie = [(date(2024, 1, 1), 10.0), (date(2025, 1, 1), 50.0)]
        resultado = CalculoHidricoService.agregar_pct_mensual(serie)
        assert [valor for _, valor in resultado] == [10.0, 50.0]

    def test_serie_vacia_devuelve_lista_vacia(self):
        assert CalculoHidricoService.agregar_pct_mensual([]) == []


HOY = date(2026, 1, 10)


def _resumen(embalses, mediciones, **filtros):
    return ObtenerResumenNacionalUseCase(
        EmbalseRepositoryEnMemoria(embalses), MedicionRepositoryEnMemoria(mediciones)
    ).ejecutar(**filtros)


class TestAgregacionNacionalYRegional:
    def setup_method(self):
        # A: lleno y con mucha energia. B: vacio, poca energia pero mucho volumen.
        # Ponderado por energia -> (100*900 + 0*100)/1000 = 90; por volumen seria ~9.
        self.a = crear_embalse("A", NombreRegion.ANTIOQUIA)
        self.b = crear_embalse("B", NombreRegion.CARIBE)
        self.mediciones = [
            crear_medicion(self.a, HOY, 100.0, capacidad_energia_gwh=900, capacidad_mm3=100),
            crear_medicion(self.b, HOY, 0.0, capacidad_energia_gwh=100, capacidad_mm3=1000),
        ]

    def test_kpi_nacional_pondera_por_capacidad_en_energia_no_por_volumen(self):
        resultado = _resumen([self.a, self.b], self.mediciones)
        assert resultado.kpis.pct_volumen_util_nacional == pytest.approx(90.0, abs=0.01)

    def test_regional_pondera_por_energia_dentro_de_la_region(self):
        a2 = crear_embalse("A2", NombreRegion.ANTIOQUIA)
        mediciones = self.mediciones + [
            crear_medicion(a2, HOY, 0.0, capacidad_energia_gwh=100, capacidad_mm3=100)
        ]
        resultado = _resumen([self.a, a2, self.b], mediciones)
        antioquia = next(r for r in resultado.regiones if r.region == "Antioquia")
        assert antioquia.pct_volumen_util == pytest.approx(90.0, abs=0.01)
        assert antioquia.num_embalses == 2

    def test_el_pct_por_embalse_sigue_siendo_volumetrico(self):
        resultado = _resumen([self.a, self.b], self.mediciones)
        assert {e.id: e.pct_volumen_util for e in resultado.embalses} == {"A": 100.0, "B": 0.0}

    def test_capacidad_guardada_suma_la_energia_publicada(self):
        resultado = _resumen([self.a, self.b], self.mediciones)
        assert resultado.kpis.capacidad_guardada_gwh == pytest.approx(900.0, abs=0.01)

    def test_capacidad_guardada_ignora_embalses_sin_energia_publicada(self):
        sin_energia = crear_medicion(
            self.b, HOY, 50.0, capacidad_energia_gwh=100, energia_util_gwh=None
        )
        resultado = _resumen([self.a, self.b], [self.mediciones[0], sin_energia])
        assert resultado.kpis.capacidad_guardada_gwh == pytest.approx(900.0, abs=0.01)

    def test_sin_embalses_devuelve_kpis_en_cero(self):
        resultado = _resumen([], [])
        assert resultado.kpis.total_embalses == 0
        assert resultado.kpis.pct_volumen_util_nacional == 0.0
        assert resultado.kpis.aportes_pct_media_nacional is None

    def test_filtra_por_region(self):
        resultado = _resumen([self.a, self.b], self.mediciones, regiones=["Caribe"])
        assert resultado.kpis.total_embalses == 1
        assert resultado.kpis.pct_volumen_util_nacional == 0.0

    def test_incluye_agregados_en_el_total_nacional(self):
        agregado = crear_embalse("AGG", NombreRegion.CENTRO, es_agregado=True)
        med = crear_medicion(agregado, HOY, 0.0, capacidad_energia_gwh=900)
        resultado = _resumen([self.a, agregado], [self.mediciones[0], med])
        assert resultado.kpis.pct_volumen_util_nacional == pytest.approx(50.0, abs=0.01)
        assert resultado.kpis.total_embalses == 2


class TestAportesNacionales:
    def test_relaciona_aportes_totales_con_media_total_no_promedia_porcentajes(self):
        a = crear_embalse("A")
        b = crear_embalse("B")
        mediciones = [
            crear_medicion(a, HOY, 50, aportes=caudal(10), aportes_media_historica_m3s=10.0),
            crear_medicion(b, HOY, 50, aportes=caudal(90), aportes_media_historica_m3s=270.0),
        ]
        resultado = _resumen([a, b], mediciones)
        # Total 100 / media 280 = 35.71% (un promedio simple de 100% y 33.3% daria 66.7%).
        assert resultado.kpis.aportes_pct_media_nacional == pytest.approx(35.71, abs=0.01)

    def test_ignora_embalses_sin_aportes_publicados(self):
        a = crear_embalse("A")
        muna = crear_embalse("MUNA")
        mediciones = [
            crear_medicion(a, HOY, 50, aportes=caudal(50), aportes_media_historica_m3s=100.0),
            crear_medicion(muna, HOY, 50),
        ]
        resultado = _resumen([a, muna], mediciones)
        assert resultado.kpis.aportes_pct_media_nacional == 50.0
