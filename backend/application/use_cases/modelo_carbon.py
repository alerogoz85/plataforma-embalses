"""Casos de uso de lectura del modelo de carbon termico.

Cada consulta devuelve un DTO ya listo para la API. Los filtros (horizonte, ventana de
historia, dias de inventario) se aplican aqui, en el backend, para que todos los
tableros y gráficos reciban datos coherentes con los mismos filtros.
"""
from __future__ import annotations

from datetime import date

from application.dtos.modelo_carbon_dto import (
    BandaDTO,
    ComparacionXmDTO,
    CriterioDTO,
    EpisodioDTO,
    ErrorHorizonteDTO,
    HistoricoCarbonDTO,
    InventarioMensualDTO,
    InventarioPicoDTO,
    PicoCarbonDTO,
    ProyeccionCarbonDTO,
    PuntoCarbonDTO,
    ResumenCarbonDTO,
    SerieCarbonDTO,
    SupuestoDTO,
    TrimestreDTO,
    ValidacionCarbonDTO,
)
from domain.entities.modelo_carbon import PaqueteModeloCarbon, ProyeccionCarbonMensual
from domain.exceptions import ModeloCarbonNoCargadoError
from domain.repositories.modelo_carbon_repository import ModeloCarbonRepository
from domain.value_objects.banda import Banda

HORIZONTES_PERMITIDOS_MESES = (1, 3, 6, 9)  # el modelo proyecta como maximo 9 meses
HISTORIA_PERMITIDA_MESES = (0, 12, 36, 60)  # 0 = toda la historia (desde 2005)
DIAS_INVENTARIO_PERMITIDOS = (15, 30, 45, 60)


def _banda(b: Banda) -> BandaDTO:
    return BandaDTO(p10=round(b.p10, 3), p50=round(b.p50, 3), p90=round(b.p90, 3))


class _ConsultaCarbon:
    """Base de las consultas: obtiene la corrida vigente o falla con un error de dominio."""

    def __init__(self, repositorio: ModeloCarbonRepository) -> None:
        self._repositorio = repositorio

    def _paquete(self) -> PaqueteModeloCarbon:
        paquete = self._repositorio.obtener()
        if paquete is None:
            raise ModeloCarbonNoCargadoError()
        return paquete

    @staticmethod
    def _ventana(paquete: PaqueteModeloCarbon, horizonte_meses: int) -> list[ProyeccionCarbonMensual]:
        """Los primeros `horizonte_meses` meses de la proyeccion (o todos si hay menos)."""
        return sorted(paquete.proyeccion, key=lambda m: m.fecha)[:horizonte_meses]


class ObtenerResumenCarbonUseCase(_ConsultaCarbon):
    """Indicadores principales: pico de consumo, techo fisico, inventario y trimestres."""

    def ejecutar(self, horizonte_meses: int = 9, dias_inventario: int = 45) -> ResumenCarbonDTO:
        paquete = self._paquete()
        ventana = self._ventana(paquete, horizonte_meses)
        pico = max(ventana, key=lambda m: m.carbon_gbtu_dia.p50)
        inventario = next(
            (i for i in paquete.inventario if i.fecha == pico.fecha and i.dias_inventario == dias_inventario), None
        )
        meses_ventana = {m.fecha for m in ventana}
        record = paquete.maximo_mensual_historico
        ultimo = max(paquete.historico, key=lambda h: h.fecha)
        return ResumenCarbonDTO(
            origen=paquete.origen,
            poder_calorifico_mbtu_t=paquete.poder_calorifico_mbtu_t,
            techo_gbtu_dia=round(pico.techo_gbtu_dia, 2),
            maximo_historico=PuntoCarbonDTO(fecha=record.fecha, carbon_gbtu_dia=round(record.carbon_gbtu_dia, 2)),
            ultimo_observado=PuntoCarbonDTO(
                fecha=ultimo.fecha, carbon_gbtu_dia=round(ultimo.carbon_gbtu_dia, 2),
                mes_completo=ultimo.mes_completo, fuente=ultimo.fuente,
            ),
            horizonte_meses=len(ventana),
            pico=PicoCarbonDTO(
                fecha=pico.fecha, carbon_gbtu_dia=_banda(pico.carbon_gbtu_dia),
                uso_techo_p50_pct=round(pico.uso_techo_pct.p50, 2),
                prob_supera_maximo_pct=round(pico.prob_supera_maximo_pct, 2),
            ),
            inventario_pico=InventarioPicoDTO(
                fecha=inventario.fecha, dias_inventario=inventario.dias_inventario,
                kt_p50=round(inventario.kt_p50, 1), kt_p90=round(inventario.kt_p90, 1),
            ) if inventario else None,
            trimestres=[
                TrimestreDTO(
                    trimestre=t.trimestre, meses=t.meses, carbon_mt=_banda(t.carbon_mt),
                    dentro_del_horizonte=self._trimestre_completo(t.trimestre, meses_ventana),
                )
                for t in paquete.trimestres
            ],
            criterios_cumplidos=sum(c.cumple for c in paquete.veredicto),
            criterios_total=len(paquete.veredicto),
        )

    @staticmethod
    def _trimestre_completo(trimestre: str, meses_ventana: set[date]) -> bool:
        """'2026Q4' -> oct, nov y dic de 2026; esta dentro si los tres meses estan en la ventana."""
        anio, q = int(trimestre[:4]), int(trimestre[-1])
        return all(date(anio, 3 * (q - 1) + k, 1) in meses_ventana for k in (1, 2, 3))


class ObtenerSerieCarbonUseCase(_ConsultaCarbon):
    """Historia mensual del consumo y proyeccion (consumo, clima e hidrologia)."""

    def ejecutar(self, historia_meses: int = 36, horizonte_meses: int = 9) -> SerieCarbonDTO:
        paquete = self._paquete()
        historico = sorted(paquete.historico, key=lambda h: h.fecha)
        if historia_meses > 0:
            historico = historico[-historia_meses:]
        ventana = self._ventana(paquete, horizonte_meses)
        return SerieCarbonDTO(
            techo_gbtu_dia=round(ventana[0].techo_gbtu_dia, 2),
            maximo_historico_gbtu_dia=round(paquete.maximo_mensual_historico.carbon_gbtu_dia, 2),
            poder_calorifico_mbtu_t=paquete.poder_calorifico_mbtu_t,
            horizonte_meses=len(ventana),
            historico=[
                HistoricoCarbonDTO(
                    fecha=h.fecha, carbon_gbtu_dia=round(h.carbon_gbtu_dia, 3), techo_gbtu_dia=h.techo_gbtu_dia,
                    uso_techo_pct=h.uso_techo_pct, aportes_pct_media=h.aportes_pct_media, roni=h.roni,
                    fuente=h.fuente, mes_completo=h.mes_completo,
                )
                for h in historico
            ],
            proyeccion=[
                ProyeccionCarbonDTO(
                    fecha=m.fecha, dias=m.dias, roni=_banda(m.roni), aportes_pct_media=_banda(m.aportes_pct_media),
                    uso_techo_pct=_banda(m.uso_techo_pct), carbon_gbtu_dia=_banda(m.carbon_gbtu_dia),
                    carbon_kt_mes=_banda(m.carbon_kt_mes), prob_supera_maximo_pct=round(m.prob_supera_maximo_pct, 2),
                    observado_parcial_gbtu_dia=m.observado_parcial_gbtu_dia,
                )
                for m in ventana
            ],
        )


class ObtenerInventarioCarbonUseCase(_ConsultaCarbon):
    """Inventario de carbon que cubre N dias de consumo, mes a mes."""

    def ejecutar(self, dias_inventario: int = 45, horizonte_meses: int = 9) -> list[InventarioMensualDTO]:
        paquete = self._paquete()
        meses = {m.fecha for m in self._ventana(paquete, horizonte_meses)}
        return [
            InventarioMensualDTO(
                fecha=i.fecha, dias_inventario=i.dias_inventario, kt_p50=round(i.kt_p50, 1), kt_p90=round(i.kt_p90, 1)
            )
            for i in sorted(paquete.inventario, key=lambda i: i.fecha)
            if i.dias_inventario == dias_inventario and i.fecha in meses
        ]


class ObtenerComparacionXmUseCase(_ConsultaCarbon):
    """Proyeccion del modelo frente a la publicada por XM."""

    def ejecutar(self, horizonte_meses: int = 9) -> list[ComparacionXmDTO]:
        paquete = self._paquete()
        meses = {m.fecha for m in self._ventana(paquete, horizonte_meses)}
        return [
            ComparacionXmDTO(
                fecha=c.fecha, modelo=_banda(c.modelo), techo_gbtu_dia=round(c.techo_gbtu_dia, 2),
                xm_estocastico_gbtu_dia=c.xm_estocastico_gbtu_dia,
                xm_historicas_min_gbtu_dia=c.xm_historicas_min_gbtu_dia,
                xm_historicas_max_gbtu_dia=c.xm_historicas_max_gbtu_dia,
            )
            for c in sorted(paquete.comparacion_xm, key=lambda c: c.fecha)
            if c.fecha in meses
        ]


class ObtenerValidacionCarbonUseCase(_ConsultaCarbon):
    """Como se comporta el modelo fuera de muestra y que supuestos tiene."""

    def ejecutar(self) -> ValidacionCarbonDTO:
        paquete = self._paquete()
        return ValidacionCarbonDTO(
            errores_horizonte=[
                ErrorHorizonteDTO(**vars_dc(e)) for e in sorted(paquete.errores_horizonte, key=lambda e: e.horizonte_meses)
            ],
            episodios=[EpisodioDTO(**vars_dc(e)) for e in paquete.episodios],
            criterios_cumplidos=sum(c.cumple for c in paquete.veredicto),
            criterios_total=len(paquete.veredicto),
            veredicto=[CriterioDTO(**vars_dc(c)) for c in paquete.veredicto],
            supuestos=[SupuestoDTO(nombre=s.nombre, valor=s.valor) for s in paquete.supuestos],
        )


def vars_dc(objeto: object) -> dict:
    """Campos de un dataclass con `slots` (que no tiene __dict__) como diccionario."""
    return {campo: getattr(objeto, campo) for campo in objeto.__dataclass_fields__}  # type: ignore[attr-defined]
