"""Endpoints de solo lectura de los modelos analiticos con ficha (/api/v1/modelos/{modelo_id}/*).

Seguridad: todos son GET; el identificador del modelo solo admite letras minusculas (largo acotado) y se
comprueba contra la lista cerrada de modelos (gas, optimizacion, apagon): cualquier otro responde 404.
La API solo lee la base local y el catalogo de fichas; no ejecuta ningun modelo ni toca archivos."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from application.dtos.modelo_analitico_dto import FichaModeloDTO, ResultadosModeloDTO
from application.use_cases.modelo_analitico import ObtenerFichaModeloUseCase, ObtenerResultadosModeloUseCase
from presentation.api.dependencies import obtener_ficha_modelo_use_case, obtener_resultados_modelo_use_case

router = APIRouter(prefix="/api/v1/modelos", tags=["modelos-analiticos"])

_MODELO = Path(max_length=20, pattern=r"^[a-z]+$", description="gas, optimizacion o apagon")


@router.get("/{modelo_id}/ficha", response_model=FichaModeloDTO, summary="Ficha documentada del modelo")
def obtener_ficha(
    modelo_id: str = _MODELO, caso_de_uso: ObtenerFichaModeloUseCase = Depends(obtener_ficha_modelo_use_case)
) -> FichaModeloDTO:
    return caso_de_uso.ejecutar(modelo_id)


@router.get("/{modelo_id}/resultados", response_model=ResultadosModeloDTO, summary="Resultados importados del modelo")
def obtener_resultados(
    modelo_id: str = _MODELO, caso_de_uso: ObtenerResultadosModeloUseCase = Depends(obtener_resultados_modelo_use_case)
) -> ResultadosModeloDTO:
    return caso_de_uso.ejecutar(modelo_id)
