from datetime import date, timedelta

import pytest

from application.use_cases.generar_prediccion import GenerarPrediccionUseCase
from domain.services.proyeccion_diaria_service import AnclaMensual, ProyeccionDiariaService
from tests.fakes import (
    EmbalseRepositoryEnMemoria,
    ForecastingPersistencia,
    MedicionRepositoryEnMemoria,
    ProyeccionSendaRepositoryEnMemoria,
    crear_embalse,
    crear_medicion,
    crear_proyeccion_publicada,
)

ULTIMA = date(2026, 9, 22)
interpolar = ProyeccionDiariaService.interpolar


def ancla(fecha, valor, ancho=0.0):
    return AnclaMensual(fecha, valor - ancho, valor, valor + ancho)


class TestAncla:
    def test_de_mes_se_sitúa_a_mitad_de_mes(self):
        assert AnclaMensual.de_mes(date(2026, 10, 1), 1.0, 2.0, 3.0).fecha == date(2026, 10, 15)


class TestInterpolacion:
    def test_va_linealmente_del_ultimo_observado_a_la_primera_ancla(self):
        puntos = interpolar(ULTIMA, 80.0, [ancla(date(2026, 10, 15), 57.0)], 30)  # 23 dias de distancia
        assert puntos[0].fecha == ULTIMA + timedelta(days=1)
        assert puntos[0].valor_esperado == pytest.approx(80.0 - 23 / 23)  # baja 1 punto por dia
        assert puntos[10].valor_esperado == pytest.approx(80.0 - 11)

    def test_pasa_exactamente_por_cada_valor_mensual(self):
        anclas = [ancla(date(2026, 10, 15), 60.0), ancla(date(2026, 11, 15), 50.0), ancla(date(2026, 12, 15), 70.0)]
        por_fecha = {p.fecha: p.valor_esperado for p in interpolar(ULTIMA, 80.0, anclas, 120)}
        assert por_fecha[date(2026, 10, 15)] == pytest.approx(60.0)
        assert por_fecha[date(2026, 11, 15)] == pytest.approx(50.0)
        assert por_fecha[date(2026, 12, 15)] == pytest.approx(70.0)

    def test_entre_dos_anclas_es_lineal(self):
        anclas = [ancla(date(2026, 10, 15), 60.0), ancla(date(2026, 11, 14), 90.0)]  # 30 dias
        por_fecha = {p.fecha: p.valor_esperado for p in interpolar(ULTIMA, 80.0, anclas, 60)}
        assert por_fecha[date(2026, 10, 30)] == pytest.approx(75.0)

    def test_la_banda_nace_sin_incertidumbre_y_llega_a_la_de_la_ancla(self):
        anclas = [ancla(date(2026, 10, 15), 60.0, ancho=10.0)]
        puntos = {p.fecha: p for p in interpolar(ULTIMA, 80.0, anclas, 30)}
        primero = puntos[ULTIMA + timedelta(days=1)]
        assert primero.limite_superior - primero.limite_inferior == pytest.approx(2 * 10.0 / 23)
        llegada = puntos[date(2026, 10, 15)]
        assert (llegada.limite_inferior, llegada.limite_superior) == pytest.approx((50.0, 70.0))

    def test_devuelve_tantos_puntos_como_el_horizonte_si_hay_datos_suficientes(self):
        anclas = [ancla(date(2026, 10, 15), 60.0), ancla(date(2027, 4, 15), 40.0)]
        assert [len(interpolar(ULTIMA, 80.0, anclas, h)) for h in (30, 90, 180)] == [30, 90, 180]

    def test_no_extrapola_mas_alla_de_la_ultima_ancla(self):
        puntos = interpolar(ULTIMA, 80.0, [ancla(date(2026, 10, 15), 60.0)], 90)
        assert len(puntos) == 23 and puntos[-1].fecha == date(2026, 10, 15)

    def test_ignora_anclas_que_ya_pasaron_y_acepta_desorden(self):
        anclas = [ancla(date(2026, 11, 15), 50.0), ancla(date(2026, 8, 15), 99.0), ancla(date(2026, 10, 15), 60.0)]
        por_fecha = {p.fecha: p.valor_esperado for p in interpolar(ULTIMA, 80.0, anclas, 60)}
        assert por_fecha[date(2026, 10, 15)] == pytest.approx(60.0)
        assert por_fecha[date(2026, 11, 15)] == pytest.approx(50.0)

    def test_sin_anclas_futuras_no_hay_proyeccion(self):
        assert interpolar(ULTIMA, 80.0, [], 30) == []
        assert interpolar(ULTIMA, 80.0, [ancla(date(2026, 9, 15), 60.0), ancla(ULTIMA, 60.0)], 30) == []

    def test_acota_entre_0_y_100(self):
        puntos = interpolar(ULTIMA, 95.0, [ancla(date(2026, 10, 15), 100.0, ancho=20.0)], 30)
        assert all(0 <= p.limite_inferior <= p.valor_esperado <= p.limite_superior <= 100 for p in puntos)
        assert puntos[-1].limite_superior == 100.0


class TestCasoDeUsoConProyeccionDeOutputs:
    def setup_method(self):
        self.embalse = crear_embalse("A")
        self.mediciones = [
            crear_medicion(self.embalse, ULTIMA - timedelta(days=i), 80.0, 100.0) for i in range(40)
        ]
        self.forecasting = ForecastingPersistencia()

    def _caso(self, publicada):
        return GenerarPrediccionUseCase(
            EmbalseRepositoryEnMemoria([self.embalse]),
            MedicionRepositoryEnMemoria(self.mediciones),
            self.forecasting,
            ProyeccionSendaRepositoryEnMemoria(publicada),
        )

    def _publicada(self, **kw):
        return crear_proyeccion_publicada("A", inicio=date(2026, 10, 1), base=60.0, **kw)

    def test_usa_la_proyeccion_de_outputs_y_no_el_modelo_estadistico(self):
        pred = self._caso(self._publicada(origen="Prophet + XGBoost (prueba)")).ejecutar("A", 90)
        assert pred.origen == "outputs" and self.forecasting.llamadas == []
        assert pred.metodo == "Prophet + XGBoost (prueba) · interpolación diaria"
        assert pred.nivel_confianza is None  # son escenarios P10/P90, no un IC

    def test_arranca_al_dia_siguiente_del_ultimo_dato(self):
        pred = self._caso(self._publicada()).ejecutar("A", 30)
        assert pred.puntos[0].fecha == ULTIMA + timedelta(days=1) and len(pred.puntos) == 30

    def test_en_las_fechas_mensuales_coincide_con_la_senda(self):
        pred = self._caso(self._publicada()).ejecutar("A", 90)
        por_fecha = {p.fecha: p for p in pred.puntos}
        assert por_fecha[date(2026, 10, 15)].valor_esperado == 60.0
        assert (por_fecha[date(2026, 10, 15)].limite_inferior, por_fecha[date(2026, 10, 15)].limite_superior) == (57.0, 63.0)
        assert por_fecha[date(2026, 11, 15)].valor_esperado == 58.0

    def test_cubre_los_cuatro_horizontes_hasta_donde_llega_lo_publicado(self):
        caso = self._caso(self._publicada(meses=12))
        largos = {h: len(caso.ejecutar("A", h).puntos) for h in (30, 90, 180, 360)}
        # la ultima ancla es el 15-sep-2027: 358 dias despues del ultimo dato
        assert largos == {30: 30, 90: 90, 180: 180, 360: 358}

    def test_el_horizonte_informado_es_el_pedido(self):
        assert self._caso(self._publicada()).ejecutar("A", 360).horizonte_dias == 360

    def test_sin_proyeccion_publicada_usa_el_respaldo_estadistico(self):
        pred = self._caso([]).ejecutar("A", 30)
        assert pred.origen == "holt_winters" and pred.nivel_confianza == 0.95
        assert pred.metodo == "Persistencia de prueba" and len(self.forecasting.llamadas) == 1

    def test_una_proyeccion_ya_vencida_no_se_usa(self):
        vieja = crear_proyeccion_publicada("A", inicio=date(2025, 1, 1))
        assert self._caso(vieja).ejecutar("A", 30).origen == "holt_winters"

    def test_una_proyeccion_de_otro_embalse_no_se_usa(self):
        otra = crear_proyeccion_publicada("OTRO", inicio=date(2026, 10, 1))
        assert self._caso(otra).ejecutar("A", 30).origen == "holt_winters"
