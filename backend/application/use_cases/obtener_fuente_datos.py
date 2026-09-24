from __future__ import annotations

from application.dtos.fuente_datos_dto import FuenteDatosDTO
from domain.repositories.metadatos_repository import MetadatosRepository


class ObtenerFuenteDatosUseCase:
    """Informa de donde vienen los datos cargados y hasta que fecha llegan."""

    def __init__(self, metadatos_repository: MetadatosRepository) -> None:
        self._metadatos_repo = metadatos_repository

    def ejecutar(self) -> FuenteDatosDTO:
        metadatos = self._metadatos_repo.obtener()
        if metadatos is None:
            return FuenteDatosDTO(
                fuente="Sin datos",
                descripcion="La base aun no tiene datos; ejecuta la sincronizacion.",
                es_real=False,
            )
        return FuenteDatosDTO(
            fuente=metadatos.fuente,
            descripcion=metadatos.descripcion,
            es_real=metadatos.es_real,
            fecha_corte=metadatos.fecha_corte,
            actualizado_en=metadatos.actualizado_en,
        )
