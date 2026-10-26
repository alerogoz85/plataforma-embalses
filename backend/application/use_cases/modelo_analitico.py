"""Casos de uso de los tableros de modelos analiticos (gas, optimizacion, apagon): ficha y resultados."""
from __future__ import annotations

from application.dtos.modelo_analitico_dto import (
    ArchivoEsperadoDTO,
    DatoDocumentadoDTO,
    FichaModeloDTO,
    IndicadorDTO,
    ParametroDTO,
    PuntoSerieDTO,
    ResultadoModeloDTO,
    ResultadosModeloDTO,
    SerieResultadoDTO,
    SeccionFichaDTO,
    TablaResultadoDTO,
)
from domain.entities.modelo_analitico import ESTADO_CON_RESULTADOS, MODELOS_CON_FICHA
from domain.exceptions import ModeloNoEncontradoError
from domain.repositories.modelo_analitico_repository import FichaModeloRepository, ResultadoModeloRepository


def _validar(modelo_id: str) -> None:
    if modelo_id not in MODELOS_CON_FICHA:
        raise ModeloNoEncontradoError(modelo_id)


class ObtenerFichaModeloUseCase:
    """La ficha cambia a «con_resultados» cuando hay un resultado importado: el estado documentado se mantiene como texto."""

    def __init__(self, fichas: FichaModeloRepository, resultados: ResultadoModeloRepository) -> None:
        self._fichas = fichas
        self._resultados = resultados

    def ejecutar(self, modelo_id: str) -> FichaModeloDTO:
        _validar(modelo_id)
        ficha = self._fichas.obtener(modelo_id)
        if ficha is None:
            raise ModeloNoEncontradoError(modelo_id)
        hay_resultado = self._resultados.obtener(modelo_id) is not None
        return FichaModeloDTO(
            id=ficha.id, titulo=ficha.titulo, resumen=ficha.resumen,
            estado=ESTADO_CON_RESULTADOS if hay_resultado else ficha.estado,
            estado_detalle=ficha.estado_detalle, documentos=ficha.documentos, pregunta=ficha.pregunta,
            secciones=[SeccionFichaDTO(titulo=s.titulo, items=list(s.items)) for s in ficha.secciones],
            datos_documentados=[
                DatoDocumentadoDTO(etiqueta=d.etiqueta, valor=d.valor, detalle=d.detalle, documento=d.documento)
                for d in ficha.datos_documentados
            ],
            archivos_esperados=[ArchivoEsperadoDTO(ruta=a.ruta, contenido=a.contenido) for a in ficha.archivos_esperados],
            comando_importacion=ficha.comando_importacion, carpeta_proyecto=ficha.carpeta_proyecto,
        )


class ObtenerResultadosModeloUseCase:
    def __init__(self, resultados: ResultadoModeloRepository) -> None:
        self._resultados = resultados

    def ejecutar(self, modelo_id: str) -> ResultadosModeloDTO:
        _validar(modelo_id)
        r = self._resultados.obtener(modelo_id)
        if r is None:
            return ResultadosModeloDTO(modelo_id=modelo_id, disponible=False)
        return ResultadosModeloDTO(
            modelo_id=modelo_id, disponible=True,
            resultado=ResultadoModeloDTO(
                generado_en=r.generado_en, origen=r.origen,
                configuracion=[ParametroDTO(nombre=n, valor=v) for n, v in r.configuracion],
                indicadores=[IndicadorDTO(etiqueta=i.etiqueta, valor=i.valor, detalle=i.detalle, nivel=i.nivel) for i in r.indicadores],
                series=[
                    SerieResultadoDTO(
                        id=s.id, titulo=s.titulo, unidad=s.unidad, tipo=s.tipo,
                        puntos=[PuntoSerieDTO(x=p.x, y=p.y, p10=p.p10, p90=p.p90) for p in s.puntos],
                    )
                    for s in r.series
                ],
                tablas=[
                    TablaResultadoDTO(id=t.id, titulo=t.titulo, columnas=list(t.columnas), filas=[list(f) for f in t.filas], nota=t.nota)
                    for t in r.tablas
                ],
                advertencias=list(r.advertencias),
            ),
        )
