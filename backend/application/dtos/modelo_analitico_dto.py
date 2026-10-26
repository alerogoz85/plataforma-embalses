"""DTOs de /api/v1/modelos/{modelo_id}/*: ficha documentada y resultados importados."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel

Celda = Union[str, float, int, None]


class SeccionFichaDTO(BaseModel):
    titulo: str
    items: list[str]


class DatoDocumentadoDTO(BaseModel):
    etiqueta: str
    valor: str
    detalle: str
    documento: str


class ArchivoEsperadoDTO(BaseModel):
    ruta: str
    contenido: str


class FichaModeloDTO(BaseModel):
    id: str
    titulo: str
    resumen: str
    estado: str  # sin_resultados | prueba_tecnica | con_resultados
    estado_detalle: str
    documentos: str
    pregunta: str
    secciones: list[SeccionFichaDTO]
    datos_documentados: list[DatoDocumentadoDTO]
    archivos_esperados: list[ArchivoEsperadoDTO]
    comando_importacion: str
    carpeta_proyecto: str


class IndicadorDTO(BaseModel):
    etiqueta: str
    valor: str
    detalle: Optional[str] = None
    nivel: Optional[str] = None


class PuntoSerieDTO(BaseModel):
    x: str
    y: float
    p10: Optional[float] = None
    p90: Optional[float] = None


class SerieResultadoDTO(BaseModel):
    id: str
    titulo: str
    unidad: str
    tipo: str
    puntos: list[PuntoSerieDTO]


class TablaResultadoDTO(BaseModel):
    id: str
    titulo: str
    columnas: list[str]
    filas: list[list[Celda]]
    nota: Optional[str] = None


class ParametroDTO(BaseModel):
    nombre: str
    valor: str


class ResultadoModeloDTO(BaseModel):
    generado_en: datetime
    origen: str
    configuracion: list[ParametroDTO]
    indicadores: list[IndicadorDTO]
    series: list[SerieResultadoDTO]
    tablas: list[TablaResultadoDTO]
    advertencias: list[str]


class ResultadosModeloDTO(BaseModel):
    """`disponible = False` es un estado normal (el modelo aun no entrega resultados), no un error."""

    modelo_id: str
    disponible: bool
    resultado: Optional[ResultadoModeloDTO] = None
