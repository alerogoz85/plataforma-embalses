"""DTOs de los endpoints del modelo de carbon termico (/api/v1/carbon/*).

Unidades: consumo en GBTU/dia, inventario y consumo mensual en kt, aportes y uso del
techo en porcentaje (0-100). Las bandas son escenarios P10/P50/P90, no intervalos de
confianza."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


class BandaDTO(BaseModel):
    p10: float
    p50: float
    p90: float


# ------------------------------------------------------------------ /carbon/resumen
class PuntoCarbonDTO(BaseModel):
    fecha: date
    carbon_gbtu_dia: float
    mes_completo: bool = True
    fuente: Optional[str] = None


class PicoCarbonDTO(BaseModel):
    """Mes de mayor consumo esperado (P50) dentro del horizonte."""

    fecha: date
    carbon_gbtu_dia: BandaDTO
    uso_techo_p50_pct: float
    prob_supera_maximo_pct: float


class InventarioPicoDTO(BaseModel):
    fecha: date
    dias_inventario: int
    kt_p50: float
    kt_p90: float


class TrimestreDTO(BaseModel):
    trimestre: str
    meses: int
    carbon_mt: BandaDTO
    dentro_del_horizonte: bool  # todos sus meses caen en el horizonte elegido


class ResumenCarbonDTO(BaseModel):
    origen: str
    poder_calorifico_mbtu_t: float
    techo_gbtu_dia: float
    maximo_historico: PuntoCarbonDTO
    ultimo_observado: PuntoCarbonDTO
    horizonte_meses: int  # el efectivo: el modelo proyecta como maximo 9
    pico: PicoCarbonDTO
    inventario_pico: Optional[InventarioPicoDTO] = None
    trimestres: list[TrimestreDTO]
    criterios_cumplidos: int
    criterios_total: int


# ------------------------------------------------------------------ /carbon/serie
class HistoricoCarbonDTO(BaseModel):
    fecha: date
    carbon_gbtu_dia: float
    techo_gbtu_dia: Optional[float] = None
    uso_techo_pct: Optional[float] = None
    aportes_pct_media: Optional[float] = None
    roni: Optional[float] = None
    fuente: str
    mes_completo: bool


class ProyeccionCarbonDTO(BaseModel):
    fecha: date
    dias: int
    roni: BandaDTO
    aportes_pct_media: BandaDTO
    uso_techo_pct: BandaDTO
    carbon_gbtu_dia: BandaDTO
    carbon_kt_mes: BandaDTO
    prob_supera_maximo_pct: float
    observado_parcial_gbtu_dia: Optional[float] = None


class SerieCarbonDTO(BaseModel):
    techo_gbtu_dia: float
    maximo_historico_gbtu_dia: float
    poder_calorifico_mbtu_t: float
    horizonte_meses: int
    historico: list[HistoricoCarbonDTO]
    proyeccion: list[ProyeccionCarbonDTO]


# ------------------------------------------------------------------ /carbon/inventario
class InventarioMensualDTO(BaseModel):
    fecha: date
    dias_inventario: int
    kt_p50: float
    kt_p90: float


# ------------------------------------------------------------------ /carbon/comparacion-xm
class ComparacionXmDTO(BaseModel):
    fecha: date
    modelo: BandaDTO
    techo_gbtu_dia: float
    xm_estocastico_gbtu_dia: Optional[float] = None
    xm_historicas_min_gbtu_dia: Optional[float] = None
    xm_historicas_max_gbtu_dia: Optional[float] = None


# ------------------------------------------------------------------ /carbon/validacion
class ErrorHorizonteDTO(BaseModel):
    horizonte_meses: int
    pronosticos: int
    mae_modelo: float
    mae_persistencia: float
    mae_estacional: float
    mae_climatologia: float
    sesgo_modelo: float


class EpisodioDTO(BaseModel):
    episodio: str
    inicio: date
    fin: date
    meses: int
    real_gbtu_dia: float
    p50_gbtu_dia: float
    error_total_pct: float
    mae_modelo: float
    mae_ingenuo: float
    cobertura_p10_p90_pct: float


class CriterioDTO(BaseModel):
    criterio: str
    resultado: str
    cumple: bool
    interpretacion: str


class SupuestoDTO(BaseModel):
    nombre: str
    valor: str


class ValidacionCarbonDTO(BaseModel):
    errores_horizonte: list[ErrorHorizonteDTO]
    episodios: list[EpisodioDTO]
    criterios_cumplidos: int
    criterios_total: int
    veredicto: list[CriterioDTO]
    supuestos: list[SupuestoDTO]
