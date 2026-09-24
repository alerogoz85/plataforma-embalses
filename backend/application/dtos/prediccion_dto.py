from __future__ import annotations

from datetime import date, datetime
from typing import Optional

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
    # Solo el respaldo estadistico tiene intervalo de confianza; la proyeccion de
    # Outputs trae escenarios P10/P90 y no lo tiene (null).
    nivel_confianza: Optional[float]
    generado_en: datetime
    metodo: str
    puntos: list[PrediccionPuntoDTO]
    # "outputs": proyeccion del modelo de largo plazo interpolada a diario;
    # "holt_winters": respaldo estadistico.
    origen: str = "holt_winters"
