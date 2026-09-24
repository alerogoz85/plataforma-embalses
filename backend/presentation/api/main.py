"""Punto de entrada de la API REST. Ejecutar desde backend/:
    uvicorn presentation.api.main:app --reload --port 8000
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api.error_handlers import registrar_manejadores_excepciones
from presentation.api.routers.embalses_router import router as embalses_router
from presentation.api.routers.fuente_datos_router import router as fuente_datos_router
from presentation.api.routers.regiones_router import router as regiones_router
from presentation.api.routers.senda_volumen_router import router as senda_volumen_router

app = FastAPI(
    title="Plataforma de Monitoreo y Prediccion de Embalses",
    description=(
        "API REST para monitoreo hidrologico con datos publicos de XM/SIMEM: "
        "volumen y energia utiles, aportes, descargas y pronosticos de "
        "%V_util a 30/60/90 dias y a 6/12/18 meses por embalse y region."
    ),
    version="1.0.0",
)

origenes_permitidos = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

registrar_manejadores_excepciones(app)

app.include_router(embalses_router)
app.include_router(regiones_router)
app.include_router(senda_volumen_router)
app.include_router(fuente_datos_router)


@app.get("/api/v1/salud", tags=["salud"], summary="Health check")
def salud() -> dict:
    return {"estado": "ok"}
