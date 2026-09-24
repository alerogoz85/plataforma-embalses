from __future__ import annotations

from fastapi import APIRouter, Depends

from application.dtos.fuente_datos_dto import FuenteDatosDTO
from application.use_cases.obtener_fuente_datos import ObtenerFuenteDatosUseCase
from presentation.api.dependencies import obtener_fuente_datos_use_case

router = APIRouter(prefix="/api/v1/fuente-datos", tags=["fuente-datos"])


@router.get("", response_model=FuenteDatosDTO, summary="Procedencia y fecha de corte de los datos")
def obtener_fuente_datos(
    caso_de_uso: ObtenerFuenteDatosUseCase = Depends(obtener_fuente_datos_use_case),
) -> FuenteDatosDTO:
    return caso_de_uso.ejecutar()
