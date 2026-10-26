"""Endpoints de solo lectura del modelo de demanda no atendida (/api/v1/dns/*).

Seguridad: todos son GET y la API solo lee de la base local. El periodo y el origen se validan
contra listas cerradas; la region y la subarea tienen largo y caracteres acotados y ademas se
comprueban contra el catalogo de la corrida cargada (si no existen responde 422). Las consultas
a la base usan parametros, nunca texto armado a mano."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from application.dtos.modelo_dns_dto import (
    CambiosReporteDTO,
    CatalogoDnsDTO,
    CausasDnsDTO,
    ModeloDnsDTO,
    PatronesDnsDTO,
    ResumenDnsDTO,
    SerieDnsDTO,
    ZonasDnsDTO,
)
from application.use_cases.modelo_dns import (
    ORIGENES_VALIDOS,
    PERIODOS_PERMITIDOS,
    ObtenerCambiosReporteDnsUseCase,
    ObtenerCatalogoDnsUseCase,
    ObtenerCausasDnsUseCase,
    ObtenerModeloDnsUseCase,
    ObtenerPatronesDnsUseCase,
    ObtenerResumenDnsUseCase,
    ObtenerSerieDnsUseCase,
    ObtenerZonasDnsUseCase,
)
from presentation.api.dependencies import (
    obtener_cambios_reporte_dns_use_case,
    obtener_catalogo_dns_use_case,
    obtener_causas_dns_use_case,
    obtener_modelo_dns_use_case,
    obtener_patrones_dns_use_case,
    obtener_resumen_dns_use_case,
    obtener_serie_dns_use_case,
    obtener_zonas_dns_use_case,
)

router = APIRouter(prefix="/api/v1/dns", tags=["demanda-no-atendida"])

_REGION = Query(default=None, max_length=40, description="Region (p. ej. Caribe); ver /dns/catalogo")
_SUBAREA = Query(default=None, max_length=20, pattern=r"^[A-Za-z0-9_]+$", description="Codigo de subarea (p. ej. Are0018)")


def _periodo(periodo_meses: int = Query(default=36, description="Meses de historia: 12, 36, 60 o 0 (todo)")) -> int:
    if periodo_meses not in PERIODOS_PERMITIDOS:
        opciones = ", ".join(str(p) for p in PERIODOS_PERMITIDOS)
        raise HTTPException(status_code=422, detail=f"El periodo (meses) debe ser uno de: {opciones}")
    return periodo_meses


def _origen(origen: Optional[str] = Query(default=None, description="programada o no_programada")) -> Optional[str]:
    if origen is not None and origen not in ORIGENES_VALIDOS:
        raise HTTPException(status_code=422, detail=f"El origen debe ser uno de: {', '.join(ORIGENES_VALIDOS)}")
    return origen


@router.get("/catalogo", response_model=CatalogoDnsDTO, summary="Regiones, subareas y fechas del modelo DNS")
def obtener_catalogo(caso_de_uso: ObtenerCatalogoDnsUseCase = Depends(obtener_catalogo_dns_use_case)) -> CatalogoDnsDTO:
    return caso_de_uso.ejecutar()


@router.get("/resumen", response_model=ResumenDnsDTO, summary="Indicadores de eventos y energia no atendida")
def obtener_resumen(
    periodo_meses: int = Depends(_periodo), origen: Optional[str] = Depends(_origen),
    region: Optional[str] = _REGION, subarea: Optional[str] = _SUBAREA,
    caso_de_uso: ObtenerResumenDnsUseCase = Depends(obtener_resumen_dns_use_case),
) -> ResumenDnsDTO:
    return caso_de_uso.ejecutar(periodo_meses, region, subarea, origen)


@router.get("/serie", response_model=SerieDnsDTO, summary="Serie mensual de eventos y energia, con el pronostico")
def obtener_serie(
    periodo_meses: int = Depends(_periodo), origen: Optional[str] = Depends(_origen),
    region: Optional[str] = _REGION, subarea: Optional[str] = _SUBAREA,
    caso_de_uso: ObtenerSerieDnsUseCase = Depends(obtener_serie_dns_use_case),
) -> SerieDnsDTO:
    return caso_de_uso.ejecutar(periodo_meses, region, subarea, origen)


@router.get("/zonas", response_model=ZonasDnsDTO, summary="Indice de priorizacion de zonas")
def obtener_zonas(
    region: Optional[str] = _REGION, subarea: Optional[str] = _SUBAREA,
    caso_de_uso: ObtenerZonasDnsUseCase = Depends(obtener_zonas_dns_use_case),
) -> ZonasDnsDTO:
    return caso_de_uso.ejecutar(region, subarea)


@router.get("/patrones", response_model=PatronesDnsDTO, summary="Eventos por hora, dia de la semana y franja")
def obtener_patrones(
    periodo_meses: int = Depends(_periodo), origen: Optional[str] = Depends(_origen),
    region: Optional[str] = _REGION, subarea: Optional[str] = _SUBAREA,
    caso_de_uso: ObtenerPatronesDnsUseCase = Depends(obtener_patrones_dns_use_case),
) -> PatronesDnsDTO:
    return caso_de_uso.ejecutar(periodo_meses, region, subarea, origen)


@router.get("/causas", response_model=CausasDnsDTO, summary="Causas de los eventos")
def obtener_causas(
    periodo_meses: int = Depends(_periodo), origen: Optional[str] = Depends(_origen),
    region: Optional[str] = _REGION, subarea: Optional[str] = _SUBAREA,
    caso_de_uso: ObtenerCausasDnsUseCase = Depends(obtener_causas_dns_use_case),
) -> CausasDnsDTO:
    return caso_de_uso.ejecutar(periodo_meses, region, subarea, origen)


@router.get("/cambios-reporte", response_model=CambiosReporteDTO, summary="Cambios en la forma de reportar")
def obtener_cambios_reporte(
    region: Optional[str] = _REGION, subarea: Optional[str] = _SUBAREA,
    caso_de_uso: ObtenerCambiosReporteDnsUseCase = Depends(obtener_cambios_reporte_dns_use_case),
) -> CambiosReporteDTO:
    return caso_de_uso.ejecutar(region, subarea)


@router.get("/modelo", response_model=ModeloDnsDTO, summary="Metricas del modelo predictivo y pronostico por subarea")
def obtener_modelo(
    region: Optional[str] = _REGION, subarea: Optional[str] = _SUBAREA,
    caso_de_uso: ObtenerModeloDnsUseCase = Depends(obtener_modelo_dns_use_case),
) -> ModeloDnsDTO:
    return caso_de_uso.ejecutar(region, subarea)
