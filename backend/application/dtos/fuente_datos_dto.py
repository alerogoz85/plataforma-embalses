from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class FuenteDatosDTO(BaseModel):
    """Procedencia de los datos que muestra la plataforma."""

    fuente: str
    descripcion: str
    es_real: bool
    fecha_corte: Optional[date] = None
    actualizado_en: Optional[datetime] = None
