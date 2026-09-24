from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NivelRiesgo(str, Enum):
    OPTIMO = "OPTIMO"
    ALERTA = "ALERTA"
    CRITICO = "CRITICO"
    REBOCE = "REBOCE"


UMBRAL_CRITICO = 15.0
UMBRAL_ALERTA = 30.0
UMBRAL_REBOCE = 95.0


@dataclass(frozen=True, slots=True)
class Porcentaje:
    """Porcentaje con clasificacion semantica de riesgo.

    No se acota por arriba: XM publica valores por encima de 100% cuando un
    embalse supera su capacidad util nominal, y se muestran tal cual.
    """

    valor: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "valor", round(max(0.0, self.valor), 2))

    @property
    def nivel_riesgo(self) -> NivelRiesgo:
        if self.valor >= UMBRAL_REBOCE:
            return NivelRiesgo.REBOCE
        if self.valor < UMBRAL_CRITICO:
            return NivelRiesgo.CRITICO
        if self.valor < UMBRAL_ALERTA:
            return NivelRiesgo.ALERTA
        return NivelRiesgo.OPTIMO

    def __str__(self) -> str:
        return f"{self.valor:.2f}%"
