"""Punto de entrada de la API REST. Ejecutar desde backend/:
    uvicorn presentation.api.main:app --reload --port 8000
"""
from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from presentation.api.error_handlers import registrar_manejadores_excepciones
from presentation.api.routers.carbon_router import router as carbon_router
from presentation.api.routers.dns_router import router as dns_router
from presentation.api.routers.embalses_router import router as embalses_router
from presentation.api.routers.fuente_datos_router import router as fuente_datos_router
from presentation.api.routers.regiones_router import router as regiones_router
from presentation.api.routers.senda_volumen_router import router as senda_volumen_router

app = FastAPI(
    title="Plataforma de Tableros Analiticos",
    description=(
        "API REST de solo lectura de los tableros analiticos. Embalses: datos publicos de "
        "XM/SIMEM (volumen y energia utiles, aportes, descargas) y pronosticos de %V_util a 1, 3, "
        "6 y 12 meses por embalse y region. Carbon termico: proyeccion del consumo de carbon del "
        "SIN con escenarios ENOS, su validacion y la comparacion con XM."
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
app.include_router(carbon_router)
app.include_router(dns_router)


@app.get("/api/v1/salud", tags=["salud"], summary="Health check")
def salud() -> dict:
    return {"estado": "ok"}
