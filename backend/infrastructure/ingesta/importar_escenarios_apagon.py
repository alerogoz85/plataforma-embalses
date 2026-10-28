"""Ejecuta el modelo de riesgo de apagon en cada combinacion de los controles del visor e importa los escenarios.

Uso (desde backend/, con un entorno que tenga las dependencias del modelo: pandas, pyarrow, scipy, statsmodels, scikit-learn, matplotlib):
    python -m infrastructure.ingesta.importar_escenarios_apagon --carpeta "../../5. Modelo apagón"

Con --exportar-csv no toca la base: escribe la tanda en un archivo CSV para cargarla despues desde el modulo de actualizacion (/actualizar).

Son 468 corridas (51 ONI x 3 simulaciones x 3 horizontes, mas el modo probabilistico); tarda unos minutos. Valida todo antes
de escribir y reemplaza la tanda anterior de una sola vez. Despues hay que volver a publicar la API (`scripts/desplegar-vercel.sh`)."""
from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.ingesta.resultados_modelos.comun import SalidaModeloInvalidaError
from infrastructure.ingesta.resultados_modelos.escenarios_csv import a_csv
from infrastructure.ingesta.resultados_modelos.escenarios_apagon import generar_escenarios
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_escenario_apagon_repository import DuckDBEscenarioApagonRepository

RUTA_BASE_DATOS_POR_DEFECTO = "../data/hidrologia.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa los escenarios del visor de riesgo de apagon")
    parser.add_argument("--carpeta", type=Path, required=True, help="Carpeta del proyecto del modelo de apagon (con Scripts/ y Datos/)")
    parser.add_argument("--db-path", default=RUTA_BASE_DATOS_POR_DEFECTO)
    parser.add_argument("--exportar-csv", type=Path, default=None, help="Escribe la tanda en este CSV en lugar de importarla a la base")
    args = parser.parse_args()

    def progreso(n: int, total: int) -> None:
        if n % 25 == 0 or n == total:
            print(f"  {n}/{total} escenarios", flush=True)

    try:
        escenarios, fuente = generar_escenarios(args.carpeta, progreso)
    except (SalidaModeloInvalidaError, ValueError) as error:
        raise SystemExit(f"No se importo nada: {error}") from error
    if args.exportar_csv:
        args.exportar_csv.write_text(a_csv(escenarios, fuente), encoding="utf-8")
        print(f"Exportados {len(escenarios)} escenarios a {args.exportar_csv} (cárgalos desde el módulo /actualizar).")
        return
    DuckDBEscenarioApagonRepository(DuckDBConnection.obtener_instancia(args.db_path)).reemplazar(escenarios, fuente)
    print(f"Importados {len(escenarios)} escenarios del modelo de apagón (generados {fuente.generado_en:%Y-%m-%d %H:%M}).")


if __name__ == "__main__":
    main()
