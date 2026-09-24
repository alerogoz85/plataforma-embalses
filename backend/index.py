"""Punto de entrada para Vercel (funcion Python con FastAPI).

En local se usa `uvicorn presentation.api.main:app`; este archivo solo existe
para el despliegue serverless.
"""
import os
from pathlib import Path

from presentation.api.arranque_vercel import preparar_base_en_tmp

if os.environ.get("VERCEL"):
    os.environ["HIDROLOGIA_DB_PATH"] = preparar_base_en_tmp(
        origen=Path(__file__).parent / "data" / "hidrologia.duckdb",
        destino=Path("/tmp/hidrologia.duckdb"),
    )

from presentation.api.main import app  # noqa: E402

__all__ = ["app"]
