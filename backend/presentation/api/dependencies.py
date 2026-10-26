"""Composition root: aqui, y solo aqui, se conectan los adaptadores
concretos de infraestructura con los puertos que espera la aplicacion."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from application.ports.output.forecasting_port import ForecastingPort
from application.use_cases.generar_prediccion import GenerarPrediccionUseCase
from application.use_cases.listar_embalses import ListarEmbalsesUseCase
from application.use_cases.modelo_dns import (
    ObtenerCambiosReporteDnsUseCase,
    ObtenerCatalogoDnsUseCase,
    ObtenerCausasDnsUseCase,
    ObtenerModeloDnsUseCase,
    ObtenerPatronesDnsUseCase,
    ObtenerResumenDnsUseCase,
    ObtenerSerieDnsUseCase,
    ObtenerZonasDnsUseCase,
)
from application.use_cases.modelo_carbon import (
    ObtenerComparacionXmUseCase,
    ObtenerInventarioCarbonUseCase,
    ObtenerResumenCarbonUseCase,
    ObtenerSerieCarbonUseCase,
    ObtenerValidacionCarbonUseCase,
)
from application.use_cases.obtener_detalle_embalse import ObtenerDetalleEmbalseUseCase
from application.use_cases.obtener_fuente_datos import ObtenerFuenteDatosUseCase
from application.use_cases.obtener_resumen_nacional import ObtenerResumenNacionalUseCase
from application.use_cases.obtener_senda_volumen import ObtenerSendaVolumenUseCase
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.repositories.metadatos_repository import MetadatosRepository
from domain.repositories.modelo_carbon_repository import ModeloCarbonRepository
from domain.repositories.modelo_dns_repository import ModeloDnsRepository
from domain.repositories.proyeccion_senda_repository import ProyeccionSendaRepository
from infrastructure.ml.holt_winters_forecasting_service import HoltWintersForecastingService
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_embalse_repository import DuckDBEmbalseRepository
from infrastructure.persistence.duckdb_medicion_repository import DuckDBMedicionRepository
from infrastructure.persistence.duckdb_metadatos_repository import DuckDBMetadatosRepository
from infrastructure.persistence.duckdb_modelo_carbon_repository import DuckDBModeloCarbonRepository
from infrastructure.persistence.duckdb_modelo_dns_repository import DuckDBModeloDnsRepository
from infrastructure.persistence.duckdb_proyeccion_senda_repository import DuckDBProyeccionSendaRepository

_RUTA_BACKEND = Path(__file__).resolve().parents[2]
_RUTA_DB_POR_DEFECTO = _RUTA_BACKEND.parent / "data" / "hidrologia.duckdb"


@lru_cache
def obtener_ruta_base_datos() -> str:
    return os.environ.get("HIDROLOGIA_DB_PATH", str(_RUTA_DB_POR_DEFECTO))


@lru_cache
def obtener_conexion() -> DuckDBConnection:
    return DuckDBConnection.obtener_instancia(obtener_ruta_base_datos())


@lru_cache
def obtener_embalse_repository() -> EmbalseRepository:
    return DuckDBEmbalseRepository(obtener_conexion())


@lru_cache
def obtener_medicion_repository() -> MedicionRepository:
    return DuckDBMedicionRepository(obtener_conexion())


@lru_cache
def obtener_metadatos_repository() -> MetadatosRepository:
    return DuckDBMetadatosRepository(obtener_conexion())


@lru_cache
def obtener_proyeccion_senda_repository() -> ProyeccionSendaRepository:
    return DuckDBProyeccionSendaRepository(obtener_conexion())


@lru_cache
def obtener_forecasting_service() -> ForecastingPort:
    return HoltWintersForecastingService()


@lru_cache
def obtener_forecasting_service_mensual() -> ForecastingPort:
    """Variante con estacionalidad anual (12 meses), usada por la senda de
    volumen para reproducir el ciclo hidrologico seco/lluvioso en vez de
    solo extrapolar la tendencia reciente."""
    return HoltWintersForecastingService(estacional=True, periodos_estacionales=12)


@lru_cache
def obtener_resumen_nacional_use_case() -> ObtenerResumenNacionalUseCase:
    return ObtenerResumenNacionalUseCase(
        obtener_embalse_repository(), obtener_medicion_repository()
    )


@lru_cache
def obtener_listar_embalses_use_case() -> ListarEmbalsesUseCase:
    return ListarEmbalsesUseCase(obtener_embalse_repository(), obtener_medicion_repository())


@lru_cache
def obtener_detalle_embalse_use_case() -> ObtenerDetalleEmbalseUseCase:
    return ObtenerDetalleEmbalseUseCase(
        obtener_embalse_repository(), obtener_medicion_repository()
    )


@lru_cache
def obtener_generar_prediccion_use_case() -> GenerarPrediccionUseCase:
    return GenerarPrediccionUseCase(
        obtener_embalse_repository(),
        obtener_medicion_repository(),
        obtener_forecasting_service(),
        obtener_proyeccion_senda_repository(),
    )


@lru_cache
def obtener_senda_volumen_use_case() -> ObtenerSendaVolumenUseCase:
    return ObtenerSendaVolumenUseCase(
        obtener_embalse_repository(),
        obtener_medicion_repository(),
        obtener_forecasting_service_mensual(),
        obtener_proyeccion_senda_repository(),
    )


@lru_cache
def obtener_fuente_datos_use_case() -> ObtenerFuenteDatosUseCase:
    return ObtenerFuenteDatosUseCase(obtener_metadatos_repository())


# --- Modelo de carbon termico -------------------------------------------------
@lru_cache
def obtener_modelo_carbon_repository() -> ModeloCarbonRepository:
    return DuckDBModeloCarbonRepository(obtener_conexion())


@lru_cache
def obtener_resumen_carbon_use_case() -> ObtenerResumenCarbonUseCase:
    return ObtenerResumenCarbonUseCase(obtener_modelo_carbon_repository())


@lru_cache
def obtener_serie_carbon_use_case() -> ObtenerSerieCarbonUseCase:
    return ObtenerSerieCarbonUseCase(obtener_modelo_carbon_repository())


@lru_cache
def obtener_inventario_carbon_use_case() -> ObtenerInventarioCarbonUseCase:
    return ObtenerInventarioCarbonUseCase(obtener_modelo_carbon_repository())


@lru_cache
def obtener_comparacion_xm_use_case() -> ObtenerComparacionXmUseCase:
    return ObtenerComparacionXmUseCase(obtener_modelo_carbon_repository())


@lru_cache
def obtener_validacion_carbon_use_case() -> ObtenerValidacionCarbonUseCase:
    return ObtenerValidacionCarbonUseCase(obtener_modelo_carbon_repository())


# --- Modelo de demanda no atendida (DNS) --------------------------------------
@lru_cache
def obtener_modelo_dns_repository() -> ModeloDnsRepository:
    return DuckDBModeloDnsRepository(obtener_conexion())


@lru_cache
def obtener_catalogo_dns_use_case() -> ObtenerCatalogoDnsUseCase:
    return ObtenerCatalogoDnsUseCase(obtener_modelo_dns_repository())


@lru_cache
def obtener_resumen_dns_use_case() -> ObtenerResumenDnsUseCase:
    return ObtenerResumenDnsUseCase(obtener_modelo_dns_repository())


@lru_cache
def obtener_serie_dns_use_case() -> ObtenerSerieDnsUseCase:
    return ObtenerSerieDnsUseCase(obtener_modelo_dns_repository())


@lru_cache
def obtener_zonas_dns_use_case() -> ObtenerZonasDnsUseCase:
    return ObtenerZonasDnsUseCase(obtener_modelo_dns_repository())


@lru_cache
def obtener_patrones_dns_use_case() -> ObtenerPatronesDnsUseCase:
    return ObtenerPatronesDnsUseCase(obtener_modelo_dns_repository())


@lru_cache
def obtener_causas_dns_use_case() -> ObtenerCausasDnsUseCase:
    return ObtenerCausasDnsUseCase(obtener_modelo_dns_repository())


@lru_cache
def obtener_cambios_reporte_dns_use_case() -> ObtenerCambiosReporteDnsUseCase:
    return ObtenerCambiosReporteDnsUseCase(obtener_modelo_dns_repository())


@lru_cache
def obtener_modelo_dns_use_case() -> ObtenerModeloDnsUseCase:
    return ObtenerModeloDnsUseCase(obtener_modelo_dns_repository())
