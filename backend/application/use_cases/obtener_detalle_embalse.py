from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from application.dtos.embalse_dto import EmbalseDetalleDTO
from application.mappers import a_detalle_dto, a_resumen_dto
from application.series_agregadas import DIAS_VENTANA_DELTAS, SeriesAgregadas
from application.ports.input.use_case_ports import ObtenerDetalleEmbalsePort
from domain.exceptions import EmbalseNoEncontradoError, SinMedicionesError
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository

DIAS_HISTORICOS_POR_DEFECTO = 180


class ObtenerDetalleEmbalseUseCase(ObtenerDetalleEmbalsePort):
    """Recupera la ficha tecnica completa y la serie historica de un embalse."""

    def __init__(
        self,
        embalse_repository: EmbalseRepository,
        medicion_repository: MedicionRepository,
    ) -> None:
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository
        self._agregadas = SeriesAgregadas(embalse_repository, medicion_repository)

    def ejecutar(
        self,
        embalse_id: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> EmbalseDetalleDTO:
        grupo = self._agregadas.resolver(embalse_id)
        if grupo is not None:
            return self._detalle_agregado(grupo, fecha_inicio, fecha_fin)

        embalse = self._embalses_repo.obtener_por_id(embalse_id)
        if embalse is None:
            raise EmbalseNoEncontradoError(embalse_id)

        medicion_actual = self._mediciones_repo.obtener_ultima_medicion(embalse_id)
        if medicion_actual is None:
            raise SinMedicionesError(embalse_id)

        medicion_ayer = self._mediciones_repo.obtener_medicion_en_fecha(
            embalse_id, medicion_actual.fecha - timedelta(days=1)
        )
        medicion_semana = self._mediciones_repo.obtener_medicion_en_fecha(
            embalse_id, medicion_actual.fecha - timedelta(days=7)
        )
        resumen = a_resumen_dto(embalse, medicion_actual, medicion_ayer, medicion_semana)

        if fecha_inicio is None:
            fecha_inicio = medicion_actual.fecha - timedelta(days=DIAS_HISTORICOS_POR_DEFECTO)
        if fecha_fin is None:
            fecha_fin = medicion_actual.fecha

        serie = self._mediciones_repo.obtener_serie(embalse_id, fecha_inicio, fecha_fin)
        return a_detalle_dto(resumen, serie)

    def _detalle_agregado(
        self, grupo, fecha_inicio: Optional[date], fecha_fin: Optional[date]
    ) -> EmbalseDetalleDTO:
        """Ficha de 'Todos los embalses': el total nacional o una region."""
        ultima = self._mediciones_repo.obtener_ultima_fecha()
        if ultima is None or not grupo.embalses:
            raise SinMedicionesError(grupo.id)
        fin = fecha_fin or ultima
        inicio = fecha_inicio or fin - timedelta(days=DIAS_HISTORICOS_POR_DEFECTO)
        # Se lee una semana antes del inicio para poder calcular los deltas del resumen.
        ventana = self._agregadas.serie(grupo, inicio - timedelta(days=DIAS_VENTANA_DELTAS), fin)
        if not ventana:
            raise SinMedicionesError(grupo.id)
        return EmbalseDetalleDTO(
            resumen=self._agregadas.a_resumen_dto(grupo, ventana),
            serie_historica=self._agregadas.a_serie_dto([p for p in ventana if p.fecha >= inicio]),
        )
