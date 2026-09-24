"""Importa la proyeccion de largo plazo del modelo de Outputs a la base local.

Uso (desde backend/, con el venv activo y `pip install -r requirements-dev.txt`):
    python -m infrastructure.ingesta.importar_proyeccion \\
        --xlsx "../../1. Modelo niveles de embalses/Datos/Outputs/proyeccion_montecarlo_enso 20260923.xlsx"

Reemplaza la proyeccion completa por la del archivo. Despues hay que volver a publicar
la API (scripts/desplegar-vercel.sh) para que la base desplegada la incluya.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from infrastructure.ingesta.proyeccion_outputs import leer_proyecciones
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_embalse_repository import DuckDBEmbalseRepository
from infrastructure.persistence.duckdb_proyeccion_senda_repository import (
    DuckDBProyeccionSendaRepository,
)

RUTA_BASE_DATOS_POR_DEFECTO = "../data/hidrologia.duckdb"
ID_TOTAL_NACIONAL = "TOTAL"


def _origen_por_defecto(ruta: Path) -> str:
    corrida = re.search(r"(\d{8})", ruta.stem)
    sufijo = f" · corrida {corrida.group(1)}" if corrida else ""
    return f"Prophet + XGBoost con escenarios ENSO (Monte Carlo, P10–P90){sufijo}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa la proyeccion de largo plazo (Outputs)")
    parser.add_argument("--xlsx", type=Path, required=True)
    parser.add_argument("--db-path", default=RUTA_BASE_DATOS_POR_DEFECTO)
    parser.add_argument("--origen", help="Texto que describe el modelo y la corrida")
    args = parser.parse_args()

    proyecciones = leer_proyecciones(args.xlsx, args.origen or _origen_por_defecto(args.xlsx))

    conexion = DuckDBConnection.obtener_instancia(args.db_path)
    conocidos = {e.id for e in DuckDBEmbalseRepository(conexion).listar()} | {ID_TOTAL_NACIONAL}
    desconocidos = sorted({p.embalse_id for p in proyecciones} - conocidos)
    if desconocidos:
        raise SystemExit(f"Embalses del archivo que no existen en la base: {', '.join(desconocidos)}")

    DuckDBProyeccionSendaRepository(conexion).reemplazar_todas(proyecciones)
    embalses = {p.embalse_id for p in proyecciones}
    meses = sorted({p.mes for p in proyecciones})
    print(
        f"Importadas {len(proyecciones)} proyecciones de {len(embalses)} series "
        f"({meses[0]:%Y-%m} a {meses[-1]:%Y-%m}). Origen: {proyecciones[0].origen}"
    )
    sin_proyeccion = sorted(conocidos - embalses)
    if sin_proyeccion:
        print(f"Sin proyeccion publicada (usaran el respaldo Holt-Winters): {', '.join(sin_proyeccion)}")


if __name__ == "__main__":
    main()
