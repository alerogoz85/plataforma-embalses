"""Calculos del tablero DNS sobre los eventos (funciones puras, sin I/O).

Convenciones del modelo que aqui se respetan:
* Solo los eventos DNS con energia >= 0 entran en conteos y energia; los EDAC se cuentan aparte.
* Un evento es critico si deja sin atender >= 100.000 kWh.
* Los patrones por hora, dia de la semana y franja excluyen la «hora desconocida» (00:00:00 exacto).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from domain.entities.modelo_dns import (
    CAUSA_DESCONOCIDA,
    ORIGEN_NO_PROGRAMADA,
    ORIGEN_PROGRAMADA,
    TIPO_DNS,
    EventoDns,
    PaqueteModeloDns,
)
from domain.value_objects.filtro_dns import FiltroDns

DIAS_SEMANA = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
FRANJAS = ("Madrugada (0-5h)", "Mañana (6-11h)", "Tarde (12-17h)", "Noche (18-23h)")


def franja_horaria(hora: int) -> str:
    if hora <= 5:
        return FRANJAS[0]
    if hora <= 11:
        return FRANJAS[1]
    if hora <= 17:
        return FRANJAS[2]
    return FRANJAS[3]


def _indice_mes(f: datetime) -> int:
    return f.year * 12 + f.month - 1


def _etiqueta_mes(indice: int) -> str:
    return f"{indice // 12:04d}-{indice % 12 + 1:02d}"


@dataclass(frozen=True)
class Ventana:
    """Rango de meses [primer_mes, ultimo_mes] (indices year*12+mes-1) del periodo elegido."""

    primer_mes: int
    ultimo_mes: int

    def contiene(self, e: EventoDns) -> bool:
        return self.primer_mes <= _indice_mes(e.fecha_hora) <= self.ultimo_mes

    def anterior(self) -> "Ventana":
        largo = self.ultimo_mes - self.primer_mes + 1
        return Ventana(self.primer_mes - largo, self.primer_mes - 1)

    @property
    def meses(self) -> list[str]:
        return [_etiqueta_mes(i) for i in range(self.primer_mes, self.ultimo_mes + 1)]


def ventana_del_periodo(paquete: PaqueteModeloDns, periodo_meses: int) -> Ventana:
    ultimo = _indice_mes(paquete.fecha_corte)
    primero = _indice_mes(paquete.fecha_inicio) if periodo_meses == 0 else ultimo - periodo_meses + 1
    return Ventana(max(primero, _indice_mes(paquete.fecha_inicio)), ultimo)


def codigos_del_ambito(paquete: PaqueteModeloDns, filtro: FiltroDns) -> Optional[set[str]]:
    """Subareas del ambito geografico elegido (None = todas). La subarea manda sobre la region."""
    if filtro.subarea:
        return {filtro.subarea}
    if filtro.region:
        return {s.codigo for s in paquete.subareas if s.region == filtro.region}
    return None


def seleccionar(
    paquete: PaqueteModeloDns,
    filtro: FiltroDns,
    *,
    tipo: str = TIPO_DNS,
    ventana: Optional[Ventana] = None,
    con_origen: bool = True,
) -> list[EventoDns]:
    """Eventos de un tipo que cumplen los filtros. `con_origen=False` ignora el filtro de origen."""
    ventana = ventana or ventana_del_periodo(paquete, filtro.periodo_meses)
    ambito = codigos_del_ambito(paquete, filtro)
    salida = []
    for e in paquete.eventos:
        if e.tipo != tipo or not ventana.contiene(e):
            continue
        if tipo == TIPO_DNS and e.energia_no_atendida_kwh < 0:
            continue
        if ambito is not None and e.codigo_subarea not in ambito:
            continue
        if con_origen and filtro.origen and e.origen_evento != filtro.origen:
            continue
        salida.append(e)
    return salida


# ----------------------------------------------------------------------------- resumen
@dataclass(frozen=True)
class TotalesDns:
    eventos: int
    energia_kwh: float
    eventos_criticos: int
    eventos_no_programados: int
    eventos_con_origen: int


def totales(eventos: list[EventoDns]) -> TotalesDns:
    return TotalesDns(
        eventos=len(eventos),
        energia_kwh=sum(e.energia_no_atendida_kwh for e in eventos),
        eventos_criticos=sum(1 for e in eventos if e.es_critico),
        eventos_no_programados=sum(1 for e in eventos if e.origen_evento == ORIGEN_NO_PROGRAMADA),
        eventos_con_origen=sum(1 for e in eventos if e.origen_evento in (ORIGEN_PROGRAMADA, ORIGEN_NO_PROGRAMADA)),
    )


def variacion_pct(actual: float, anterior: float) -> Optional[float]:
    """Cambio porcentual frente al periodo previo; None si no hay base de comparacion."""
    if anterior <= 0:
        return None
    return (actual - anterior) / anterior * 100


# ----------------------------------------------------------------------------- serie mensual
@dataclass(frozen=True)
class MesDns:
    mes: str
    eventos: int
    energia_kwh: float
    eventos_no_programados: int
    parcial: bool  # el mes del corte aun no termina


def serie_mensual(paquete: PaqueteModeloDns, filtro: FiltroDns) -> list[MesDns]:
    ventana = ventana_del_periodo(paquete, filtro.periodo_meses)
    eventos = seleccionar(paquete, filtro, ventana=ventana)
    por_mes: dict[str, list[EventoDns]] = defaultdict(list)
    for e in eventos:
        por_mes[_etiqueta_mes(_indice_mes(e.fecha_hora))].append(e)
    corte = paquete.fecha_corte
    mes_corte = _etiqueta_mes(_indice_mes(corte))
    ultimo_dia_del_mes_corte = _ultimo_dia(corte)
    filas = []
    for mes in ventana.meses:
        del_mes = por_mes.get(mes, [])
        filas.append(
            MesDns(
                mes=mes,
                eventos=len(del_mes),
                energia_kwh=sum(e.energia_no_atendida_kwh for e in del_mes),
                eventos_no_programados=sum(1 for e in del_mes if e.origen_evento == ORIGEN_NO_PROGRAMADA),
                parcial=mes == mes_corte and corte.day < ultimo_dia_del_mes_corte,
            )
        )
    return filas


def _ultimo_dia(f: datetime) -> int:
    siguiente = datetime(f.year + (f.month == 12), f.month % 12 + 1, 1)
    return (siguiente - datetime(f.year, f.month, 1)).days


# ----------------------------------------------------------------------------- patrones
@dataclass(frozen=True)
class PatronesDns:
    por_hora: list[int]  # 24 posiciones
    por_dia_semana: list[int]  # 7 posiciones, lunes primero
    origen_por_franja: dict[str, tuple[int, int]]  # franja -> (no programados, programados)
    eventos_usados: int
    eventos_hora_desconocida: int


def patrones(paquete: PaqueteModeloDns, filtro: FiltroDns) -> PatronesDns:
    eventos = seleccionar(paquete, filtro)
    con_hora = [e for e in eventos if not e.hora_desconocida]
    por_hora = [0] * 24
    por_dia = [0] * 7
    franjas = {f: [0, 0] for f in FRANJAS}
    for e in con_hora:
        por_hora[e.fecha_hora.hour] += 1
        por_dia[e.fecha_hora.weekday()] += 1
        if e.origen_evento == ORIGEN_NO_PROGRAMADA:
            franjas[franja_horaria(e.fecha_hora.hour)][0] += 1
        elif e.origen_evento == ORIGEN_PROGRAMADA:
            franjas[franja_horaria(e.fecha_hora.hour)][1] += 1
    return PatronesDns(
        por_hora=por_hora,
        por_dia_semana=por_dia,
        origen_por_franja={f: (v[0], v[1]) for f, v in franjas.items()},
        eventos_usados=len(con_hora),
        eventos_hora_desconocida=len(eventos) - len(con_hora),
    )


# ----------------------------------------------------------------------------- causas
@dataclass(frozen=True)
class CausasDns:
    por_causa: list[tuple[str, int, float]]  # causa, eventos, energia_kwh (mayor energia primero)
    por_origen_de_la_causa: list[tuple[str, int]]  # reportada / inferida / sin clasificar
    por_tipo_evento: list[tuple[str, int]]
    por_nivel_red: list[tuple[str, int]]
    total: int


def causas(paquete: PaqueteModeloDns, filtro: FiltroDns) -> CausasDns:
    eventos = seleccionar(paquete, filtro)
    energia: dict[str, float] = defaultdict(float)
    conteo: Counter = Counter()
    for e in eventos:
        conteo[e.causa_definitiva] += 1
        energia[e.causa_definitiva] += e.energia_no_atendida_kwh
    por_causa = sorted(((c, conteo[c], energia[c]) for c in conteo), key=lambda t: (-t[2], t[0]))
    return CausasDns(
        por_causa=por_causa,
        por_origen_de_la_causa=Counter(e.origen_causa_definitiva for e in eventos).most_common(),
        por_tipo_evento=Counter(e.tipo_evento for e in eventos).most_common(),
        por_nivel_red=Counter(e.nivel_red for e in eventos).most_common(),
        total=len(eventos),
    )


def causa_mas_frecuente_conocida(eventos: list[EventoDns]) -> Optional[tuple[str, int]]:
    """La causa conocida que mas se repite (ignora «desconocido»)."""
    conteo = Counter(e.causa_definitiva for e in eventos if e.causa_definitiva != CAUSA_DESCONOCIDA)
    return conteo.most_common(1)[0] if conteo else None
