"""Preparacion de la base de datos para funciones serverless (Vercel).

El sistema de archivos de una funcion es de solo lectura salvo /tmp, y la
aplicacion abre DuckDB en lectura/escritura (crea las tablas si faltan). Por
eso la base empaquetada con el despliegue se copia una vez a /tmp al arrancar.
"""
from __future__ import annotations

import shutil
from pathlib import Path


def preparar_base_en_tmp(origen: Path, destino: Path) -> str:
    """Copia la base empaquetada a `destino` (si aun no esta) y devuelve su ruta."""
    if not origen.is_file():
        raise FileNotFoundError(
            f"No se encontro la base empaquetada en {origen}; el despliegue debe incluir data/hidrologia.duckdb"
        )
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origen, destino)
    return str(destino)
