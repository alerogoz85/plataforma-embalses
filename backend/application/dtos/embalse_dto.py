from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class EmbalseResumenDTO(BaseModel):
    """Vista resumida de un embalse para tablas y tarjetas del dashboard.

    Los campos opcionales son None cuando XM/SIMEM no publica el dato para
    ese embalse (por ejemplo, aportes de Muna)."""

    id: str
    nombre: str
    region: str
    es_agregado: bool
    fecha: date
    pct_volumen_util: float
    nivel_riesgo: str
    volumen_util_mm3: float
    capacidad_util_mm3: float
    energia_util_gwh: Optional[float] = None
    aportes_m3s: Optional[float] = None
    aportes_pct_media: Optional[float] = None
    vertimientos_m3s: Optional[float] = None
    turbinado_m3s: Optional[float] = None
    dias_autonomia: Optional[int] = None
    delta_diario_pct: float = 0.0
    delta_semanal_pct: float = 0.0


class RegionResumenDTO(BaseModel):
    """Agregado por region hidrologica."""

    region: str
    pct_volumen_util: float
    aportes_pct_media: Optional[float] = None
    nivel_riesgo: str
    num_embalses: int
    energia_util_gwh: float


class KPINacionalDTO(BaseModel):
    """Indicadores clave agregados a nivel nacional, para el header del dashboard."""

    fecha_corte: date
    pct_volumen_util_nacional: float
    delta_diario_pct: float
    delta_semanal_pct: float
    aportes_pct_media_nacional: Optional[float] = None
    capacidad_guardada_gwh: float
    nivel_riesgo_sistema: str
    total_embalses: int


class ResumenNacionalDTO(BaseModel):
    """Payload completo del endpoint /embalses/resumen."""

    kpis: KPINacionalDTO
    regiones: list[RegionResumenDTO]
    embalses: list[EmbalseResumenDTO]


class SeriePuntoDTO(BaseModel):
    """Un punto de la serie historica multi-variable de un embalse."""

    fecha: date
    pct_volumen_util: float
    energia_util_gwh: Optional[float] = None
    aportes_m3s: Optional[float] = None
    aportes_pct_media: Optional[float] = None
    vertimientos_m3s: Optional[float] = None
    turbinado_m3s: Optional[float] = None


class EmbalseDetalleDTO(BaseModel):
    """Detalle de un embalse: resumen mas reciente + serie historica."""

    resumen: EmbalseResumenDTO
    serie_historica: list[SeriePuntoDTO] = Field(default_factory=list)
