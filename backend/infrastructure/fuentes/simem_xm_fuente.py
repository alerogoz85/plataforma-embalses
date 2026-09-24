"""Fuente de datos reales: SIMEM (volumenes, descargas, aportes) + API de XM
(energia util y capacidad util en energia por embalse).

Los datasets de SIMEM usados son:
  138ED1  capacidad util y volumen util diario por embalse (m3)
  1445AC  descargas (turbinada, no turbinada, vertimiento) por embalse (m3/dia)
  02B289  aportes hidricos por serie hidrologica de rio (m3/s) y media historica
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import date
from typing import Any, Protocol

from application.ports.output.fuente_mediciones_port import DescargaMediciones, FuenteMedicionesPort
from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.entities.region import NombreRegion, Region
from domain.exceptions import FuenteDatosError
from domain.value_objects.caudal import Caudal
from domain.value_objects.volumen import Volumen

logger = logging.getLogger(__name__)

SEGUNDOS_POR_DIA = 86_400
M3_POR_MM3 = 1_000_000
KWH_POR_GWH = 1_000_000

ID_AGREGADO_BOGOTA = "AGREGADO_BOGOTA"
# XM renombro el agregado de Bogota de AGREGADO_BOGOTA a AGREGADO en enero de 2025.
CODIGOS_AGREGADO_BOGOTA = frozenset({"AGREGADO", ID_AGREGADO_BOGOTA})
# Agregado nacional oficial de XM: no es un embalse, se usa solo como referencia.
CODIGO_AGREGADO_NACIONAL = "AGREGADO_SIN"

NOMBRES_EMBALSES = {
    "ALTOANCH": "Alto Anchicayá",
    "BETANIA": "Betania",
    "CALIMA1": "Calima",
    "CHUZA": "Chuza",
    "ELQUIMBO": "El Quimbo",
    "ESMERALD": "Esmeralda",
    "GUAVIO": "Guavio",
    "ITUANGO": "Ituango",
    "MIEL1": "Amaní (Miel I)",
    "MIRAFLOR": "Miraflores",
    "MUNA": "Muna",
    "PENOL": "Guatapé (Peñol)",
    "PLAYAS": "Playas",
    "PORCE2": "Porce II",
    "PORCE3": "Porce III",
    "PRADO": "Prado",
    "PUNCHINA": "Punchiná",
    "RIOGRAN2": "Río Grande 2",
    "SALVAJIN": "Salvajina",
    "SANLOREN": "San Lorenzo",
    "SOGAMOSO": "Sogamoso (Topocoro)",
    "TRONERAS": "Troneras",
    "URRA1": "Urrá I",
    ID_AGREGADO_BOGOTA: "Agregado Bogotá",
}

# Serie hidrologica de rio (dataset 02B289) -> embalse al que aporta. Mapeo del
# proyecto de modelado previo, con los codigos vigentes y los anteriores que XM
# renombro. Varias series pueden alimentar el mismo embalse y se suman. MUNA no
# tiene serie de aportes publicada.
SERIE_A_EMBALSE = {
    "ALTOANCH": "ALTOANCH",
    "AMANMIEL": "MIEL1",
    "PTEHMIEL": "MIEL1",
    "BETAMAG1": "BETANIA",
    "BETAMAGD": "BETANIA",
    "CAL1CALM": "CALIMA1",
    "EMBACHUZ": "CHUZA",
    "QUIMMAGD": "ELQUIMBO",
    "ESMECAMP": "ESMERALD",
    "GUAVGUAV": "GUAVIO",
    "EMBAGUAV": "GUAVIO",
    "ITUACAUC": "ITUANGO",
    "MIRFTENC": "MIRAFLOR",
    "EMBAMUNA": "MUNA",
    "PENONARE": "PENOL",
    "PLAYGUAT": "PLAYAS",
    "PP-2POR1": "PORCE2",
    "PP-2PORC": "PORCE2",
    "PP-3PORC": "PORCE3",
    "EMBAPRAD": "PRADO",
    "PUNCGUAT": "PUNCHINA",
    "RGR2RGRD": "RIOGRAN2",
    "SALVCAUC": "SALVAJIN",
    "SLORNARE": "SANLOREN",
    "SOGASOGA": "SOGAMOSO",
    "TRONGUAD": "TRONERAS",
    "URR1SINU": "URRA1",
}


class ClienteSimemPuerto(Protocol):
    def consultar(self, dataset_id: str, desde: date, hasta: date) -> list[dict[str, Any]]: ...


class ClienteXmPuerto(Protocol):
    def listar_embalses(self) -> list[dict[str, str]]: ...

    def metrica_diaria_embalses(
        self, metrica: str, desde: date, hasta: date
    ) -> list[dict[str, Any]]: ...


def normalizar_codigo(codigo: str) -> str:
    return ID_AGREGADO_BOGOTA if codigo in CODIGOS_AGREGADO_BOGOTA else codigo


def _fecha(texto: str) -> date:
    return date.fromisoformat(texto[:10])


def indexar_energia(
    filas: list[dict[str, Any]], codigo_por_nombre: dict[str, str]
) -> dict[tuple[str, date], float]:
    """(codigo, fecha) -> GWh, a partir de una metrica de energia de XM (kWh)."""
    indice: dict[tuple[str, date], float] = {}
    for fila in filas:
        codigo = codigo_por_nombre.get(fila["Name"])
        if codigo is None or fila["Value"] is None:
            continue
        indice[(codigo, _fecha(fila["Date"]))] = fila["Value"] / KWH_POR_GWH
    return indice


def indexar_descargas(filas: list[dict[str, Any]]) -> dict[tuple[str, date, str], float]:
    """(codigo, fecha, tipo) -> m3/s, a partir del dataset 1445AC (m3/dia)."""
    indice: dict[tuple[str, date, str], float] = defaultdict(float)
    for fila in filas:
        if fila.get("Volumen") is None:
            continue
        clave = (normalizar_codigo(fila["CodigoEmbalse"]), _fecha(fila["Fecha"]), fila["TipoDescarga"])
        indice[clave] += fila["Volumen"] / SEGUNDOS_POR_DIA
    return dict(indice)


def indexar_aportes(
    filas: list[dict[str, Any]],
) -> dict[tuple[str, date], tuple[float, float]]:
    """(codigo, fecha) -> (aportes m3/s, media historica m3/s), sumando las
    series de rio que alimentan a cada embalse."""
    indice: dict[tuple[str, date], list[float]] = defaultdict(lambda: [0.0, 0.0])
    for fila in filas:
        embalse = SERIE_A_EMBALSE.get(fila["CodigoSerieHidrologica"])
        if embalse is None or fila["AportesHidricosMasa"] is None:
            continue
        acumulado = indice[(embalse, _fecha(fila["Fecha"]))]
        acumulado[0] += fila["AportesHidricosMasa"]
        acumulado[1] += fila.get("MediaHistoricaMasa") or 0.0
    return {clave: (valores[0], valores[1]) for clave, valores in indice.items()}


def _capacidad_mas_cercana(
    capacidad_energia: dict[tuple[str, date], float],
) -> dict[str, list[tuple[date, float]]]:
    por_embalse: dict[str, list[tuple[date, float]]] = defaultdict(list)
    for (codigo, fecha), gwh in capacidad_energia.items():
        por_embalse[codigo].append((fecha, gwh))
    for lista in por_embalse.values():
        lista.sort()
    return por_embalse


def _peso_mas_cercano(publicaciones: list[tuple[date, float]], fecha: date) -> float:
    """Capacidad energetica publicada mas cercana en el tiempo (peso de
    agregacion cuando XM no la publica ese dia)."""
    return min(publicaciones, key=lambda par: abs((par[0] - fecha).days))[1]


def ensamblar(
    volumenes: list[dict[str, Any]],
    descargas: list[dict[str, Any]],
    aportes: list[dict[str, Any]],
    energia_util: dict[tuple[str, date], float],
    capacidad_energia: dict[tuple[str, date], float],
) -> tuple[list[Embalse], list[MedicionHidrologica], int]:
    """Une las fuentes por (embalse, fecha). Devuelve embalses, mediciones y
    cuantos registros se descartaron por no poder determinar su peso."""
    descargas_idx = indexar_descargas(descargas)
    aportes_idx = indexar_aportes(aportes)
    capacidades = _capacidad_mas_cercana(capacidad_energia)

    embalses: dict[str, Embalse] = {}
    mediciones: list[MedicionHidrologica] = []
    descartadas = 0

    for fila in sorted(volumenes, key=lambda f: f.get("FechaPublicacion") or ""):
        codigo = normalizar_codigo(fila["CodigoEmbalse"])
        if codigo == CODIGO_AGREGADO_NACIONAL:
            continue
        fecha = _fecha(fila["Fecha"])

        capacidad_gwh = capacidad_energia.get((codigo, fecha))
        if capacidad_gwh is None:
            if codigo not in capacidades:
                descartadas += 1
                continue
            capacidad_gwh = _peso_mas_cercano(capacidades[codigo], fecha)

        try:
            region = Region(NombreRegion(fila["RegionHidrologica"]))
        except ValueError as error:
            raise FuenteDatosError(
                f"Region hidrologica desconocida '{fila['RegionHidrologica']}' en {codigo}"
            ) from error
        embalses[codigo] = Embalse(
            id=codigo,
            nombre=NOMBRES_EMBALSES.get(codigo, codigo.title()),
            region=region,
            es_agregado=codigo == ID_AGREGADO_BOGOTA,
        )

        turbinado = descargas_idx.get((codigo, fecha, "DESCARGA TURBINADA"))
        vertimiento = descargas_idx.get((codigo, fecha, "VERTIMIENTO"))
        aporte = aportes_idx.get((codigo, fecha))
        mediciones.append(
            MedicionHidrologica(
                embalse_id=codigo,
                fecha=fecha,
                volumen_util=Volumen(fila["VolumenUtilDiarioMasa"] / M3_POR_MM3),
                capacidad_util=Volumen(fila["CapacidadUtilMasa"] / M3_POR_MM3),
                capacidad_util_energia_gwh=capacidad_gwh,
                energia_util_gwh=energia_util.get((codigo, fecha)),
                aportes=Caudal(aporte[0]) if aporte else None,
                aportes_media_historica_m3s=aporte[1] if aporte and aporte[1] > 0 else None,
                vertimientos=Caudal(vertimiento) if vertimiento is not None else None,
                turbinado=Caudal(turbinado) if turbinado is not None else None,
            )
        )
    return list(embalses.values()), mediciones, descartadas


class SimemXmFuenteMediciones(FuenteMedicionesPort):
    """Adaptador que descarga datos reales de SIMEM y XM."""

    def __init__(self, simem: ClienteSimemPuerto, xm: ClienteXmPuerto) -> None:
        self._simem = simem
        self._xm = xm

    def descargar(self, desde: date, hasta: date) -> DescargaMediciones:
        logger.info("Descargando SIMEM %s..%s", desde, hasta)
        volumenes = self._simem.consultar("138ED1", desde, hasta)
        descargas = self._simem.consultar("1445AC", desde, hasta)
        aportes = self._simem.consultar("02B289", desde, hasta)

        codigo_por_nombre = {
            e["Name"]: normalizar_codigo(e["Code"]) for e in self._xm.listar_embalses()
        }
        logger.info("Descargando energia XM %s..%s", desde, hasta)
        energia_util = indexar_energia(
            self._xm.metrica_diaria_embalses("VoluUtilDiarEner", desde, hasta), codigo_por_nombre
        )
        capacidad_energia = indexar_energia(
            self._xm.metrica_diaria_embalses("CapaUtilDiarEner", desde, hasta), codigo_por_nombre
        )

        embalses, mediciones, descartadas = ensamblar(
            volumenes, descargas, aportes, energia_util, capacidad_energia
        )
        if descartadas:
            logger.warning("%d registros descartados: XM no publica capacidad de energia", descartadas)
        if not mediciones:
            raise FuenteDatosError(f"La fuente no devolvio mediciones para {desde}..{hasta}")

        return DescargaMediciones(
            embalses=embalses,
            mediciones=mediciones,
            fuente="SIMEM / XM",
            descripcion=(
                "Volumenes, descargas y aportes de SIMEM (datasets 138ED1, 1445AC, 02B289); "
                "energia util y capacidad util en energia de la API de XM."
            ),
            es_real=True,
        )
