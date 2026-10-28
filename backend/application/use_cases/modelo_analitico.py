"""Casos de uso de los tableros de modelos analiticos (gas, optimizacion, apagon): ficha y resultados."""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from application.dtos.modelo_analitico_dto import (
    ArchivoEsperadoDTO,
    CatalogoEscenariosDTO,
    EscenarioApagonDTO,
    FuenteEscenariosDTO,
    MesEscenarioDTO,
    DatoDocumentadoDTO,
    DimensionFiltroDTO,
    GraficoResultadoDTO,
    LineaGraficoDTO,
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
from domain.entities import escenario_apagon as esc
from domain.entities.modelo_analitico import ESTADO_CON_RESULTADOS, MODELOS_CON_FICHA
from domain.exceptions import EscenarioNoDisponibleError, FiltroInvalidoError, ModeloNoEncontradoError
from domain.repositories.modelo_analitico_repository import EscenarioApagonRepository, FichaModeloRepository, ResultadoModeloRepository


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
            estado_detalle=ficha.estado_detalle_con_resultados if hay_resultado else ficha.estado_detalle, documentos=ficha.documentos, pregunta=ficha.pregunta,
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
                    TablaResultadoDTO(id=t.id, titulo=t.titulo, columnas=list(t.columnas), filas=[list(f) for f in t.filas], nota=t.nota,
                                      filtros_columna=dict(t.filtros_columna))
                    for t in r.tablas
                ],
                advertencias=list(r.advertencias),
                dimensiones=[
                    DimensionFiltroDTO(id=d.id, etiqueta=d.etiqueta, opciones=list(d.opciones), por_defecto=d.por_defecto) for d in r.dimensiones
                ],
                graficos=[
                    GraficoResultadoDTO(
                        id=g.id, titulo=g.titulo, unidad=g.unidad, etiquetas=dict(g.etiquetas),
                        lineas=[
                            LineaGraficoDTO(nombre=l.nombre, estilo=l.estilo, puntos=[PuntoSerieDTO(x=p.x, y=p.y, p10=p.p10, p90=p.p90) for p in l.puntos])
                            for l in g.lineas
                        ],
                    )
                    for g in r.graficos
                ],
            ),
        )


class ObtenerCatalogoEscenariosApagonUseCase:
    """Opciones de los controles del visor de apagon y procedencia de la tanda de escenarios importada."""

    def __init__(self, escenarios: EscenarioApagonRepository) -> None:
        self._escenarios = escenarios

    def ejecutar(self) -> CatalogoEscenariosDTO:
        fuente = self._escenarios.fuente()
        return CatalogoEscenariosDTO(
            disponible=fuente is not None, modos=list(esc.MODOS_ONI),
            oni_minimo=esc.ONI_MINIMO, oni_maximo=esc.ONI_MAXIMO, oni_paso=esc.ONI_PASO, oni_por_defecto=esc.ONI_POR_DEFECTO,
            simulaciones=list(esc.SIMULACIONES), simulaciones_por_defecto=esc.SIMULACIONES_POR_DEFECTO,
            horizontes=list(esc.HORIZONTES), horizonte_por_defecto=esc.HORIZONTE_POR_DEFECTO, franjas=list(esc.FRANJAS),
            fuente=None if fuente is None else FuenteEscenariosDTO(
                generado_en=fuente.generado_en, origen=fuente.origen, ultimo_oni_observado=fuente.ultimo_oni_observado,
                ultimo_mes_demanda=fuente.ultimo_mes_demanda, semilla=fuente.semilla),
        )


class ObtenerEscenarioApagonUseCase:
    def __init__(self, escenarios: EscenarioApagonRepository) -> None:
        self._escenarios = escenarios

    def ejecutar(self, modo: str, oni: Optional[float], simulaciones: int, horizonte: int) -> EscenarioApagonDTO:
        """El escenario de esa combinacion; los valores se validan contra las opciones del visor (FiltroInvalidoError -> 422)."""
        if modo not in esc.MODOS_ONI:
            raise FiltroInvalidoError(f"Modo de ONI desconocido; admitidos: {', '.join(esc.MODOS_ONI)}")
        if modo == esc.MODO_MANUAL:
            oni = esc.ONI_POR_DEFECTO if oni is None else oni
            # Solo los valores del deslizador (de 0,1 en 0,1): uno intermedio no tiene escenario y se rechaza.
            if abs(oni * 10 - round(oni * 10)) > 1e-6 or round(oni, 1) not in esc.valores_oni():
                raise FiltroInvalidoError(f"El ONI debe estar entre {esc.ONI_MINIMO} y {esc.ONI_MAXIMO} de {esc.ONI_PASO} en {esc.ONI_PASO}")
        else:
            oni = None
        if simulaciones not in esc.SIMULACIONES:
            raise FiltroInvalidoError(f"Simulaciones admitidas: {', '.join(map(str, esc.SIMULACIONES))}")
        if horizonte not in esc.HORIZONTES:
            raise FiltroInvalidoError(f"Horizontes admitidos: {', '.join(map(str, esc.HORIZONTES))}")
        oni = None if oni is None else round(oni, 1)
        e = self._escenarios.obtener(modo, oni, simulaciones, horizonte)
        if e is None:
            raise EscenarioNoDisponibleError()
        return EscenarioApagonDTO(
            modo=e.modo, oni=e.oni, simulaciones=e.simulaciones, horizonte=e.horizonte,
            meses=[MesEscenarioDTO(**{**asdict(m), "deficit_por_franja_mwh": list(m.deficit_por_franja_mwh)}) for m in e.meses],
        )
