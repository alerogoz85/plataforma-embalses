from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from application.dtos.senda_volumen_dto import SendaVolumenDTO
from application.use_cases.obtener_senda_volumen import (
    ID_TOTAL_NACIONAL,
    ObtenerSendaVolumenUseCase,
)
from presentation.api.dependencies import obtener_senda_volumen_use_case

router = APIRouter(prefix="/api/v1/senda-volumen", tags=["senda-volumen"])

HORIZONTES_PERMITIDOS_MESES = {6, 12, 18}


@router.get(
    "",
    response_model=SendaVolumenDTO,
    summary="Senda mensual observada + proyectada de %V. util, con validacion walk-forward",
)
def obtener_senda_volumen(
    embalse: str = Query(
        default=ID_TOTAL_NACIONAL,
        description="Id de embalse, o 'TOTAL' para el agregado nacional ponderado",
    ),
    horizonte_meses: int = Query(default=12, description="Horizonte en meses (6, 12 o 18)"),
    caso_de_uso: ObtenerSendaVolumenUseCase = Depends(obtener_senda_volumen_use_case),
) -> SendaVolumenDTO:
    if horizonte_meses not in HORIZONTES_PERMITIDOS_MESES:
        raise HTTPException(status_code=422, detail="El horizonte debe ser 6, 12 o 18 meses")
    return caso_de_uso.ejecutar(embalse_id=embalse, horizonte_meses=horizonte_meses)
