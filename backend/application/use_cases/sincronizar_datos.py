from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from application.ports.output.fuente_mediciones_port import FuenteMedicionesPort
from domain.entities.metadatos_datos import MetadatosDatos
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.repositories.metadatos_repository import MetadatosRepository

# XM publica y luego revisa datos recientes: cada sincronizacion incremental
# vuelve a descargar los ultimos dias para recoger esas correcciones.
DIAS_REVISION = 7


@dataclass(frozen=True, slots=True)
class ResultadoSincronizacion:
    desde: date
    hasta: date
    embalses: int
    mediciones: int
    fecha_corte: Optional[date]


class SincronizarDatosUseCase:
    """Descarga embalses y mediciones desde una fuente externa y los guarda
    en los repositorios (upsert idempotente), registrando la procedencia."""

    def __init__(
        self,
        fuente: FuenteMedicionesPort,
        embalse_repository: EmbalseRepository,
        medicion_repository: MedicionRepository,
        metadatos_repository: MetadatosRepository,
    ) -> None:
        self._fuente = fuente
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository
        self._metadatos_repo = metadatos_repository

    def ejecutar(
        self,
        desde_por_defecto: date,
        desde: Optional[date] = None,
        hasta: Optional[date] = None,
    ) -> ResultadoSincronizacion:
        hasta = hasta or date.today()
        if desde is None:
            ultima = self._mediciones_repo.obtener_ultima_fecha()
            desde = ultima - timedelta(days=DIAS_REVISION) if ultima else desde_por_defecto

        descarga = self._fuente.descargar(desde, hasta)

        for embalse in descarga.embalses:
            self._embalses_repo.guardar(embalse)
        self._mediciones_repo.guardar_lote(descarga.mediciones)

        fecha_corte = self._mediciones_repo.obtener_ultima_fecha()
        if fecha_corte is not None:
            self._metadatos_repo.guardar(
                MetadatosDatos(
                    fuente=descarga.fuente,
                    descripcion=descarga.descripcion,
                    fecha_corte=fecha_corte,
                    actualizado_en=datetime.now(timezone.utc),
                    es_real=descarga.es_real,
                )
            )
        return ResultadoSincronizacion(
            desde=desde,
            hasta=hasta,
            embalses=len(descarga.embalses),
            mediciones=len(descarga.mediciones),
            fecha_corte=fecha_corte,
        )
