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
    filtros_columna: dict[str, str] = {}  # dimension -> columna por la que se filtran las filas


class LineaGraficoDTO(BaseModel):
    nombre: str
    estilo: str
    puntos: list[PuntoSerieDTO]


class GraficoResultadoDTO(BaseModel):
    id: str
    titulo: str
    unidad: str
    lineas: list[LineaGraficoDTO]
    etiquetas: dict[str, str]  # dimension -> valor


class DimensionFiltroDTO(BaseModel):
    id: str
    etiqueta: str
    opciones: list[str]
    por_defecto: str


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
    dimensiones: list[DimensionFiltroDTO] = []
    graficos: list[GraficoResultadoDTO] = []


class ResultadosModeloDTO(BaseModel):
    """`disponible = False` es un estado normal (el modelo aun no entrega resultados), no un error."""

    modelo_id: str
    disponible: bool
    resultado: Optional[ResultadoModeloDTO] = None


class MesEscenarioDTO(BaseModel):
    mes: str
    indice_riesgo: float
    probabilidad_deficit: float
    probabilidad_apagon_severo: float
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
    deficit_por_franja_mwh: list[float]


class EscenarioApagonDTO(BaseModel):
    modo: str
    oni: Optional[float]
    simulaciones: int
    horizonte: int
    meses: list[MesEscenarioDTO]


class FuenteEscenariosDTO(BaseModel):
    generado_en: datetime
    origen: str
    ultimo_oni_observado: Optional[float]
    ultimo_mes_demanda: Optional[str]
    semilla: int


class CatalogoEscenariosDTO(BaseModel):
    """Opciones de los controles del visor y procedencia. `disponible` es falso mientras no se importe la tanda."""

    disponible: bool
    modos: list[str]
    oni_minimo: float
    oni_maximo: float
    oni_paso: float
    oni_por_defecto: float
    simulaciones: list[int]
    simulaciones_por_defecto: int
    horizontes: list[int]
    horizonte_por_defecto: int
    franjas: list[str]
    fuente: Optional[FuenteEscenariosDTO] = None
