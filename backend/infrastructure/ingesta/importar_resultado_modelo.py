"""Importa el resultado de un modelo analitico (gas, optimizacion o apagon) a la base local.

Uso (desde backend/, con el venv activo y `pip install -r requirements-dev.txt`):
    python -m infrastructure.ingesta.importar_resultado_modelo --modelo apagon --carpeta "../../5. Modelo apagón/Scripts"

El comando exacto de cada modelo y los archivos que lee estan en su ficha (pestaña del tablero).
Valida los archivos antes de escribir, reemplaza solo el resultado de ESE modelo y no se borra con
`sincronizar --reiniciar`. Despues hay que volver a publicar la API (`scripts/desplegar-vercel.sh`)."""
from __future__ import annotations

import argparse
from pathlib import Path

from domain.entities.modelo_analitico import MODELOS_CON_FICHA
from infrastructure.ingesta.resultados_modelos import LECTORES, SalidaModeloInvalidaError
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_modelo_resultado_repository import DuckDBModeloResultadoRepository

RUTA_BASE_DATOS_POR_DEFECTO = "../data/hidrologia.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa el resultado de un modelo analitico")
    parser.add_argument("--modelo", choices=MODELOS_CON_FICHA, required=True)
    parser.add_argument("--carpeta", type=Path, required=True, help="Carpeta del proyecto que contiene las salidas del modelo")
    parser.add_argument("--db-path", default=RUTA_BASE_DATOS_POR_DEFECTO)
    args = parser.parse_args()

    try:
        resultado = LECTORES[args.modelo](args.carpeta)
    except (SalidaModeloInvalidaError, ValueError) as error:
        raise SystemExit(f"No se importo nada: {error}") from error

    DuckDBModeloResultadoRepository(DuckDBConnection.obtener_instancia(args.db_path)).reemplazar(resultado)
    print(
        f"Importado '{args.modelo}': {len(resultado.indicadores)} indicadores, {len(resultado.series)} series, "
        f"{len(resultado.tablas)} tablas, {len(resultado.advertencias)} advertencias (generado {resultado.generado_en:%Y-%m-%d %H:%M})."
    )


if __name__ == "__main__":
    main()
