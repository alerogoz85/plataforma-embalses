import math
from datetime import date, timedelta

import numpy as np

from infrastructure.ml.holt_winters_forecasting_service import HoltWintersForecastingService


def _fechas_mensuales(n: int) -> list[date]:
    return [date(2020, 1, 31) + timedelta(days=30 * i) for i in range(n)]


def _serie_estacional(n: int) -> list[float]:
    return [60 + 20 * math.sin(2 * math.pi * i / 12) for i in range(n)]


def _error_medio(proyeccion, reales) -> float:
    return float(np.mean([abs(p.valor_esperado - r) for p, r in zip(proyeccion, reales)]))


class TestHoltWintersEstacional:
    def test_estacional_reproduce_el_ciclo_anual_mejor_que_el_no_estacional(self):
        completa = _serie_estacional(60)
        entrenamiento, futuro = completa[:48], completa[48:60]
        fechas = _fechas_mensuales(48)

        estacional = HoltWintersForecastingService(estacional=True).proyectar(
            entrenamiento, fechas, 12, paso_dias=30
        )
        plano = HoltWintersForecastingService().proyectar(entrenamiento, fechas, 12, paso_dias=30)

        assert _error_medio(estacional, futuro) < 1.0
        assert _error_medio(estacional, futuro) < _error_medio(plano, futuro) / 3

    def test_con_menos_de_dos_ciclos_cae_al_modelo_sin_estacionalidad(self):
        serie = _serie_estacional(23)
        puntos = HoltWintersForecastingService(estacional=True).proyectar(
            serie, _fechas_mensuales(23), 6, paso_dias=30
        )
        assert len(puntos) == 6

    def test_con_dos_ciclos_completos_ya_usa_estacionalidad(self):
        completa = _serie_estacional(36)
        puntos = HoltWintersForecastingService(estacional=True).proyectar(
            completa[:24], _fechas_mensuales(24), 12, paso_dias=30
        )
        assert _error_medio(puntos, completa[24:36]) < 2.0

    def test_las_fechas_avanzan_paso_dias_desde_la_ultima_observacion(self):
        fechas = _fechas_mensuales(30)
        puntos = HoltWintersForecastingService(estacional=True).proyectar(
            _serie_estacional(30), fechas, 3, paso_dias=30
        )
        assert [p.fecha for p in puntos] == [fechas[-1] + timedelta(days=30 * i) for i in (1, 2, 3)]

    def test_paso_por_defecto_es_diario(self):
        serie = [50 + 0.1 * i for i in range(60)]
        fechas = [date(2024, 1, 1) + timedelta(days=i) for i in range(60)]
        puntos = HoltWintersForecastingService().proyectar(serie, fechas, 2)
        assert [p.fecha for p in puntos] == [fechas[-1] + timedelta(days=1), fechas[-1] + timedelta(days=2)]

    def test_valores_e_intervalo_quedan_acotados_entre_0_y_100(self):
        serie = [95 + 4 * math.sin(2 * math.pi * i / 12) for i in range(48)]
        puntos = HoltWintersForecastingService(estacional=True).proyectar(
            serie, _fechas_mensuales(48), 12, paso_dias=30
        )
        for p in puntos:
            assert 0 <= p.limite_inferior <= p.valor_esperado <= p.limite_superior <= 100

    def test_el_nombre_del_metodo_distingue_la_variante_estacional(self):
        assert "estacional" in HoltWintersForecastingService(estacional=True).nombre_metodo()
        assert "estacional" not in HoltWintersForecastingService().nombre_metodo()
