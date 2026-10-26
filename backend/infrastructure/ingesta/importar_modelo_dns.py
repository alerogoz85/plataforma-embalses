"""Importa la corrida vigente del modelo de demanda no atendida (DNS) a la base local.

Uso (desde backend/, con el venv activo):
    python -m infrastructure.ingesta.importar_modelo_dns --carpeta "../../2. Modelo DNS"

La carpeta es la del proyecto del modelo (contiene `Datos/outputs` y `Datos/outputs_datos`).
Reemplaza la corrida anterior por completo, valida los archivos antes de escribir y no se borra
con `sincronizar --reiniciar`. Despues hay que volver a publicar la API
(`scripts/desplegar-vercel.sh`) para que la base desplegada la incluya."""
from __future__ import annotations

import argparse
from pathlib import Path

from infrastructure.ingesta.modelo_dns_archivos import ArchivoModeloDnsInvalidoError, leer_modelo_dns
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_modelo_dns_repository import DuckDBModeloDnsRepository

RUTA_BASE_DATOS_POR_DEFECTO = "../data/hidrologia.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Importa el modelo DNS")
    parser.add_argument("--carpeta", type=Path, required=True, help="Carpeta del proyecto del modelo")
    parser.add_argument("--db-path", default=RUTA_BASE_DATOS_POR_DEFECTO)
    args = parser.parse_args()

    try:
        paquete = leer_modelo_dns(args.carpeta)
    except ArchivoModeloDnsInvalidoError as error:
        raise SystemExit(f"No se importo nada: {error}") from error

    DuckDBModeloDnsRepository(DuckDBConnection.obtener_instancia(args.db_path)).reemplazar(paquete)
    print(
        f"Importado: {len(paquete.eventos)} eventos ({paquete.fecha_inicio:%Y-%m-%d} a {paquete.fecha_corte:%Y-%m-%d}), "
        f"{len(paquete.subareas)} subareas, {len(paquete.zonas)} zonas, {len(paquete.cambios_reporte)} cambios de reporte, "
        f"{len(paquete.metricas)} metricas, pronostico {paquete.periodo_pronostico} de {len(paquete.pronostico)} subareas."
    )


if __name__ == "__main__":
    main()
