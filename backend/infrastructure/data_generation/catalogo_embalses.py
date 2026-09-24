"""Catalogo de embalses sinteticos usado para poblar la plataforma de demo.

Los nombres y agrupaciones por region se inspiran libremente en el sistema
hidroelectrico colombiano solo para dar contexto geografico realista al
dashboard; las series de datos asociadas son enteramente sinteticas y no
representan mediciones oficiales.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DefinicionEmbalse:
    id: str
    nombre: str
    region: str
    planta: str
    cota_minima: float
    cota_maxima: float
    volumen_muerto_mm3: float
    volumen_maximo_mm3: float
    capacidad_instalada_mw: float
    aportes_media_base_m3s: float
    pct_volumen_util_inicial: float


CATALOGO_EMBALSES: list[DefinicionEmbalse] = [
    DefinicionEmbalse(
        "EMB-GUA", "Guatapé", "Antioquia", "Central Guatapé",
        1878, 1897, 200, 1238, 560, 45, 68,
    ),
    DefinicionEmbalse(
        "EMB-POR", "Porce II", "Antioquia", "Central Porce II",
        570, 587, 15, 128, 405, 90, 72,
    ),
    DefinicionEmbalse(
        "EMB-RIO", "Riogrande II", "Antioquia", "Central Niquía",
        2270, 2280, 60, 240, 76, 18, 45,
    ),
    DefinicionEmbalse(
        "EMB-BET", "Betania", "Centro", "Central Betania",
        555, 570, 150, 611, 540, 130, 70,
    ),
    DefinicionEmbalse(
        "EMB-PRA", "Prado", "Centro", "Central Prado",
        424, 442, 200, 950, 51, 60, 38,
    ),
    DefinicionEmbalse(
        "EMB-AMA", "Amaní", "Centro", "Central La Miel I",
        502, 520, 80, 375, 396, 75, 75,
    ),
    DefinicionEmbalse(
        "EMB-CHI", "Chivor", "Oriente", "Central Chivor",
        1178, 1197, 230, 720, 1000, 55, 58,
    ),
    DefinicionEmbalse(
        "EMB-ESM", "La Esmeralda", "Oriente", "Central Esmeralda",
        1180, 1190, 20, 60, 30, 12, 12,
    ),
    DefinicionEmbalse(
        "EMB-SAL", "Salvajina", "Valle", "Central Salvajina",
        1421, 1450, 230, 848, 285, 140, 60,
    ),
    DefinicionEmbalse(
        "EMB-ALT", "Alto Anchicayá", "Valle", "Central Alto Anchicayá",
        807, 815, 1.2, 4.6, 365, 45, 82,
    ),
    DefinicionEmbalse(
        "EMB-URR", "Urrá I", "Caribe", "Central Urrá I",
        26, 32, 700, 3221, 340, 220, 24,
    ),
    DefinicionEmbalse(
        "EMB-TOP", "Topocoro", "Caribe", "Central Sogamoso",
        240, 280, 1200, 4800, 820, 310, 33,
    ),
]
