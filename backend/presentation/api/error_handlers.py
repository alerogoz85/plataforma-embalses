from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from domain.exceptions import (
    DatosHistoricosInsuficientesError,
    DomainError,
    EmbalseNoEncontradoError,
    SinMedicionesError,
)


def registrar_manejadores_excepciones(app: FastAPI) -> None:
    @app.exception_handler(EmbalseNoEncontradoError)
    async def _manejar_no_encontrado(request: Request, exc: EmbalseNoEncontradoError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(SinMedicionesError)
    async def _manejar_sin_mediciones(request: Request, exc: SinMedicionesError):
        return JSONResponse(status_code=404, content={"detalle": str(exc)})

    @app.exception_handler(DatosHistoricosInsuficientesError)
    async def _manejar_datos_insuficientes(
        request: Request, exc: DatosHistoricosInsuficientesError
    ):
        return JSONResponse(status_code=422, content={"detalle": str(exc)})

    @app.exception_handler(DomainError)
    async def _manejar_error_dominio(request: Request, exc: DomainError):
        return JSONResponse(status_code=400, content={"detalle": str(exc)})
