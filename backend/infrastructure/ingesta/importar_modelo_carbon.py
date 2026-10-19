"""Importa la corrida vigente del modelo de carbon termico a la base local.

Uso (desde backend/, con el venv activo y `pip install -r requirements-dev.txt`):
    python -m infrastructure.ingesta.importar_modelo_carbon \\
        --carpeta "../../Modelo de carbón térmico"

La carpeta es la del proyecto del modelo (contiene `resultados/` y `datos/`). Reemplaza la
corrida anterior por completo, valida los archivos antes de escribir y no se borra con
`sincronizar --reiniciar`. Despues hay que volver a publicar la API
(`scripts/desplegar-vercel.sh`) para que la base desplegada la incluya.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.ingesta.modelo_carbon_archivos import (
    ArchivoModeloCarbonInvalidoError,
    leer_modelo_carbon,
)
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_modelo_carbon_repository import DuckDBModeloCarbonRepository

RUTA_BASE_DATOS_POR_DEFECTO = "../data/hidrologia.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa el modelo de carbon termico")
    parser.add_argument("--carpeta", type=Path, required=True, help="Carpeta del proyecto del modelo")
    parser.add_argument("--db-path", default=RUTA_BASE_DATOS_POR_DEFECTO)
    args = parser.parse_args()

    try:
        paquete = leer_modelo_carbon(args.carpeta)
    except ArchivoModeloCarbonInvalidoError as error:
        raise SystemExit(f"No se importo nada: {error}") from error

    repositorio = DuckDBModeloCarbonRepository(DuckDBConnection.obtener_instancia(args.db_path))
    repositorio.reemplazar(paquete)

    primero, ultimo = paquete.proyeccion[0].fecha, paquete.proyeccion[-1].fecha
    print(
        f"Importado: {len(paquete.historico)} meses de historia, proyeccion {primero:%Y-%m} a {ultimo:%Y-%m}, "
        f"{len(paquete.trimestres)} trimestres, {len(paquete.inventario)} filas de inventario, "
        f"{len(paquete.comparacion_xm)} meses de comparacion con XM, {len(paquete.errores_horizonte)} horizontes "
        f"de error, {len(paquete.episodios)} episodios y {len(paquete.veredicto)} criterios de validez."
    )


if __name__ == "__main__":
    main()
