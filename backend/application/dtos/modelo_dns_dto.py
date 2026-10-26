"""DTOs de los endpoints del modelo de demanda no atendida (/api/v1/dns/*).

Unidades: energia en GWh, porcentajes 0-100, conteos de eventos. Las variaciones son frente a la
ventana anterior de igual duracion (None cuando el periodo es «todo el historico» o no hay base)."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


# ------------------------------------------------------------------ /dns/catalogo
class SubareaDTO(BaseModel):
    codigo: str
    nombre: str
    region: str
    departamentos: Optional[str] = None


class CatalogoDnsDTO(BaseModel):
    origen: str
    fecha_inicio: date
    fecha_corte: date
    mes_corte_parcial: bool
    regiones: list[str]
    subareas: list[SubareaDTO]
    periodo_pronostico: str


# ------------------------------------------------------------------ /dns/resumen
class ResumenDnsDTO(BaseModel):
    periodo_meses: int
    desde: str  # AAAA-MM
    hasta: str
    eventos: int
    energia_gwh: float
    pct_criticos: float
    pct_no_programados: Optional[float]
    variacion_eventos_pct: Optional[float]
    variacion_energia_pct: Optional[float]
    causa_mas_frecuente: Optional[str]
    causa_mas_frecuente_eventos: int
    eventos_edac: int


# ------------------------------------------------------------------ /dns/serie
class MesDnsDTO(BaseModel):
    mes: str
    eventos: int
    energia_gwh: float
    eventos_no_programados: int
    parcial: bool


class PronosticoMesDTO(BaseModel):
    mes: str
    eventos: float
    energia_gwh: float
    subareas: int  # cuantas subareas del filtro tienen pronostico


class SerieDnsDTO(BaseModel):
    meses: list[MesDnsDTO]
    pronostico: Optional[PronosticoMesDTO]
    nota_pronostico: Optional[str]  # por que no hay pronostico, si no lo hay


# ------------------------------------------------------------------ /dns/zonas
class ZonaDTO(BaseModel):
    ranking: int
    codigo: str
    nombre: str
    region: str
    indice_priorizacion: float
    energia_total_gwh: float
    n_eventos: int
    pct_criticos: float
    variacion_pct: float


class ZonasDnsDTO(BaseModel):
    zonas: list[ZonaDTO]


# ------------------------------------------------------------------ /dns/patrones
class FranjaDTO(BaseModel):
    franja: str
    no_programada: int
    programada: int
    pct_no_programada: Optional[float]


class PatronesDnsDTO(BaseModel):
    por_hora: list[int]
    dias: list[str]
    por_dia_semana: list[int]
    franjas: list[FranjaDTO]
    eventos_usados: int
    eventos_hora_desconocida: int


# ------------------------------------------------------------------ /dns/causas
class CausaDTO(BaseModel):
    causa: str
    eventos: int
    energia_gwh: float
    pct_eventos: float


class ConteoDTO(BaseModel):
    nombre: str
    eventos: int


class CausasDnsDTO(BaseModel):
    total: int
    causas: list[CausaDTO]
    origen_de_la_causa: list[ConteoDTO]
    tipos_evento: list[ConteoDTO]
    niveles_red: list[ConteoDTO]


# ------------------------------------------------------------------ /dns/cambios-reporte
class CambioReporteDTO(BaseModel):
    codigo: str
    nombre: str
    region: str
    periodo_quiebre: str
    direccion: str
    pct_generica_antes: float
    pct_generica_despues: float
    pct_causa_conocida_antes: float
    pct_causa_conocida_despues: float


class CambiosReporteDTO(BaseModel):
    cambios: list[CambioReporteDTO]


# ------------------------------------------------------------------ /dns/modelo
class MetricaDTO(BaseModel):
    modelo: str
    variable: str  # n_eventos o energia_kwh
    mae: float
    rmse: float
    mejora_vs_persistencia_pct: Optional[float]  # None en la propia persistencia


class ImportanciaDTO(BaseModel):
    variable: str
    importancia_n_eventos: float
    importancia_energia_kwh: float


class PronosticoSubareaDTO(BaseModel):
    codigo: str
    nombre: str
    region: str
    n_eventos: float
    energia_gwh: float


class ModeloDnsDTO(BaseModel):
    periodo_pronostico: str
    metricas: list[MetricaDTO]
    importancia: list[ImportanciaDTO]
    pronostico: list[PronosticoSubareaDTO]
