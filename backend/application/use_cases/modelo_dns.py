"""Casos de uso del tablero de demanda no atendida (DNS): leen la corrida vigente y la resumen.

Los filtros (periodo, region, subarea, origen) llegan ya validados contra listas cerradas; la
region y la subarea se validan ademas contra el catalogo de la corrida cargada."""
from __future__ import annotations

from typing import Optional

from application.dtos.modelo_dns_dto import (
    CambioReporteDTO,
    CambiosReporteDTO,
    CatalogoDnsDTO,
    CausaDTO,
    CausasDnsDTO,
    ConteoDTO,
    FranjaDTO,
    ImportanciaDTO,
    MesDnsDTO,
    MetricaDTO,
    ModeloDnsDTO,
    PatronesDnsDTO,
    PronosticoMesDTO,
    PronosticoSubareaDTO,
    ResumenDnsDTO,
    SerieDnsDTO,
    SubareaDTO,
    ZonaDTO,
    ZonasDnsDTO,
)
from domain.entities.modelo_dns import REGION_SIN_ASIGNAR, TIPO_EDAC, PaqueteModeloDns
from domain.exceptions import FiltroInvalidoError, ModeloDnsNoCargadoError
from domain.repositories.modelo_dns_repository import ModeloDnsRepository
from domain.services import analisis_dns as analisis
from domain.value_objects.filtro_dns import ORIGENES_PERMITIDOS, PERIODOS_PERMITIDOS_MESES, FiltroDns

PERIODOS_PERMITIDOS = PERIODOS_PERMITIDOS_MESES
ORIGENES_VALIDOS = ORIGENES_PERMITIDOS
TOP_VARIABLES_IMPORTANCIA = 10
_KWH_POR_GWH = 1_000_000.0


class _CasoDeUsoDns:
    def __init__(self, repositorio: ModeloDnsRepository) -> None:
        self._repositorio = repositorio

    def _paquete(self) -> PaqueteModeloDns:
        paquete = self._repositorio.obtener()
        if paquete is None:
            raise ModeloDnsNoCargadoError()
        return paquete

    @staticmethod
    def _validar_ambito(paquete: PaqueteModeloDns, region: Optional[str], subarea: Optional[str]) -> None:
        if region and region not in {s.region for s in paquete.subareas}:
            raise FiltroInvalidoError(f"La region '{region}' no existe en el modelo")
        if subarea and paquete.subarea(subarea) is None:
            raise FiltroInvalidoError(f"La subarea '{subarea}' no existe en el modelo")

    def _filtro(self, paquete, periodo_meses, region, subarea, origen) -> FiltroDns:
        self._validar_ambito(paquete, region, subarea)
        return FiltroDns(periodo_meses=periodo_meses, region=region, subarea=subarea, origen=origen)


def _gwh(kwh: float) -> float:
    return kwh / _KWH_POR_GWH


class ObtenerCatalogoDnsUseCase(_CasoDeUsoDns):
    def ejecutar(self) -> CatalogoDnsDTO:
        p = self._paquete()
        corte = p.fecha_corte
        return CatalogoDnsDTO(
            origen=p.origen,
            fecha_inicio=p.fecha_inicio.date(),
            fecha_corte=corte.date(),
            mes_corte_parcial=serie_parcial(p),
            regiones=sorted({s.region for s in p.subareas if s.region != REGION_SIN_ASIGNAR})
            + ([REGION_SIN_ASIGNAR] if any(s.region == REGION_SIN_ASIGNAR for s in p.subareas) else []),
            subareas=[
                SubareaDTO(codigo=s.codigo, nombre=s.nombre, region=s.region, departamentos=s.departamentos)
                for s in sorted(p.subareas, key=lambda s: s.nombre)
            ],
            periodo_pronostico=p.periodo_pronostico,
        )


def serie_parcial(paquete: PaqueteModeloDns) -> bool:
    ultimos = analisis.serie_mensual(paquete, FiltroDns(periodo_meses=12))
    return bool(ultimos) and ultimos[-1].parcial


class ObtenerResumenDnsUseCase(_CasoDeUsoDns):
    def ejecutar(self, periodo_meses: int, region: Optional[str], subarea: Optional[str], origen: Optional[str]) -> ResumenDnsDTO:
        p = self._paquete()
        filtro = self._filtro(p, periodo_meses, region, subarea, origen)
        ventana = analisis.ventana_del_periodo(p, periodo_meses)
        eventos = analisis.seleccionar(p, filtro, ventana=ventana)
        t = analisis.totales(eventos)

        var_eventos = var_energia = None
        previa = ventana.anterior()
        primer_mes_datos = analisis.ventana_del_periodo(p, 0).primer_mes
        if periodo_meses != 0 and previa.primer_mes >= primer_mes_datos:
            t_prev = analisis.totales(analisis.seleccionar(p, filtro, ventana=previa))
            var_eventos = analisis.variacion_pct(t.eventos, t_prev.eventos)
            var_energia = analisis.variacion_pct(t.energia_kwh, t_prev.energia_kwh)

        causa = analisis.causa_mas_frecuente_conocida(eventos)
        edac = analisis.seleccionar(p, filtro, tipo=TIPO_EDAC, ventana=ventana, con_origen=False)
        return ResumenDnsDTO(
            periodo_meses=periodo_meses,
            desde=ventana.meses[0],
            hasta=ventana.meses[-1],
            eventos=t.eventos,
            energia_gwh=_gwh(t.energia_kwh),
            pct_criticos=(t.eventos_criticos / t.eventos * 100) if t.eventos else 0.0,
            pct_no_programados=(t.eventos_no_programados / t.eventos_con_origen * 100) if t.eventos_con_origen else None,
            variacion_eventos_pct=var_eventos,
            variacion_energia_pct=var_energia,
            causa_mas_frecuente=causa[0] if causa else None,
            causa_mas_frecuente_eventos=causa[1] if causa else 0,
            eventos_edac=len(edac),
        )


class ObtenerSerieDnsUseCase(_CasoDeUsoDns):
    def ejecutar(self, periodo_meses: int, region: Optional[str], subarea: Optional[str], origen: Optional[str]) -> SerieDnsDTO:
        p = self._paquete()
        filtro = self._filtro(p, periodo_meses, region, subarea, origen)
        meses = [
            MesDnsDTO(mes=m.mes, eventos=m.eventos, energia_gwh=_gwh(m.energia_kwh),
                      eventos_no_programados=m.eventos_no_programados, parcial=m.parcial)
            for m in analisis.serie_mensual(p, filtro)
        ]
        pronostico, nota = None, None
        if origen:
            nota = "El pronóstico es del total del mes y no se separa por origen: quita el filtro de origen para verlo."
        else:
            ambito = analisis.codigos_del_ambito(p, filtro)
            filas = [f for f in p.pronostico if ambito is None or f.codigo_subarea in ambito]
            if filas:
                pronostico = PronosticoMesDTO(
                    mes=p.periodo_pronostico,
                    eventos=sum(f.n_eventos for f in filas),
                    energia_gwh=_gwh(sum(f.energia_kwh for f in filas)),
                    subareas=len(filas),
                )
            else:
                nota = "El modelo no pronostica ninguna subárea de este ámbito."
        return SerieDnsDTO(meses=meses, pronostico=pronostico, nota_pronostico=nota)


class ObtenerZonasDnsUseCase(_CasoDeUsoDns):
    """El indice lo calcula el modelo sobre todo el historico: solo respeta el ambito geografico."""

    def ejecutar(self, region: Optional[str], subarea: Optional[str]) -> ZonasDnsDTO:
        p = self._paquete()
        self._validar_ambito(p, region, subarea)
        ambito = analisis.codigos_del_ambito(p, FiltroDns(region=region, subarea=subarea))
        zonas = []
        for z in sorted(p.zonas, key=lambda z: z.ranking):
            if ambito is not None and z.codigo_subarea not in ambito:
                continue
            s = p.subarea(z.codigo_subarea)
            zonas.append(ZonaDTO(
                ranking=z.ranking, codigo=z.codigo_subarea, nombre=s.nombre, region=s.region,
                indice_priorizacion=z.indice_priorizacion, energia_total_gwh=_gwh(z.energia_total_kwh),
                n_eventos=z.n_eventos, pct_criticos=z.pct_criticos * 100, variacion_pct=z.variacion_pct,
            ))
        return ZonasDnsDTO(zonas=zonas)


class ObtenerPatronesDnsUseCase(_CasoDeUsoDns):
    def ejecutar(self, periodo_meses: int, region: Optional[str], subarea: Optional[str], origen: Optional[str]) -> PatronesDnsDTO:
        p = self._paquete()
        pat = analisis.patrones(p, self._filtro(p, periodo_meses, region, subarea, origen))
        franjas = []
        for franja, (no_prog, prog) in pat.origen_por_franja.items():
            total = no_prog + prog
            franjas.append(FranjaDTO(franja=franja, no_programada=no_prog, programada=prog,
                                     pct_no_programada=(no_prog / total * 100) if total else None))
        return PatronesDnsDTO(
            por_hora=pat.por_hora, dias=list(analisis.DIAS_SEMANA), por_dia_semana=pat.por_dia_semana,
            franjas=franjas, eventos_usados=pat.eventos_usados, eventos_hora_desconocida=pat.eventos_hora_desconocida,
        )


class ObtenerCausasDnsUseCase(_CasoDeUsoDns):
    def ejecutar(self, periodo_meses: int, region: Optional[str], subarea: Optional[str], origen: Optional[str]) -> CausasDnsDTO:
        p = self._paquete()
        c = analisis.causas(p, self._filtro(p, periodo_meses, region, subarea, origen))
        pct = (lambda n: n / c.total * 100) if c.total else (lambda n: 0.0)
        return CausasDnsDTO(
            total=c.total,
            causas=[CausaDTO(causa=n, eventos=e, energia_gwh=_gwh(en), pct_eventos=pct(e)) for n, e, en in c.por_causa],
            origen_de_la_causa=[ConteoDTO(nombre=n, eventos=e) for n, e in c.por_origen_de_la_causa],
            tipos_evento=[ConteoDTO(nombre=n, eventos=e) for n, e in c.por_tipo_evento],
            niveles_red=[ConteoDTO(nombre=n, eventos=e) for n, e in c.por_nivel_red],
        )


class ObtenerCambiosReporteDnsUseCase(_CasoDeUsoDns):
    def ejecutar(self, region: Optional[str], subarea: Optional[str]) -> CambiosReporteDTO:
        p = self._paquete()
        self._validar_ambito(p, region, subarea)
        ambito = analisis.codigos_del_ambito(p, FiltroDns(region=region, subarea=subarea))
        filas = []
        for c in sorted(p.cambios_reporte, key=lambda c: (c.periodo_quiebre, c.codigo_subarea)):
            if ambito is not None and c.codigo_subarea not in ambito:
                continue
            s = p.subarea(c.codigo_subarea)
            filas.append(CambioReporteDTO(
                codigo=c.codigo_subarea, nombre=s.nombre, region=s.region, periodo_quiebre=c.periodo_quiebre,
                direccion=c.direccion, pct_generica_antes=c.pct_generica_antes,
                pct_generica_despues=c.pct_generica_despues, pct_causa_conocida_antes=c.pct_causa_conocida_antes,
                pct_causa_conocida_despues=c.pct_causa_conocida_despues,
            ))
        return CambiosReporteDTO(cambios=filas)


class ObtenerModeloDnsUseCase(_CasoDeUsoDns):
    """Metricas del modelo (no cambian con los filtros) y pronostico por subarea (respeta el ambito)."""

    def ejecutar(self, region: Optional[str], subarea: Optional[str]) -> ModeloDnsDTO:
        p = self._paquete()
        self._validar_ambito(p, region, subarea)
        ambito = analisis.codigos_del_ambito(p, FiltroDns(region=region, subarea=subarea))

        persistencia = {}
        for m in p.metricas:
            variable, _, nombre = m.modelo.partition(" - ")
            if nombre.lower().startswith("persistencia"):
                persistencia[variable] = m.mae
        metricas = []
        for m in p.metricas:
            variable, _, nombre = m.modelo.partition(" - ")
            base = persistencia.get(variable)
            es_base = nombre.lower().startswith("persistencia")
            metricas.append(MetricaDTO(
                modelo=nombre or m.modelo, variable=variable, mae=m.mae, rmse=m.rmse,
                mejora_vs_persistencia_pct=None if es_base or not base else (base - m.mae) / base * 100,
            ))

        importancia = sorted(p.importancia, key=lambda i: -i.importancia_n_eventos)[:TOP_VARIABLES_IMPORTANCIA]
        pronostico = []
        for f in sorted(p.pronostico, key=lambda f: -f.energia_kwh):
            if ambito is not None and f.codigo_subarea not in ambito:
                continue
            s = p.subarea(f.codigo_subarea)
            pronostico.append(PronosticoSubareaDTO(codigo=f.codigo_subarea, nombre=s.nombre, region=s.region,
                                                   n_eventos=f.n_eventos, energia_gwh=_gwh(f.energia_kwh)))
        return ModeloDnsDTO(
            periodo_pronostico=p.periodo_pronostico, metricas=metricas,
            importancia=[ImportanciaDTO(variable=i.variable, importancia_n_eventos=i.importancia_n_eventos,
                                        importancia_energia_kwh=i.importancia_energia_kwh) for i in importancia],
            pronostico=pronostico,
        )
