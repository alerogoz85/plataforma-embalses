from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NombreRegion(str, Enum):
    ANTIOQUIA = "Antioquia"
    CALDAS = "Caldas"
    CARIBE = "Caribe"
    CENTRO = "Centro"
    ORIENTE = "Oriente"
    VALLE = "Valle"


@dataclass(frozen=True, slots=True)
class Region:
    """Region hidrologica a la que XM asigna un embalse."""

    nombre: NombreRegion

    def __str__(self) -> str:
        return self.nombre.value
