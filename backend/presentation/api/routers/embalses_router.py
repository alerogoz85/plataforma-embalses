from __future__ import annotations

import csv
import io
from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from application.dtos.embalse_dto import EmbalseDetalleDTO, ResumenNacionalDTO
from application.dtos.prediccion_dto import PrediccionDTO
from application.use_cases.generar_prediccion import GenerarPrediccionUseCase
from application.use_cases.listar_embalses import ListarEmbalsesUseCase
from application.use_cases.obtener_detalle_embalse import ObtenerDetalleEmbalseUseCase
from application.use_cases.obtener_resumen_nacional import ObtenerResumenNacionalUseCase
from presentation.api.dependencies import (
    obtener_detalle_embalse_use_case,
    obtener_generar_prediccion_use_case,
    obtener_listar_embalses_use_case,
    obtener_resumen_nacional_use_case,
)

router = APIRouter(prefix="/api/v1/embalses", tags=["embalses"])

# 1, 3, 6 y 12 meses, con el mes comercial de 30 dias.
HORIZONTES_PERMITIDOS = {30, 90, 180, 360}


@router.get("/resumen", response_model=ResumenNacionalDTO, summary="Panorama nacional agregado")
def obtener_resumen_nacional(
    region: Optional[list[str]] = Query(default=None, description="Filtrar por region(es)"),
    embalse: Optional[list[str]] = Query(default=None, description="Filtrar por id de embalse"),
    fecha: Optional[date] = Query(default=None, description="Fecha de corte (por defecto, hoy)"),
    caso_de_uso: ObtenerResumenNacionalUseCase = Depends(obtener_resumen_nacional_use_case),
) -> ResumenNacionalDTO:
    return caso_de_uso.ejecutar(regiones=region, embalses=embalse, fecha=fecha)


@router.get("", response_model=list[EmbalseDetalleDTO], summary="Listado de embalses")
def listar_embalses(
    region: Optional[str] = Query(default=None),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    caso_de_uso: ListarEmbalsesUseCase = Depends(obtener_listar_embalses_use_case),
) -> list[EmbalseDetalleDTO]:
    return caso_de_uso.ejecutar(region=region, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@router.get("/{embalse_id}", response_model=EmbalseDetalleDTO, summary="Detalle de un embalse")
def obtener_detalle_embalse(
    embalse_id: str,
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    caso_de_uso: ObtenerDetalleEmbalseUseCase = Depends(obtener_detalle_embalse_use_case),
) -> EmbalseDetalleDTO:
    return caso_de_uso.ejecutar(embalse_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@router.get(
    "/{embalse_id}/prediccion",
    response_model=PrediccionDTO,
    summary="Pronostico de %V_util a 1, 3, 6 o 12 meses (30, 90, 180 o 360 dias)",
)
def generar_prediccion(
    embalse_id: str,
    horizonte: int = Query(default=30, description="Horizonte en dias: 30, 90, 180 o 360 (1, 3, 6 o 12 meses)"),
    caso_de_uso: GenerarPrediccionUseCase = Depends(obtener_generar_prediccion_use_case),
) -> PrediccionDTO:
    if horizonte not in HORIZONTES_PERMITIDOS:
        raise HTTPException(status_code=422, detail="El horizonte debe ser 30, 90, 180 o 360 dias (1, 3, 6 o 12 meses)")
    return caso_de_uso.ejecutar(embalse_id, horizonte_dias=horizonte)


@router.get("/{embalse_id}/reporte", summary="Descarga de serie historica (CSV o JSON)")
def descargar_reporte(
    embalse_id: str,
    formato: Literal["csv", "json"] = Query(default="csv"),
    fecha_inicio: Optional[date] = Query(default=None),
    fecha_fin: Optional[date] = Query(default=None),
    caso_de_uso: ObtenerDetalleEmbalseUseCase = Depends(obtener_detalle_embalse_use_case),
):
    detalle = caso_de_uso.ejecutar(embalse_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)

    if formato == "json":
        contenido = detalle.model_dump_json(indent=2)
        return StreamingResponse(
            io.BytesIO(contenido.encode("utf-8")),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{embalse_id}_reporte.json"'
            },
        )

    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(
        ["fecha", "pct_volumen_util", "energia_util_gwh", "aportes_m3s", "aportes_pct_media",
         "vertimientos_m3s", "turbinado_m3s"]
    )
    for punto in detalle.serie_historica:
        escritor.writerow(
            [punto.fecha, punto.pct_volumen_util, punto.energia_util_gwh, punto.aportes_m3s,
             punto.aportes_pct_media, punto.vertimientos_m3s, punto.turbinado_m3s]
        )

    return StreamingResponse(
        io.BytesIO(buffer.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{embalse_id}_reporte.csv"'},
    )
