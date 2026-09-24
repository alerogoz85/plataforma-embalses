from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from application.dtos.embalse_dto import EmbalseDetalleDTO
from application.mappers import a_detalle_dto, a_resumen_dto
from application.ports.input.use_case_ports import ListarEmbalsesPort
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository


class ListarEmbalsesUseCase(ListarEmbalsesPort):
    """Lista embalses con su ficha resumida y, si se solicita un rango de
    fechas, la serie historica correspondiente para la tabla interactiva."""

    def __init__(
        self,
        embalse_repository: EmbalseRepository,
        medicion_repository: MedicionRepository,
    ) -> None:
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository

    def ejecutar(
        self,
        region: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> list[EmbalseDetalleDTO]:
        nombre_region = None
        if region:
            from domain.entities.region import NombreRegion

            try:
                nombre_region = NombreRegion(region)
            except ValueError:
                nombre_region = None

        embalses = self._embalses_repo.listar(region=nombre_region)

        detalles = []
        for embalse in embalses:
            medicion_actual = self._mediciones_repo.obtener_ultima_medicion(embalse.id)
            if medicion_actual is None:
                continue

            medicion_ayer = self._mediciones_repo.obtener_medicion_en_fecha(
                embalse.id, medicion_actual.fecha - timedelta(days=1)
            )
            medicion_semana = self._mediciones_repo.obtener_medicion_en_fecha(
                embalse.id, medicion_actual.fecha - timedelta(days=7)
            )
            resumen = a_resumen_dto(embalse, medicion_actual, medicion_ayer, medicion_semana)

            serie = []
            if fecha_inicio or fecha_fin:
                serie = self._mediciones_repo.obtener_serie(
                    embalse.id, fecha_inicio, fecha_fin
                )

            detalles.append(a_detalle_dto(resumen, serie))

        return detalles
