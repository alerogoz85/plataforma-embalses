"""Traduce entidades y value objects de dominio a DTOs de aplicacion."""
from __future__ import annotations

from typing import Optional

from application.dtos.embalse_dto import EmbalseDetalleDTO, EmbalseResumenDTO, SeriePuntoDTO
from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.services.autonomia_service import AutonomiaService
from domain.services.calculo_hidrico_service import CalculoHidricoService
from domain.value_objects.caudal import Caudal

_calculo = CalculoHidricoService()
_autonomia = AutonomiaService()


def _m3s(caudal: Optional[Caudal]) -> Optional[float]:
    return caudal.valor_m3s if caudal is not None else None


def a_resumen_dto(
    embalse: Embalse,
    medicion: MedicionHidrologica,
    medicion_anterior: Optional[MedicionHidrologica] = None,
    medicion_semana_anterior: Optional[MedicionHidrologica] = None,
) -> EmbalseResumenDTO:
    pct_actual = _calculo.calcular_porcentaje_volumen_util(medicion)

    delta_diario = 0.0
    if medicion_anterior is not None:
        pct_anterior = _calculo.calcular_porcentaje_volumen_util(medicion_anterior)
        delta_diario = _calculo.calcular_delta_porcentual(pct_actual, pct_anterior)

    delta_semanal = 0.0
    if medicion_semana_anterior is not None:
        pct_semana = _calculo.calcular_porcentaje_volumen_util(medicion_semana_anterior)
        delta_semanal = _calculo.calcular_delta_porcentual(pct_actual, pct_semana)

    return EmbalseResumenDTO(
        id=embalse.id,
        nombre=embalse.nombre,
        region=str(embalse.region),
        es_agregado=embalse.es_agregado,
        fecha=medicion.fecha,
        pct_volumen_util=pct_actual.valor,
        nivel_riesgo=pct_actual.nivel_riesgo.value,
        volumen_util_mm3=medicion.volumen_util.valor_mm3,
        capacidad_util_mm3=medicion.capacidad_util.valor_mm3,
        energia_util_gwh=medicion.energia_util_gwh,
        aportes_m3s=_m3s(medicion.aportes),
        aportes_pct_media=_calculo.calcular_aportes_pct_media(medicion),
        vertimientos_m3s=_m3s(medicion.vertimientos),
        turbinado_m3s=_m3s(medicion.turbinado),
        dias_autonomia=_autonomia.calcular_dias_autonomia(medicion),
        delta_diario_pct=delta_diario,
        delta_semanal_pct=delta_semanal,
    )


def a_serie_punto_dto(medicion: MedicionHidrologica) -> SeriePuntoDTO:
    return SeriePuntoDTO(
        fecha=medicion.fecha,
        pct_volumen_util=_calculo.calcular_porcentaje_volumen_util(medicion).valor,
        energia_util_gwh=medicion.energia_util_gwh,
        aportes_m3s=_m3s(medicion.aportes),
        aportes_pct_media=_calculo.calcular_aportes_pct_media(medicion),
        vertimientos_m3s=_m3s(medicion.vertimientos),
        turbinado_m3s=_m3s(medicion.turbinado),
    )


def a_detalle_dto(
    resumen: EmbalseResumenDTO, serie: list[MedicionHidrologica]
) -> EmbalseDetalleDTO:
    return EmbalseDetalleDTO(resumen=resumen, serie_historica=[a_serie_punto_dto(m) for m in serie])
