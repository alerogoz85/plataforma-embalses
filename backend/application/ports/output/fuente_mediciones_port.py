from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica


@dataclass(frozen=True, slots=True)
class DescargaMediciones:
    embalses: list[Embalse]
    mediciones: list[MedicionHidrologica]
    fuente: str
    descripcion: str
    es_real: bool


class FuenteMedicionesPort(ABC):
    """Puerto de salida: origen externo de embalses y mediciones diarias
    (API de SIMEM/XM, generador sintetico, archivos, ...)."""

    @abstractmethod
    def descargar(self, desde: date, hasta: date) -> DescargaMediciones:
        raise NotImplementedError
