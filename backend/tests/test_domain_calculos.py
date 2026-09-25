from datetime import date

import pytest

from domain.exceptions import CaudalInvalidoError, VolumenInvalidoError
from domain.services.autonomia_service import AutonomiaService
from domain.services.calculo_hidrico_service import CalculoHidricoService
from domain.value_objects.caudal import Caudal
from domain.value_objects.porcentaje import NivelRiesgo, Porcentaje
from domain.value_objects.volumen import Volumen
from tests.fakes import caudal, crear_embalse, crear_medicion

EMBALSE = crear_embalse("A")
HOY = date(2026, 1, 10)


def _medicion(pct: float, **opcionales):
    return crear_medicion(EMBALSE, HOY, pct, **opcionales)


class TestPorcentajeVolumenUtil:
    def test_es_volumen_util_sobre_capacidad_util_del_dia(self):
        assert CalculoHidricoService.calcular_porcentaje_volumen_util(_medicion(50)).valor == 50.0

    def test_usa_la_capacidad_publicada_ese_dia(self):
        # La misma cantidad de agua es un % distinto si XM revisa la capacidad.
        antes = crear_medicion(EMBALSE, HOY, 50, capacidad_mm3=100)
        despues = crear_medicion(
            EMBALSE, HOY, 50, capacidad_mm3=200, volumen_util=Volumen(50)
        )
        assert CalculoHidricoService.calcular_porcentaje_volumen_util(antes).valor == 50.0
        assert CalculoHidricoService.calcular_porcentaje_volumen_util(despues).valor == 25.0

    def test_no_acota_por_arriba_valores_sobre_capacidad_nominal(self):
        pct = CalculoHidricoService.calcular_porcentaje_volumen_util(_medicion(111.8))
        assert pct.valor == 111.8
        assert pct.nivel_riesgo == NivelRiesgo.NORMAL

    def test_capacidad_cero_no_divide_por_cero(self):
        medicion = crear_medicion(EMBALSE, HOY, 0, capacidad_mm3=0)
        assert CalculoHidricoService.calcular_porcentaje_volumen_util(medicion).valor == 0.0

    @pytest.mark.parametrize(
        "pct,esperado",
        [
            (0, NivelRiesgo.CRITICO),
            (49.99, NivelRiesgo.CRITICO),
            (50, NivelRiesgo.SITUACION_DELICADA),
            (59.99, NivelRiesgo.SITUACION_DELICADA),
            (60, NivelRiesgo.ALERTA_TEMPRANA),
            (69.99, NivelRiesgo.ALERTA_TEMPRANA),
            (70, NivelRiesgo.ESTABLE),
            (80, NivelRiesgo.ESTABLE),
            (80.01, NivelRiesgo.NORMAL),
            (100, NivelRiesgo.NORMAL),
            (111.8, NivelRiesgo.NORMAL),
        ],
    )
    def test_clasificacion_de_riesgo_en_los_umbrales_de_5_niveles(self, pct, esperado):
        assert Porcentaje(pct).nivel_riesgo == esperado

    def test_delta_en_puntos_porcentuales(self):
        assert CalculoHidricoService.calcular_delta_porcentual(Porcentaje(55), Porcentaje(50)) == 5.0


class TestAportesPctMedia:
    def test_relacion_con_la_media_historica(self):
        medicion = _medicion(50, aportes=Caudal(30), aportes_media_historica_m3s=60.0)
        assert CalculoHidricoService.calcular_aportes_pct_media(medicion) == 50.0

    def test_none_si_no_hay_aportes_publicados(self):
        assert CalculoHidricoService.calcular_aportes_pct_media(_medicion(50)) is None

    def test_none_si_no_hay_media_historica(self):
        medicion = _medicion(50, aportes=Caudal(30))
        assert CalculoHidricoService.calcular_aportes_pct_media(medicion) is None


class TestEnergia:
    def test_capacidad_guardada_es_la_energia_publicada(self):
        medicion = _medicion(50, capacidad_energia_gwh=200.0)
        assert CalculoHidricoService.calcular_capacidad_guardada_gwh(medicion) == 100.0

    def test_capacidad_guardada_es_cero_si_xm_no_la_publica(self):
        assert CalculoHidricoService.calcular_capacidad_guardada_gwh(
            _medicion(50, energia_util_gwh=None)
        ) == 0.0

    def test_el_peso_de_agregacion_es_la_capacidad_en_energia(self):
        medicion = _medicion(50, capacidad_energia_gwh=321.0)
        assert CalculoHidricoService.calcular_peso_energetico_agregacion(medicion) == 321.0


def _con_balance(aportes, turbinado, vertimientos, pct=50):
    return _medicion(
        pct,
        aportes=caudal(aportes),
        turbinado=caudal(turbinado),
        vertimientos=caudal(vertimientos),
    )


class TestAutonomia:
    def test_infinita_si_los_aportes_superan_las_salidas(self):
        assert AutonomiaService.calcular_dias_autonomia(_con_balance(50, 20, 1)) is None

    def test_finita_cuando_las_salidas_superan_los_aportes(self):
        # Util = 50 Mm3; balance = (10 + 5 - 1) m3/s = 14 m3/s = 1.2096 Mm3/dia -> 41 dias.
        assert AutonomiaService.calcular_dias_autonomia(_con_balance(1, 10, 5)) == 41

    def test_incluye_la_descarga_turbinada_en_las_salidas(self):
        # Aportes 10 m3/s frente a vertimientos 5: sin turbinar el embalse se llena.
        sin_turbinar = AutonomiaService.calcular_dias_autonomia(_con_balance(10, 0, 5))
        turbinando = AutonomiaService.calcular_dias_autonomia(_con_balance(10, 10, 5))
        assert sin_turbinar is None
        assert turbinando is not None

    def test_cero_si_no_queda_volumen_util(self):
        assert AutonomiaService.calcular_dias_autonomia(_con_balance(1, 10, 5, pct=0)) == 0

    @pytest.mark.parametrize("faltante", ["aportes", "turbinado", "vertimientos"])
    def test_none_si_falta_algun_dato_publicado(self, faltante):
        datos = {"aportes": 1, "turbinado": 10, "vertimientos": 5}
        datos[faltante] = None
        assert AutonomiaService.calcular_dias_autonomia(_con_balance(**datos)) is None


class TestValueObjects:
    def test_volumen_no_puede_ser_negativo(self):
        with pytest.raises(VolumenInvalidoError):
            Volumen(-1)

    def test_caudal_no_puede_ser_negativo(self):
        with pytest.raises(CaudalInvalidoError):
            Caudal(-1)

    def test_el_porcentaje_no_baja_de_cero(self):
        assert Porcentaje(-5).valor == 0.0
