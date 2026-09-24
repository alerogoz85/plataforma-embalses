from __future__ import annotations

from fastapi import APIRouter, Depends

from application.dtos.embalse_dto import RegionResumenDTO
from application.use_cases.obtener_resumen_nacional import ObtenerResumenNacionalUseCase
from presentation.api.dependencies import obtener_resumen_nacional_use_case

router = APIRouter(prefix="/api/v1/regiones", tags=["regiones"])


@router.get("", response_model=list[RegionResumenDTO], summary="Agregado por region hidrologica")
def listar_regiones(
    caso_de_uso: ObtenerResumenNacionalUseCase = Depends(obtener_resumen_nacional_use_case),
) -> list[RegionResumenDTO]:
    return caso_de_uso.ejecutar().regiones
