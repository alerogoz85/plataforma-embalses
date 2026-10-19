"""Entidades del modelo de consumo de carbon termico para generacion electrica.

Son el resultado ya calculado del modelo (proyeccion Monte Carlo del consumo de
carbon del SIN, su validacion y su comparacion con la proyeccion de XM). La
plataforma no recalcula el modelo: lo muestra. Unidades:

* consumo de carbon: GBTU/dia (mil millones de BTU por dia), kt/mes (miles de toneladas)
* aportes y uso del techo fisico: porcentaje (0-100)
* RONI: indice oceanico relativo (puntos)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from domain.value_objects.banda import Banda


@dataclass(frozen=True, slots=True)
class HistoricoCarbonMensual:
    """Consumo de carbon de un mes ya ocurrido (oficial de Sinergox o estimado)."""

    fecha: date  # primer dia del mes
    carbon_gbtu_dia: float
    techo_gbtu_dia: Optional[float]  # consumo con el parque a carbon a plena capacidad
    uso_techo_pct: Optional[float]
    aportes_pct_media: Optional[float]
    roni: Optional[float]
    fuente: str  # "Sinergox", "Estimado" o "Sinergox + estimado"
    mes_completo: bool  # False si es el mes en curso (promedio parcial)
    dias_con_dato: int


@dataclass(frozen=True, slots=True)
class ProyeccionCarbonMensual:
    """Proyeccion de un mes futuro: clima, hidrologia y consumo de carbon."""

    fecha: date
    dias: int
    techo_gbtu_dia: float
    roni: Banda
    aportes_pct_media: Banda
    uso_techo_pct: Banda
    carbon_gbtu_dia: Banda
    carbon_kt_mes: Banda
    prob_supera_maximo_pct: float  # probabilidad de superar el maximo mensual historico
    observado_parcial_gbtu_dia: Optional[float]  # promedio de lo ya ocurrido del mes en curso


@dataclass(frozen=True, slots=True)
class TrimestreCarbon:
    """Consumo total de un trimestre (se calcula simulacion por simulacion)."""

    trimestre: str  # "2026Q4"
    meses: int
    carbon_mt: Banda  # millones de toneladas


@dataclass(frozen=True, slots=True)
class InventarioCarbon:
    """Inventario de carbon que cubre `dias_inventario` de consumo en un mes."""

    fecha: date
    dias_inventario: int
    kt_p50: float
    kt_p90: float


@dataclass(frozen=True, slots=True)
class ComparacionXM:
    """Proyeccion del modelo frente a la publicada por XM (conjunto 0837f0)."""

    fecha: date
    modelo: Banda
    techo_gbtu_dia: float
    xm_estocastico_gbtu_dia: Optional[float]
    xm_historicas_min_gbtu_dia: Optional[float]  # casos de hidrologias historicas de XM
    xm_historicas_max_gbtu_dia: Optional[float]


@dataclass(frozen=True, slots=True)
class ErrorPorHorizonte:
    """Error absoluto medio fuera de muestra a un horizonte, contra referencias ingenuas."""

    horizonte_meses: int
    pronosticos: int
    mae_modelo: float
    mae_persistencia: float
    mae_estacional: float
    mae_climatologia: float
    sesgo_modelo: float


@dataclass(frozen=True, slots=True)
class EpisodioValidacion:
    """Prueba del modelo sobre un episodio de El Nino reestimando sin sus meses."""

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


@dataclass(frozen=True, slots=True)
class CriterioValidez:
    """Un criterio de validez estadistica del veredicto del modelo."""

    criterio: str
    resultado: str
    cumple: bool
    interpretacion: str


@dataclass(frozen=True, slots=True)
class SupuestoCarbon:
    nombre: str
    valor: str


@dataclass(frozen=True, slots=True)
class PaqueteModeloCarbon:
    """Todo lo que publica una corrida del modelo. Se carga y se reemplaza completo."""

    origen: str  # descripcion de la corrida (modelo, version, fecha)
    poder_calorifico_mbtu_t: float  # conversion de energia a toneladas
    historico: list[HistoricoCarbonMensual]
    proyeccion: list[ProyeccionCarbonMensual]
    trimestres: list[TrimestreCarbon] = field(default_factory=list)
    inventario: list[InventarioCarbon] = field(default_factory=list)
    comparacion_xm: list[ComparacionXM] = field(default_factory=list)
    errores_horizonte: list[ErrorPorHorizonte] = field(default_factory=list)
    episodios: list[EpisodioValidacion] = field(default_factory=list)
    veredicto: list[CriterioValidez] = field(default_factory=list)
    supuestos: list[SupuestoCarbon] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.historico or not self.proyeccion:
            raise ValueError("El modelo de carbon necesita historico y proyeccion")
        if self.poder_calorifico_mbtu_t <= 0:
            raise ValueError("El poder calorifico debe ser positivo")
        for nombre, claves in (
            ("historico", [h.fecha for h in self.historico]),
            ("proyeccion", [m.fecha for m in self.proyeccion]),
            ("trimestres", [x.trimestre for x in self.trimestres]),
            ("inventario", [(i.fecha, i.dias_inventario) for i in self.inventario]),
            ("comparacion_xm", [c.fecha for c in self.comparacion_xm]),
            ("errores_horizonte", [e.horizonte_meses for e in self.errores_horizonte]),
            ("episodios", [e.episodio for e in self.episodios]),
        ):
            if len(set(claves)) != len(claves):
                raise ValueError(f"El modelo de carbon tiene claves repetidas en '{nombre}'")

    @property
    def maximo_mensual_historico(self) -> HistoricoCarbonMensual:
        """Mes completo con el mayor consumo observado (el 'record' mensual)."""
        return max((h for h in self.historico if h.mes_completo), key=lambda h: h.carbon_gbtu_dia)
