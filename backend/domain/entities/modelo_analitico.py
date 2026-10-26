"""Entidades comunes de los modelos analiticos que aun no tienen (o apenas empiezan a tener) resultados:
gas fiscalizado vs. declarado, optimizacion hidrotermica (SDDP) y riesgo de apagon.

Cada modelo se describe con una FICHA (lo que documentan sus entregables: pregunta, metodo, datos,
alcance, limitaciones y estado) y, cuando existen, con un RESULTADO importado de sus archivos de salida.
La plataforma nunca inventa cifras: sin resultado importado, el tablero muestra solo la ficha y dice
que faltan los resultados."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

MODELOS_CON_FICHA = ("gas", "optimizacion", "apagon")

ESTADO_SIN_RESULTADOS = "sin_resultados"  # documentado, sin salidas del modelo disponibles
ESTADO_PRUEBA_TECNICA = "prueba_tecnica"  # hay corridas de verificacion no publicables
ESTADO_CON_RESULTADOS = "con_resultados"
ESTADOS_FICHA = (ESTADO_SIN_RESULTADOS, ESTADO_PRUEBA_TECNICA, ESTADO_CON_RESULTADOS)

NIVELES = ("ok", "alerta", "critico")
TIPOS_SERIE = ("linea", "barras")

Celda = Union[str, float, int, None]


@dataclass(frozen=True)
class SeccionFicha:
    titulo: str
    items: tuple[str, ...]


@dataclass(frozen=True)
class DatoDocumentado:
    """Una cifra que ya esta publicada en los documentos del modelo (no es un resultado calculado aqui)."""

    etiqueta: str
    valor: str
    detalle: str
    documento: str  # de que documento sale


@dataclass(frozen=True)
class ArchivoEsperado:
    ruta: str  # relativa a la carpeta del proyecto del modelo
    contenido: str


@dataclass(frozen=True)
class FichaModelo:
    id: str
    titulo: str
    resumen: str
    estado: str
    estado_detalle: str
    documentos: str  # que documentos respaldan la ficha y de que fecha
    pregunta: str
    secciones: tuple[SeccionFicha, ...]
    datos_documentados: tuple[DatoDocumentado, ...]
    archivos_esperados: tuple[ArchivoEsperado, ...]
    comando_importacion: str
    carpeta_proyecto: str

    def __post_init__(self) -> None:
        if self.id not in MODELOS_CON_FICHA:
            raise ValueError(f"modelo desconocido: {self.id}")
        if self.estado not in ESTADOS_FICHA:
            raise ValueError(f"estado de ficha desconocido: {self.estado}")
        if not self.archivos_esperados:
            raise ValueError("una ficha debe decir que archivos espera el importador")


@dataclass(frozen=True)
class Indicador:
    etiqueta: str
    valor: str
    detalle: Optional[str] = None
    nivel: Optional[str] = None  # ok / alerta / critico: colorea la tarjeta

    def __post_init__(self) -> None:
        if self.nivel is not None and self.nivel not in NIVELES:
            raise ValueError(f"nivel desconocido: {self.nivel}")


@dataclass(frozen=True)
class PuntoSerie:
    x: str  # etiqueta ordenable (AAAA-MM o AAAA-MM-DD)
    y: float
    p10: Optional[float] = None
    p90: Optional[float] = None

    def __post_init__(self) -> None:
        if (self.p10 is None) != (self.p90 is None):
            raise ValueError("una banda necesita p10 y p90")
        if self.p10 is not None and not (self.p10 <= self.y <= self.p90):
            raise ValueError(f"la banda no contiene al valor central en {self.x}: debe cumplirse p10 <= y <= p90")


@dataclass(frozen=True)
class SerieResultado:
    id: str
    titulo: str
    unidad: str
    tipo: str
    puntos: tuple[PuntoSerie, ...]

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_SERIE:
            raise ValueError(f"tipo de serie desconocido: {self.tipo}")
        if not self.puntos:
            raise ValueError(f"la serie '{self.id}' no tiene puntos")
        xs = [p.x for p in self.puntos]
        if len(set(xs)) != len(xs):
            raise ValueError(f"la serie '{self.id}' tiene puntos repetidos")


@dataclass(frozen=True)
class TablaResultado:
    id: str
    titulo: str
    columnas: tuple[str, ...]
    filas: tuple[tuple[Celda, ...], ...]
    nota: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.columnas:
            raise ValueError(f"la tabla '{self.id}' no tiene columnas")
        if any(len(f) != len(self.columnas) for f in self.filas):
            raise ValueError(f"la tabla '{self.id}' tiene filas de distinto largo que sus columnas")


@dataclass(frozen=True)
class ResultadoModelo:
    """Salida importada de un modelo. Se valida al construirla; ningun valor se calcula aqui."""

    modelo_id: str
    generado_en: datetime
    origen: str
    configuracion: tuple[tuple[str, str], ...] = ()
    indicadores: tuple[Indicador, ...] = ()
    series: tuple[SerieResultado, ...] = ()
    tablas: tuple[TablaResultado, ...] = ()
    advertencias: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.modelo_id not in MODELOS_CON_FICHA:
            raise ValueError(f"modelo desconocido: {self.modelo_id}")
        if not (self.indicadores or self.series or self.tablas):
            raise ValueError("un resultado debe traer al menos un indicador, una serie o una tabla")
        for nombre, items in (("series", self.series), ("tablas", self.tablas)):
            ids = [i.id for i in items]
            if len(set(ids)) != len(ids):
                raise ValueError(f"{nombre} con id repetido")
