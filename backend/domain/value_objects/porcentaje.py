from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NivelRiesgo(str, Enum):
    NORMAL = "NORMAL"
    ESTABLE = "ESTABLE"
    ALERTA_TEMPRANA = "ALERTA_TEMPRANA"
    SITUACION_DELICADA = "SITUACION_DELICADA"
    CRITICO = "CRITICO"


# Clasificacion del %V. util (misma para embalses, regiones y sistema):
#   Normal              > 80 %
#   Estable             70 % a 80 %  (80 incluido)
#   Alerta temprana     60 % a < 70 %
#   Situacion delicada  50 % a < 60 %
#   Critico             < 50 %
UMBRAL_NORMAL = 80.0
UMBRAL_ESTABLE = 70.0
UMBRAL_ALERTA_TEMPRANA = 60.0
UMBRAL_SITUACION_DELICADA = 50.0


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
        if self.valor > UMBRAL_NORMAL:
            return NivelRiesgo.NORMAL
        if self.valor >= UMBRAL_ESTABLE:
            return NivelRiesgo.ESTABLE
        if self.valor >= UMBRAL_ALERTA_TEMPRANA:
            return NivelRiesgo.ALERTA_TEMPRANA
        if self.valor >= UMBRAL_SITUACION_DELICADA:
            return NivelRiesgo.SITUACION_DELICADA
        return NivelRiesgo.CRITICO

    def __str__(self) -> str:
        return f"{self.valor:.2f}%"
