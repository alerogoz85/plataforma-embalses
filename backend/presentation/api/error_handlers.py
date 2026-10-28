from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import (
    DatosHistoricosInsuficientesError,
    DomainError,
    EmbalseNoEncontradoError,
    FiltroInvalidoError,
    ModeloCarbonNoCargadoError,
    ModeloDnsNoCargadoError,
    AccesoDenegadoError,
    AlmacenamientoNoPersistenteError,
    CargaInvalidaError,
    CredencialesInvalidasError,
    CuentaBloqueadaError,
    EscenarioNoDisponibleError,
    SesionInvalidaError,
    TableroNoActualizableError,
    ModeloNoEncontradoError,
    SinMedicionesError,
)


def registrar_manejadores_excepciones(app: FastAPI) -> None:
    @app.exception_handler(EmbalseNoEncontradoError)
    async def _manejar_no_encontrado(request: Request, exc: EmbalseNoEncontradoError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(SinMedicionesError)
    async def _manejar_sin_mediciones(request: Request, exc: SinMedicionesError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(ModeloCarbonNoCargadoError)
    async def _manejar_modelo_carbon_no_cargado(request: Request, exc: ModeloCarbonNoCargadoError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(ModeloDnsNoCargadoError)
    async def _manejar_modelo_dns_no_cargado(request: Request, exc: ModeloDnsNoCargadoError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(ModeloNoEncontradoError)
    async def _manejar_modelo_no_encontrado(request: Request, exc: ModeloNoEncontradoError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(CredencialesInvalidasError)
    async def _manejar_credenciales(request: Request, exc: CredencialesInvalidasError):
        return JSONResponse(status_code=401, content={"detalle": str(exc)}, headers={"Cache-Control": "no-store"})

    @app.exception_handler(SesionInvalidaError)
    async def _manejar_sesion(request: Request, exc: SesionInvalidaError):
        return JSONResponse(status_code=401, content={"detalle": str(exc)}, headers={"Cache-Control": "no-store"})

    @app.exception_handler(AccesoDenegadoError)
    async def _manejar_acceso_denegado(request: Request, exc: AccesoDenegadoError):
        return JSONResponse(status_code=403, content={"detalle": str(exc)})

    @app.exception_handler(CuentaBloqueadaError)
    async def _manejar_cuenta_bloqueada(request: Request, exc: CuentaBloqueadaError):
        return JSONResponse(status_code=429, content={"detalle": str(exc)}, headers={"Retry-After": str(exc.minutos * 60)})

    @app.exception_handler(TableroNoActualizableError)
    async def _manejar_tablero_no_actualizable(request: Request, exc: TableroNoActualizableError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(CargaInvalidaError)
    async def _manejar_carga_invalida(request: Request, exc: CargaInvalidaError):
        return JSONResponse(status_code=422, content={"detalle": str(exc), "errores": exc.errores})

    @app.exception_handler(AlmacenamientoNoPersistenteError)
    async def _manejar_no_persistente(request: Request, exc: AlmacenamientoNoPersistenteError):
        return JSONResponse(status_code=503, content={"detalle": str(exc)})

    @app.exception_handler(EscenarioNoDisponibleError)
    async def _manejar_escenario_no_disponible(request: Request, exc: EscenarioNoDisponibleError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(FiltroInvalidoError)
    async def _manejar_filtro_invalido(request: Request, exc: FiltroInvalidoError):
        return JSONResponse(status_code=422, content={"detalle": str(exc)})

    @app.exception_handler(DatosHistoricosInsuficientesError)
    async def _manejar_datos_insuficientes(
        request: Request, exc: DatosHistoricosInsuficientesError
    ):
        return JSONResponse(status_code=422, content={"detalle": str(exc)})

    @app.exception_handler(DomainError)
    async def _manejar_error_dominio(request: Request, exc: DomainError):
        return JSONResponse(status_code=400, content={"detalle": str(exc)})
