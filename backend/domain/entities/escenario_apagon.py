"""Escenarios precalculados del modelo de riesgo de apagon (Monte Carlo condicionado por ENOS).

El visor interactivo deja mover el ONI, las simulaciones y el horizonte. La plataforma no ejecuta el modelo al
consultar: guarda la corrida del modelo para CADA combinacion que ofrecen los controles (parametros cerrados abajo)
y la API devuelve la que corresponde. Es la salida real del modelo, con su semilla fija; aqui no se calcula nada."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

MODO_PROBABILISTICO = "probabilistico"
MODO_MANUAL = "manual"
MODOS_ONI = (MODO_PROBABILISTICO, MODO_MANUAL)
ONI_MINIMO = -2.5
ONI_MAXIMO = 2.5
ONI_PASO = 0.1
SIMULACIONES = (1000, 2000, 5000)
HORIZONTES = (12, 18, 24)
SIMULACIONES_POR_DEFECTO = 2000
HORIZONTE_POR_DEFECTO = 18
ONI_POR_DEFECTO = 1.0
SEMAFOROS = ("VERDE", "AMARILLO", "ROJO")
FRANJAS = ("madrugada_00_05", "manana_06_11", "tarde_12_17", "pico_noche_18_21", "noche_22_23")


def valores_oni() -> tuple[float, ...]:
    """Todos los ONI que ofrece el deslizador: de -2,5 a 2,5 de 0,1 en 0,1."""
    pasos = round((ONI_MAXIMO - ONI_MINIMO) / ONI_PASO)
    return tuple(round(ONI_MINIMO + i * ONI_PASO, 1) for i in range(pasos + 1))


def clave_escenario(modo: str, oni: Optional[float], simulaciones: int, horizonte: int) -> str:
    """Identificador de una combinacion; en modo probabilistico el ONI no interviene."""
    oni_txt = "-" if modo == MODO_PROBABILISTICO or oni is None else f"{oni:.1f}"
    return f"{modo}|{oni_txt}|{simulaciones}|{horizonte}"


@dataclass(frozen=True)
class MesEscenario:
    """Un mes del horizonte: percentiles, probabilidades, indice y semaforo tal como salen del modelo."""

    mes: str  # AAAA-MM
    indice_riesgo: float
    probabilidad_deficit: float  # 0-1
    probabilidad_apagon_severo: float  # 0-1
    semaforo: str
    oni_p10: float
    oni_p50: float
    oni_p90: float
    embalse_pct_p10: float
    embalse_pct_p50: float
    embalse_pct_p90: float
    demanda_mwh_p10: float
    demanda_mwh_p50: float
    demanda_mwh_p90: float
    oferta_mwh_p10: float
    oferta_mwh_p50: float
    oferta_mwh_p90: float
    deficit_mwh_p50: float
    deficit_mwh_p90: float
    margen_reserva_pct_p50: float
    deficit_por_franja_mwh: tuple[float, ...]  # una por cada franja de FRANJAS, en ese orden

    def __post_init__(self) -> None:
        if len(self.mes) != 7 or self.mes[4] != "-":
            raise ValueError(f"El mes '{self.mes}' debe tener la forma AAAA-MM")
        if self.semaforo not in SEMAFOROS:
            raise ValueError(f"Semaforo '{self.semaforo}' desconocido; admitidos: {', '.join(SEMAFOROS)}")
        for nombre in ("probabilidad_deficit", "probabilidad_apagon_severo"):
            if not 0 <= getattr(self, nombre) <= 1:
                raise ValueError(f"{nombre} debe estar entre 0 y 1")
        if len(self.deficit_por_franja_mwh) != len(FRANJAS):
            raise ValueError(f"El deficit por franja debe traer {len(FRANJAS)} valores")


@dataclass(frozen=True)
class EscenarioApagon:
    modo: str
    oni: Optional[float]  # None en modo probabilistico
    simulaciones: int
    horizonte: int
    meses: tuple[MesEscenario, ...]

    def __post_init__(self) -> None:
        if self.modo not in MODOS_ONI:
            raise ValueError(f"Modo de ONI '{self.modo}' desconocido; admitidos: {', '.join(MODOS_ONI)}")
        if (self.modo == MODO_MANUAL) != (self.oni is not None):
            raise ValueError("El ONI se indica solo en modo manual")
        if self.oni is not None and self.oni not in valores_oni():
            raise ValueError(f"El ONI {self.oni} no esta entre los valores del deslizador")
        if self.simulaciones not in SIMULACIONES or self.horizonte not in HORIZONTES:
            raise ValueError("Simulaciones u horizonte fuera de las opciones del visor")
        if len(self.meses) != self.horizonte:
            raise ValueError(f"El escenario trae {len(self.meses)} meses y el horizonte es {self.horizonte}")

    @property
    def clave(self) -> str:
        return clave_escenario(self.modo, self.oni, self.simulaciones, self.horizonte)


@dataclass(frozen=True)
class FuenteEscenarios:
    """Procedencia de la tanda de escenarios (la misma para todos)."""

    generado_en: datetime
    origen: str
    ultimo_oni_observado: Optional[float]
    ultimo_mes_demanda: Optional[str]
    semilla: int
