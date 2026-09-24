from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class PrediccionPuntoDTO(BaseModel):
    """Un punto proyectado del pronostico de %V_util con intervalo de confianza."""

    fecha: date
    valor_esperado: float
    limite_inferior: float
    limite_superior: float


class PrediccionDTO(BaseModel):
    """Payload del endpoint /embalses/{id}/prediccion."""

    embalse_id: str
    horizonte_dias: int
    nivel_confianza: float
    generado_en: datetime
    metodo: str
    puntos: list[PrediccionPuntoDTO]
