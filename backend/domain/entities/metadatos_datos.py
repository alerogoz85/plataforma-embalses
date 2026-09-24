from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class MetadatosDatos:
    """Procedencia de los datos cargados: de donde vienen y hasta cuando."""

    fuente: str
    descripcion: str
    fecha_corte: date
    actualizado_en: datetime
    es_real: bool
