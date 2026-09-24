from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PuntoMensualDTO(BaseModel):
    """Un punto observado de la serie mensual de %V. util."""

    mes: str  # "YYYY-MM"
    pct_volumen_util: float


class PuntoProyeccionMensualDTO(BaseModel):
    """Un punto proyectado de la senda mensual, con intervalo de confianza."""

    mes: str  # "YYYY-MM"
    valor_esperado: float
    limite_inferior: float
    limite_superior: float


class MetricaValidacionDTO(BaseModel):
    """Resultado de validacion walk-forward de un modelo frente al real."""

    modelo: str
    mae: float
    r2: float


class SendaVolumenDTO(BaseModel):
    """Payload del endpoint /senda-volumen: trayectoria mensual observada +
    proyectada de %V. util para un embalse o para el agregado nacional,
    junto con la validacion honesta del modelo frente a una linea base de
    persistencia (walk-forward)."""

    embalse_id: str
    nombre: str
    metodo: str
    generado_en: datetime
    ultimo_observado: PuntoMensualDTO
    minimo_proyectado: PuntoProyeccionMensualDTO
    historico: list[PuntoMensualDTO]
    proyeccion: list[PuntoProyeccionMensualDTO]
    validacion: list[MetricaValidacionDTO]
