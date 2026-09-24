from datetime import date

import pytest

from application.use_cases.obtener_senda_volumen import (
    MESES_VALIDACION,
    MINIMO_MESES_HISTORICO,
    PASO_DIAS_MENSUAL,
    ObtenerSendaVolumenUseCase,
)
from domain.exceptions import (
    DatosHistoricosInsuficientesError,
    EmbalseNoEncontradoError,
    SinMedicionesError,
)
from tests.fakes import (
    EmbalseRepositoryEnMemoria,
    ForecastingPersistencia,
    MedicionRepositoryEnMemoria,
    crear_embalse,
    serie_mensual_constante,
)

MESES = 20


def _caso(embalses, mediciones, forecasting=None):
    forecasting = forecasting or ForecastingPersistencia()
    caso = ObtenerSendaVolumenUseCase(
        EmbalseRepositoryEnMemoria(embalses), MedicionRepositoryEnMemoria(mediciones), forecasting
    )
    return caso, forecasting


def _rampa(n=MESES, inicio=10.0, paso=1.0):
    return [inicio + paso * i for i in range(n)]


class TestSendaEmbalseIndividual:
    def setup_method(self):
        self.embalse = crear_embalse("A")
        self.valores = _rampa()
        self.caso, self.forecasting = _caso(
            [self.embalse], serie_mensual_constante(self.embalse, self.valores)
        )

    def test_historico_mensual_coincide_con_los_datos(self):
        senda = self.caso.ejecutar("A", horizonte_meses=6)
        assert [p.pct_volumen_util for p in senda.historico] == pytest.approx(self.valores, abs=0.01)
        assert senda.historico[0].mes == "2024-01"
        assert senda.historico[-1].mes == "2025-08"

    def test_ultimo_observado_es_el_ultimo_mes(self):
        senda = self.caso.ejecutar("A")
        assert senda.ultimo_observado.mes == "2025-08"
        assert senda.ultimo_observado.pct_volumen_util == pytest.approx(self.valores[-1], abs=0.01)

    @pytest.mark.parametrize("horizonte", [6, 12, 18])
    def test_proyecta_el_horizonte_solicitado(self, horizonte):
        senda = self.caso.ejecutar("A", horizonte_meses=horizonte)
        assert len(senda.proyeccion) == horizonte

    def test_proyeccion_usa_paso_mensual_y_horizonte_en_meses(self):
        self.caso.ejecutar("A", horizonte_meses=12)
        principal = self.forecasting.llamadas[0]
        assert principal["horizonte"] == 12
        assert principal["paso_dias"] == PASO_DIAS_MENSUAL

    def test_minimo_proyectado_es_el_menor_valor_esperado(self):
        senda = self.caso.ejecutar("A", horizonte_meses=6)
        menor = min(p.valor_esperado for p in senda.proyeccion)
        assert senda.minimo_proyectado.valor_esperado == menor

    def test_nombra_el_embalse_y_el_metodo(self):
        senda = self.caso.ejecutar("A")
        assert senda.nombre == "Embalse A"
        assert senda.metodo == "Persistencia de prueba"


class TestSendaTotalNacional:
    def test_pondera_por_capacidad_en_energia(self):
        lleno = crear_embalse("A")
        vacio = crear_embalse("B")
        mediciones = serie_mensual_constante(
            lleno, [100.0] * MESES, capacidad_energia_gwh=900
        ) + serie_mensual_constante(vacio, [0.0] * MESES, capacidad_energia_gwh=100)
        caso, _ = _caso([lleno, vacio], mediciones)

        senda = caso.ejecutar("TOTAL")

        assert senda.nombre == "Total nacional"
        assert senda.ultimo_observado.pct_volumen_util == pytest.approx(90.0, abs=0.01)
        assert all(p.pct_volumen_util == pytest.approx(90.0, abs=0.01) for p in senda.historico)

    def test_es_el_valor_por_defecto(self):
        embalse = crear_embalse("A")
        caso, _ = _caso([embalse], serie_mensual_constante(embalse, _rampa()))
        assert caso.ejecutar().embalse_id == "TOTAL"


class TestSendaErrores:
    def test_embalse_inexistente(self):
        caso, _ = _caso([], [])
        with pytest.raises(EmbalseNoEncontradoError):
            caso.ejecutar("NOPE")

    def test_embalse_sin_mediciones(self):
        caso, _ = _caso([crear_embalse("A")], [])
        with pytest.raises(SinMedicionesError):
            caso.ejecutar("A")

    def test_historia_insuficiente(self):
        embalse = crear_embalse("A")
        mediciones = serie_mensual_constante(embalse, _rampa(MINIMO_MESES_HISTORICO - 1))
        caso, _ = _caso([embalse], mediciones)
        with pytest.raises(DatosHistoricosInsuficientesError) as error:
            caso.ejecutar("A")
        assert error.value.requeridos == MINIMO_MESES_HISTORICO
        assert error.value.disponibles == MINIMO_MESES_HISTORICO - 1

    def test_historia_minima_exacta_es_suficiente(self):
        embalse = crear_embalse("A")
        mediciones = serie_mensual_constante(embalse, _rampa(MINIMO_MESES_HISTORICO))
        caso, _ = _caso([embalse], mediciones)
        assert caso.ejecutar("A").historico


class TestValidacionWalkForward:
    def test_devuelve_persistencia_y_modelo(self):
        embalse = crear_embalse("A")
        caso, _ = _caso([embalse], serie_mensual_constante(embalse, _rampa()))
        modelos = [m.modelo for m in caso.ejecutar("A").validacion]
        assert modelos == ["Persistencia (ultimo valor)", "Persistencia de prueba"]

    def test_mae_y_r2_de_una_rampa_con_persistencia(self):
        # Rampa de +1 por mes: persistencia se equivoca exactamente 1 punto cada mes.
        embalse = crear_embalse("A")
        caso, _ = _caso([embalse], serie_mensual_constante(embalse, _rampa(paso=1.0)))

        persistencia = caso.ejecutar("A").validacion[0]

        assert persistencia.mae == pytest.approx(1.0, abs=0.001)
        # SS_res = 6, SS_tot = 6 * var(rampa de 6) = 17.5 -> R2 = 1 - 6/17.5
        assert persistencia.r2 == pytest.approx(1 - 6 / 17.5, abs=0.001)

    def test_serie_constante_da_error_cero_y_r2_cero(self):
        embalse = crear_embalse("A")
        caso, _ = _caso([embalse], serie_mensual_constante(embalse, [50.0] * MESES))
        for metrica in caso.ejecutar("A").validacion:
            assert metrica.mae == 0.0
            assert metrica.r2 == 0.0

    def test_no_usa_informacion_futura_para_predecir_cada_mes(self):
        embalse = crear_embalse("A")
        valores = _rampa()
        caso, forecasting = _caso([embalse], serie_mensual_constante(embalse, valores))

        caso.ejecutar("A")

        folds = [c for c in forecasting.llamadas if c["horizonte"] == 1]
        assert len(folds) == MESES_VALIDACION
        largos = [len(c["serie"]) for c in folds]
        assert largos == list(range(MESES - MESES_VALIDACION, MESES))
        for fold in folds:
            assert fold["serie"] == pytest.approx(valores[: len(fold["serie"])], abs=0.01)

    def test_el_modelo_se_evalua_sobre_los_mismos_meses_que_la_persistencia(self):
        embalse = crear_embalse("A")
        caso, _ = _caso([embalse], serie_mensual_constante(embalse, _rampa()))
        persistencia, modelo = caso.ejecutar("A").validacion
        # El pronostico de prueba repite el ultimo valor, igual que la persistencia.
        assert modelo.mae == persistencia.mae
        assert modelo.r2 == persistencia.r2

    def test_las_fechas_de_entrenamiento_son_anteriores_al_mes_evaluado(self):
        embalse = crear_embalse("A")
        caso, forecasting = _caso([embalse], serie_mensual_constante(embalse, _rampa()))
        caso.ejecutar("A")
        for fold in (c for c in forecasting.llamadas if c["horizonte"] == 1):
            assert fold["fechas"] == sorted(fold["fechas"])
            assert fold["fechas"][-1] < date(2025, 8, 3)
