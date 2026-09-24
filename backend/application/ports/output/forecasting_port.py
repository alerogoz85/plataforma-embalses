from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class PuntoForecast:
    fecha: date
    valor_esperado: float
    limite_inferior: float
    limite_superior: float


class ForecastingPort(ABC):
    """Puerto de salida: contrato que debe cumplir cualquier motor de
    pronostico de series de tiempo (Holt-Winters, Prophet, XGBoost, ...).

    La aplicacion depende solo de esta abstraccion; el modelo concreto vive
    en infrastructure/ml/.
    """

    @abstractmethod
    def nombre_metodo(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def proyectar(
        self,
        serie_historica: list[float],
        fechas_historicas: list[date],
        horizonte_periodos: int,
        nivel_confianza: float = 0.95,
        paso_dias: int = 1,
    ) -> list[PuntoForecast]:
        """Proyecta `horizonte_periodos` puntos futuros, cada uno separado
        `paso_dias` dias del anterior (1 para series diarias, ~30 para
        aproximar series mensuales)."""
        raise NotImplementedError
