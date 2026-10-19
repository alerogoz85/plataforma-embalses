"""Endpoints de solo lectura del modelo de carbon termico (/api/v1/carbon/*).

Seguridad: todos son GET, no reciben texto libre (cada parametro se valida contra una
lista cerrada de valores) y la API solo lee de la base local; no consulta servicios
externos ni escribe nada."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from application.dtos.modelo_carbon_dto import (
    ComparacionXmDTO,
    InventarioMensualDTO,
    ResumenCarbonDTO,
    SerieCarbonDTO,
    ValidacionCarbonDTO,
)
from application.use_cases.modelo_carbon import (
    DIAS_INVENTARIO_PERMITIDOS,
    HISTORIA_PERMITIDA_MESES,
    HORIZONTES_PERMITIDOS_MESES,
    ObtenerComparacionXmUseCase,
    ObtenerInventarioCarbonUseCase,
    ObtenerResumenCarbonUseCase,
    ObtenerSerieCarbonUseCase,
    ObtenerValidacionCarbonUseCase,
)
from presentation.api.dependencies import (
    obtener_comparacion_xm_use_case,
    obtener_inventario_carbon_use_case,
    obtener_resumen_carbon_use_case,
    obtener_serie_carbon_use_case,
    obtener_validacion_carbon_use_case,
)

router = APIRouter(prefix="/api/v1/carbon", tags=["carbon-termico"])


def _validar(valor: int, permitidos: tuple[int, ...], nombre: str) -> int:
    if valor not in permitidos:
        opciones = ", ".join(str(p) for p in permitidos)
        raise HTTPException(status_code=422, detail=f"{nombre} debe ser uno de: {opciones}")
    return valor


def _horizonte(horizonte_meses: int = Query(default=9, description="Meses proyectados: 1, 3, 6 o 9")) -> int:
    return _validar(horizonte_meses, HORIZONTES_PERMITIDOS_MESES, "El horizonte (meses)")


def _dias(dias: int = Query(default=45, description="Dias de inventario: 15, 30, 45 o 60")) -> int:
    return _validar(dias, DIAS_INVENTARIO_PERMITIDOS, "Los dias de inventario")


@router.get("/resumen", response_model=ResumenCarbonDTO, summary="Indicadores del modelo de carbon termico")
def obtener_resumen(
    horizonte_meses: int = Depends(_horizonte),
    dias: int = Depends(_dias),
    caso_de_uso: ObtenerResumenCarbonUseCase = Depends(obtener_resumen_carbon_use_case),
) -> ResumenCarbonDTO:
    return caso_de_uso.ejecutar(horizonte_meses=horizonte_meses, dias_inventario=dias)


@router.get("/serie", response_model=SerieCarbonDTO, summary="Historia mensual y proyeccion del consumo de carbon")
def obtener_serie(
    horizonte_meses: int = Depends(_horizonte),
    historia_meses: int = Query(default=36, description="Meses de historia: 12, 36, 60 o 0 (toda)"),
    caso_de_uso: ObtenerSerieCarbonUseCase = Depends(obtener_serie_carbon_use_case),
) -> SerieCarbonDTO:
    _validar(historia_meses, HISTORIA_PERMITIDA_MESES, "La historia (meses)")
    return caso_de_uso.ejecutar(historia_meses=historia_meses, horizonte_meses=horizonte_meses)


@router.get("/inventario", response_model=list[InventarioMensualDTO], summary="Inventario de carbon requerido")
def obtener_inventario(
    horizonte_meses: int = Depends(_horizonte),
    dias: int = Depends(_dias),
    caso_de_uso: ObtenerInventarioCarbonUseCase = Depends(obtener_inventario_carbon_use_case),
) -> list[InventarioMensualDTO]:
    return caso_de_uso.ejecutar(dias_inventario=dias, horizonte_meses=horizonte_meses)


@router.get("/comparacion-xm", response_model=list[ComparacionXmDTO], summary="Modelo frente a la proyeccion de XM")
def obtener_comparacion_xm(
    horizonte_meses: int = Depends(_horizonte),
    caso_de_uso: ObtenerComparacionXmUseCase = Depends(obtener_comparacion_xm_use_case),
) -> list[ComparacionXmDTO]:
    return caso_de_uso.ejecutar(horizonte_meses=horizonte_meses)


@router.get("/validacion", response_model=ValidacionCarbonDTO, summary="Validacion y supuestos del modelo")
def obtener_validacion(
    caso_de_uso: ObtenerValidacionCarbonUseCase = Depends(obtener_validacion_carbon_use_case),
) -> ValidacionCarbonDTO:
    return caso_de_uso.ejecutar()
