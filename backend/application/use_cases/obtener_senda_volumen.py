from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Optional

from application.dtos.senda_volumen_dto import (
    MetricaValidacionDTO,
    PuntoMensualDTO,
    PuntoProyeccionMensualDTO,
    SendaVolumenDTO,
)
from application.ports.input.use_case_ports import ObtenerSendaVolumenPort
from application.ports.output.forecasting_port import ForecastingPort
from domain.exceptions import (
    DatosHistoricosInsuficientesError,
    EmbalseNoEncontradoError,
    SinMedicionesError,
)
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.repositories.proyeccion_senda_repository import ProyeccionSendaRepository
from domain.services.calculo_hidrico_service import CalculoHidricoService

ID_TOTAL_NACIONAL = "TOTAL"
PASO_DIAS_MENSUAL = 30
MESES_VALIDACION = 6
MINIMO_MESES_HISTORICO = 9
NIVEL_CONFIANZA = 0.95
ORIGEN_OUTPUTS = "outputs"
ORIGEN_HOLT_WINTERS = "holt_winters"


class ObtenerSendaVolumenUseCase(ObtenerSendaVolumenPort):
    """Construye la senda mensual observada + proyectada de %V. util de un
    embalse (o del agregado nacional ponderado 'TOTAL').

    La proyeccion es la del modelo de largo plazo (Outputs: Prophet + XGBoost
    con escenarios ENSO) cuando hay una publicada para el embalse. Sin ella
    (p. ej. Agregado Bogota) se usa un respaldo estadistico, Holt-Winters, junto
    con una validacion walk-forward que lo compara contra la persistencia.
    """

    def __init__(
        self,
        embalse_repository: EmbalseRepository,
        medicion_repository: MedicionRepository,
        forecasting_service: ForecastingPort,
        proyeccion_repository: Optional[ProyeccionSendaRepository] = None,
    ) -> None:
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository
        self._forecasting = forecasting_service
        self._proyecciones = proyeccion_repository
        self._calculo = CalculoHidricoService()

    def ejecutar(
        self, embalse_id: str = ID_TOTAL_NACIONAL, horizonte_meses: int = 12
    ) -> SendaVolumenDTO:
        if embalse_id == ID_TOTAL_NACIONAL:
            nombre = "Total nacional"
            serie_diaria = self._serie_diaria_nacional()
        else:
            embalse = self._embalses_repo.obtener_por_id(embalse_id)
            if embalse is None:
                raise EmbalseNoEncontradoError(embalse_id)
            mediciones = self._mediciones_repo.obtener_serie(embalse_id)
            if not mediciones:
                raise SinMedicionesError(embalse_id)
            nombre = embalse.nombre
            serie_diaria = [
                (m.fecha, self._calculo.calcular_porcentaje_volumen_util(m).valor)
                for m in mediciones
            ]

        historico_mensual = self._calculo.agregar_pct_mensual(serie_diaria)
        if len(historico_mensual) < MINIMO_MESES_HISTORICO:
            raise DatosHistoricosInsuficientesError(
                embalse_id, MINIMO_MESES_HISTORICO, len(historico_mensual)
            )

        fechas_mensuales = [fecha for fecha, _ in historico_mensual]
        valores_mensuales = [valor for _, valor in historico_mensual]

        publicada = self._proyecciones.obtener(embalse_id) if self._proyecciones else []
        if publicada:
            proyeccion = [
                PuntoProyeccionMensualDTO(
                    mes=p.mes.strftime("%Y-%m"),
                    valor_esperado=round(p.valor_esperado, 2),
                    limite_inferior=round(p.limite_inferior, 2),
                    limite_superior=round(p.limite_superior, 2),
                )
                for p in publicada[:horizonte_meses]
            ]
            metodo = publicada[0].origen
            origen_proyeccion = ORIGEN_OUTPUTS
            validacion: list[MetricaValidacionDTO] = []
        else:
            puntos_forecast = self._forecasting.proyectar(
                serie_historica=valores_mensuales,
                fechas_historicas=fechas_mensuales,
                horizonte_periodos=horizonte_meses,
                nivel_confianza=NIVEL_CONFIANZA,
                paso_dias=PASO_DIAS_MENSUAL,
            )
            proyeccion = [
                PuntoProyeccionMensualDTO(
                    mes=p.fecha.strftime("%Y-%m"),
                    valor_esperado=round(p.valor_esperado, 2),
                    limite_inferior=round(p.limite_inferior, 2),
                    limite_superior=round(p.limite_superior, 2),
                )
                for p in puntos_forecast
            ]
            metodo = self._forecasting.nombre_metodo()
            origen_proyeccion = ORIGEN_HOLT_WINTERS
            validacion = self._validar_walk_forward(valores_mensuales, fechas_mensuales)
        minimo_proyectado = min(proyeccion, key=lambda p: p.valor_esperado)

        ultima_fecha, ultimo_valor = historico_mensual[-1]
        ultimo_observado = PuntoMensualDTO(
            mes=ultima_fecha.strftime("%Y-%m"), pct_volumen_util=ultimo_valor
        )
        historico = [
            PuntoMensualDTO(mes=fecha.strftime("%Y-%m"), pct_volumen_util=valor)
            for fecha, valor in historico_mensual
        ]

        return SendaVolumenDTO(
            embalse_id=embalse_id,
            nombre=nombre,
            metodo=metodo,
            generado_en=datetime.now(timezone.utc),
            ultimo_observado=ultimo_observado,
            minimo_proyectado=minimo_proyectado,
            historico=historico,
            proyeccion=proyeccion,
            validacion=validacion,
            origen_proyeccion=origen_proyeccion,
            horizonte_efectivo_meses=len(proyeccion),
        )

    def _serie_diaria_nacional(self) -> list[tuple[date, float]]:
        """%V_util nacional diario: promedio ponderado por la capacidad util
        en energia de cada embalse ese dia (metodo de XM)."""
        por_fecha: dict[date, list[tuple[float, float]]] = defaultdict(list)
        for embalse in self._embalses_repo.listar():
            for medicion in self._mediciones_repo.obtener_serie(embalse.id):
                pct = self._calculo.calcular_porcentaje_volumen_util(medicion).valor
                peso = self._calculo.calcular_peso_energetico_agregacion(medicion)
                por_fecha[medicion.fecha].append((pct, peso))

        serie = []
        for fecha in sorted(por_fecha):
            valores_pesos = por_fecha[fecha]
            peso_total = sum(peso for _, peso in valores_pesos) or 1.0
            pct_ponderado = sum(pct * peso for pct, peso in valores_pesos) / peso_total
            serie.append((fecha, round(pct_ponderado, 2)))
        return serie

    def _validar_walk_forward(
        self, valores: list[float], fechas: list[date]
    ) -> list[MetricaValidacionDTO]:
        """Para cada uno de los ultimos MESES_VALIDACION meses, entrena solo
        con los datos anteriores a ese mes y compara la prediccion a 1 paso
        del modelo contra la linea base de persistencia (repetir el ultimo
        valor observado). Es el mismo principio de honestidad que un backtest
        walk-forward: nunca se usa informacion futura para predecir el pasado.
        """
        total_meses = len(valores)
        meses_entrenamiento_minimo = max(3, MINIMO_MESES_HISTORICO - MESES_VALIDACION)
        k = min(MESES_VALIDACION, total_meses - meses_entrenamiento_minimo)
        if k <= 0:
            return []

        reales: list[float] = []
        predicciones_persistencia: list[float] = []
        predicciones_modelo: list[float] = []

        for i in range(total_meses - k, total_meses):
            entrenamiento_valores = valores[:i]
            entrenamiento_fechas = fechas[:i]
            reales.append(valores[i])
            predicciones_persistencia.append(entrenamiento_valores[-1])

            punto = self._forecasting.proyectar(
                serie_historica=entrenamiento_valores,
                fechas_historicas=entrenamiento_fechas,
                horizonte_periodos=1,
                nivel_confianza=NIVEL_CONFIANZA,
                paso_dias=PASO_DIAS_MENSUAL,
            )[0]
            predicciones_modelo.append(punto.valor_esperado)

        return [
            self._calcular_metrica("Persistencia (ultimo valor)", reales, predicciones_persistencia),
            self._calcular_metrica(self._forecasting.nombre_metodo(), reales, predicciones_modelo),
        ]

    @staticmethod
    def _calcular_metrica(
        modelo: str, reales: list[float], predicciones: list[float]
    ) -> MetricaValidacionDTO:
        n = len(reales)
        mae = sum(abs(r - p) for r, p in zip(reales, predicciones)) / n

        media_real = sum(reales) / n
        suma_total = sum((r - media_real) ** 2 for r in reales)
        suma_residual = sum((r - p) ** 2 for r, p in zip(reales, predicciones))
        r2 = 1 - (suma_residual / suma_total) if suma_total > 0 else 0.0

        return MetricaValidacionDTO(modelo=modelo, mae=round(mae, 3), r2=round(r2, 3))
