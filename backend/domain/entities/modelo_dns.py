"""Entidades del modelo de Demanda No Atendida (DNS).

DNS es la energia que el sistema deja de suministrar durante un evento (en kWh). El modelo
analiza los eventos DNS y EDAC reportados a SIMEM por subarea operativa: prioriza zonas,
detecta cambios en la forma de reportar, describe cuando y por que ocurren y pronostica el mes
siguiente. Estas entidades son la corrida vigente; no dependen de ninguna base de datos."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

REGION_SIN_ASIGNAR = "Sin asignar"
TIPO_DNS = "DNS"
TIPO_EDAC = "EDAC"
ORIGEN_PROGRAMADA = "programada"
ORIGEN_NO_PROGRAMADA = "no_programada"
# Un evento es critico si deja sin atender 100.000 kWh (100 MWh) o mas: es el umbral del modelo.
UMBRAL_CRITICO_KWH = 100_000.0
CAUSA_DESCONOCIDA = "desconocido"


@dataclass(frozen=True)
class SubareaDns:
    codigo: str
    nombre: str
    region: str
    departamentos: Optional[str] = None


@dataclass(frozen=True)
class EventoDns:
    """Un evento reportado. `tipo` es DNS o EDAC; `origen_evento` solo existe para los DNS.

    OJO: en los EDAC (esquema de desconexion automatica de carga) el valor de
    `energia_no_atendida_kwh` es la carga desconectada, no kWh de DNS: nunca se suma con la de los DNS."""

    fecha_hora: datetime
    codigo_subarea: str
    tipo: str
    energia_no_atendida_kwh: float
    origen_evento: Optional[str]
    causa_definitiva: str
    origen_causa_definitiva: str
    tipo_evento: str
    nivel_red: str

    @property
    def es_critico(self) -> bool:
        return self.energia_no_atendida_kwh >= UMBRAL_CRITICO_KWH

    @property
    def hora_desconocida(self) -> bool:
        """SIMEM guarda 00:00:00 exacto cuando no se capturo la hora real: no es un pico de medianoche."""
        f = self.fecha_hora
        return f.hour == 0 and f.minute == 0 and f.second == 0


@dataclass(frozen=True)
class ZonaPriorizada:
    """Fila del indice de priorizacion (0-100) calculado por el modelo sobre todo el historico."""

    ranking: int
    codigo_subarea: str
    indice_priorizacion: float
    energia_total_kwh: float
    n_eventos: int
    pct_criticos: float  # fraccion 0-1 tal como la entrega el modelo
    variacion_pct: float  # ultimos 24 meses frente a los 24 anteriores


@dataclass(frozen=True)
class CambioReporte:
    """Subarea cuya forma de reportar cambio (mas descripciones genericas y menos causa conocida)."""

    codigo_subarea: str
    periodo_quiebre: str  # AAAA-MM
    direccion: str
    pct_generica_antes: float
    pct_generica_despues: float
    pct_causa_conocida_antes: float
    pct_causa_conocida_despues: float


@dataclass(frozen=True)
class MetricaModelo:
    modelo: str  # p. ej. "n_eventos - GradientBoosting"
    mae: float
    rmse: float


@dataclass(frozen=True)
class ImportanciaVariable:
    variable: str
    importancia_n_eventos: float
    importancia_energia_kwh: float


@dataclass(frozen=True)
class PronosticoSubarea:
    codigo_subarea: str
    n_eventos: float
    energia_kwh: float


@dataclass(frozen=True)
class PaqueteModeloDns:
    """Corrida vigente completa del modelo DNS. Se valida al construirla."""

    origen: str
    periodo_pronostico: str  # AAAA-MM del mes pronosticado
    subareas: list[SubareaDns]
    eventos: list[EventoDns]
    zonas: list[ZonaPriorizada]
    cambios_reporte: list[CambioReporte]
    metricas: list[MetricaModelo]
    importancia: list[ImportanciaVariable]
    pronostico: list[PronosticoSubarea]

    def __post_init__(self) -> None:
        if not self.eventos:
            raise ValueError("el modelo DNS no trae eventos")
        if not self.subareas:
            raise ValueError("el modelo DNS no trae subareas")
        codigos = [s.codigo for s in self.subareas]
        if len(set(codigos)) != len(codigos):
            raise ValueError("subareas con codigo repetido")
        conocidos = set(codigos)
        referencias = (
            ("eventos", {e.codigo_subarea for e in self.eventos}),
            ("zonas", {z.codigo_subarea for z in self.zonas}),
            ("cambios de reporte", {c.codigo_subarea for c in self.cambios_reporte}),
            ("pronostico", {p.codigo_subarea for p in self.pronostico}),
        )
        for nombre, usados in referencias:
            desconocidas = sorted(usados - conocidos)
            if desconocidas:
                raise ValueError(f"{nombre} con subareas que no existen: {', '.join(desconocidas)}")
        for e in self.eventos:
            if e.energia_no_atendida_kwh < 0:
                raise ValueError("un evento tiene energia no atendida negativa")
            if e.tipo not in (TIPO_DNS, TIPO_EDAC):
                raise ValueError(f"tipo de evento desconocido: {e.tipo}")
        rankings = [z.ranking for z in self.zonas]
        if len(set(rankings)) != len(rankings):
            raise ValueError("zonas con ranking repetido")
        if len({(c.codigo_subarea, c.periodo_quiebre) for c in self.cambios_reporte}) != len(self.cambios_reporte):
            raise ValueError("cambios de reporte repetidos")

    @property
    def fecha_corte(self) -> datetime:
        """Fecha del ultimo evento: el corte de los datos."""
        return max(e.fecha_hora for e in self.eventos)

    @property
    def fecha_inicio(self) -> datetime:
        return min(e.fecha_hora for e in self.eventos)

    def subarea(self, codigo: str) -> Optional[SubareaDns]:
        return next((s for s in self.subareas if s.codigo == codigo), None)
