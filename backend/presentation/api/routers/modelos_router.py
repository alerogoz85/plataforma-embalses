"""Endpoints de solo lectura de los modelos analiticos con ficha (/api/v1/modelos/{modelo_id}/*).

Seguridad: todos son GET; el identificador del modelo solo admite letras minusculas (largo acotado) y se
comprueba contra la lista cerrada de modelos (gas, optimizacion, apagon): cualquier otro responde 404.
El visor de apagon (/apagon/escenarios y /apagon/escenario) devuelve escenarios YA calculados por el modelo, uno por
combinacion de sus controles; los parametros se validan contra esas opciones cerradas (fuera de ellas, 422).
La API solo lee la base local y el catalogo de fichas; no ejecuta ningun modelo ni toca archivos."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query

from application.dtos.modelo_analitico_dto import CatalogoEscenariosDTO, EscenarioApagonDTO, FichaModeloDTO, ResultadosModeloDTO
from application.use_cases.modelo_analitico import (
    ObtenerCatalogoEscenariosApagonUseCase,
    ObtenerEscenarioApagonUseCase,
    ObtenerFichaModeloUseCase,
    ObtenerResultadosModeloUseCase,
)
from presentation.api.dependencies import (
    obtener_catalogo_escenarios_apagon_use_case,
    obtener_escenario_apagon_use_case,
    obtener_ficha_modelo_use_case,
    obtener_resultados_modelo_use_case,
)

router = APIRouter(prefix="/api/v1/modelos", tags=["modelos-analiticos"])

# Antes de las rutas /{modelo_id}/...: «apagon/escenarios» y «apagon/escenario» tienen su propio contrato.
@router.get("/apagon/escenarios", response_model=CatalogoEscenariosDTO, summary="Controles del visor de apagon y procedencia")
def obtener_catalogo_escenarios(
    caso_de_uso: ObtenerCatalogoEscenariosApagonUseCase = Depends(obtener_catalogo_escenarios_apagon_use_case),
) -> CatalogoEscenariosDTO:
    return caso_de_uso.ejecutar()


@router.get("/apagon/escenario", response_model=EscenarioApagonDTO, summary="Escenario del modelo de apagon para una combinacion de controles")
def obtener_escenario(
    modo: str = Query("manual", max_length=20, pattern=r"^[a-z]+$", description="probabilistico (pronostico ENOS) o manual (ONI elegido)"),
    oni: Optional[float] = Query(None, ge=-2.5, le=2.5, description="ONI objetivo en modo manual, de 0,1 en 0,1"),
    simulaciones: int = Query(2000, description="1000, 2000 o 5000"),
    horizonte: int = Query(18, description="12, 18 o 24 meses"),
    caso_de_uso: ObtenerEscenarioApagonUseCase = Depends(obtener_escenario_apagon_use_case),
) -> EscenarioApagonDTO:
    return caso_de_uso.ejecutar(modo, oni, simulaciones, horizonte)


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
