from __future__ import annotations

from datetime import date, timedelta

import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from application.ports.output.forecasting_port import ForecastingPort, PuntoForecast

VALOR_MINIMO_PCT = 0.0
VALOR_MAXIMO_PCT = 100.0
SIMULACIONES_MONTE_CARLO = 300


class HoltWintersForecastingService(ForecastingPort):
    """Adaptador de infraestructura que implementa el pronostico de series
    de tiempo con suavizamiento exponencial de Holt-Winters. Los intervalos
    de confianza se estiman por simulacion Monte Carlo de trayectorias
    futuras, que es el enfoque nativo de statsmodels para este modelo (no
    produce intervalos cerrados).

    Con `estacional=True` agrega un componente estacional aditivo (periodo
    `periodos_estacionales`, 12 para series mensuales) para que la
    proyeccion reproduzca el ciclo hidrologico anual (temporada seca/lluvias)
    en vez de solo extrapolar una tendencia. Requiere al menos dos ciclos
    completos de historia; si no los hay, cae automaticamente al modelo sin
    estacionalidad.
    """

    def __init__(self, estacional: bool = False, periodos_estacionales: int = 12) -> None:
        self._estacional = estacional
        self._periodos_estacionales = periodos_estacionales

    def nombre_metodo(self) -> str:
        if self._estacional:
            return (
                f"Holt-Winters estacional ({self._periodos_estacionales} periodos, "
                "tendencia amortiguada, IC via simulacion Monte Carlo)"
            )
        return "Holt-Winters (tendencia amortiguada, IC via simulacion Monte Carlo)"

    def proyectar(
        self,
        serie_historica: list[float],
        fechas_historicas: list[date],
        horizonte_periodos: int,
        nivel_confianza: float = 0.95,
        paso_dias: int = 1,
    ) -> list[PuntoForecast]:
        valores = np.asarray(serie_historica, dtype=float)
        usar_estacionalidad = (
            self._estacional and len(valores) >= 2 * self._periodos_estacionales
        )

        modelo = ExponentialSmoothing(
            valores,
            trend="add",
            damped_trend=True,
            seasonal="add" if usar_estacionalidad else None,
            seasonal_periods=self._periodos_estacionales if usar_estacionalidad else None,
            initialization_method="estimated",
        )
        resultado = modelo.fit(optimized=True)

        trayectorias = resultado.simulate(
            nsimulations=horizonte_periodos,
            repetitions=SIMULACIONES_MONTE_CARLO,
            error="add",
            random_state=42,
        )
        # trayectorias: matriz (horizonte_periodos x repeticiones)
        pronostico_medio = resultado.forecast(horizonte_periodos)

        cola = (1 - nivel_confianza) / 2
        limite_inferior = np.quantile(trayectorias, cola, axis=1)
        limite_superior = np.quantile(trayectorias, 1 - cola, axis=1)

        ultima_fecha = fechas_historicas[-1]
        puntos = []
        for i in range(horizonte_periodos):
            fecha_proyectada = ultima_fecha + timedelta(days=paso_dias * (i + 1))
            puntos.append(
                PuntoForecast(
                    fecha=fecha_proyectada,
                    valor_esperado=self._acotar(pronostico_medio[i]),
                    limite_inferior=self._acotar(limite_inferior[i]),
                    limite_superior=self._acotar(limite_superior[i]),
                )
            )
        return puntos

    @staticmethod
    def _acotar(valor: float) -> float:
        return float(max(VALOR_MINIMO_PCT, min(VALOR_MAXIMO_PCT, valor)))
