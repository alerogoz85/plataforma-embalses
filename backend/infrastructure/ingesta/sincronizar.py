"""Sincroniza la base local con una fuente de datos.

Uso (desde backend/, con el venv activo):
    python -m infrastructure.ingesta.sincronizar --fuente simem --reiniciar   # carga inicial
    python -m infrastructure.ingesta.sincronizar --fuente simem                # actualizacion incremental
    python -m infrastructure.ingesta.sincronizar --fuente sintetica --reiniciar --desde 2023-01-01
"""
from __future__ import annotations

import argparse
import logging
from datetime import date, timedelta

from application.ports.output.fuente_mediciones_port import FuenteMedicionesPort
from application.use_cases.sincronizar_datos import SincronizarDatosUseCase
from infrastructure.data_generation.fuente_sintetica import FuenteSintetica
from infrastructure.fuentes.clientes_http import ClienteSimem, ClienteXm
from infrastructure.fuentes.simem_xm_fuente import SimemXmFuenteMediciones
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_embalse_repository import DuckDBEmbalseRepository
from infrastructure.persistence.duckdb_medicion_repository import DuckDBMedicionRepository
from infrastructure.persistence.duckdb_metadatos_repository import DuckDBMetadatosRepository

RUTA_BASE_DATOS_POR_DEFECTO = "../data/hidrologia.duckdb"
DESDE_POR_DEFECTO_SIMEM = date(2022, 1, 1)
DIAS_POR_DEFECTO_SINTETICA = 1095


def _crear_fuente(nombre: str) -> FuenteMedicionesPort:
    if nombre == "simem":
        return SimemXmFuenteMediciones(ClienteSimem(), ClienteXm())
    return FuenteSintetica()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sincroniza la base con SIMEM/XM o con datos sinteticos")
    parser.add_argument("--fuente", choices=["simem", "sintetica"], default="simem")
    parser.add_argument("--db-path", default=RUTA_BASE_DATOS_POR_DEFECTO)
    parser.add_argument("--desde", type=date.fromisoformat, help="YYYY-MM-DD; por defecto, incremental")
    parser.add_argument("--hasta", type=date.fromisoformat, help="YYYY-MM-DD; por defecto, hoy")
    parser.add_argument("--reiniciar", action="store_true", help="Borra las tablas antes de cargar")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    conexion = DuckDBConnection.obtener_instancia(args.db_path, reiniciar=args.reiniciar)
    caso_de_uso = SincronizarDatosUseCase(
        _crear_fuente(args.fuente),
        DuckDBEmbalseRepository(conexion),
        DuckDBMedicionRepository(conexion),
        DuckDBMetadatosRepository(conexion),
    )

    por_defecto = (
        DESDE_POR_DEFECTO_SIMEM
        if args.fuente == "simem"
        else date.today() - timedelta(days=DIAS_POR_DEFECTO_SINTETICA)
    )
    resultado = caso_de_uso.ejecutar(desde_por_defecto=por_defecto, desde=args.desde, hasta=args.hasta)
    print(
        f"Sincronizado {resultado.desde} -> {resultado.hasta}: "
        f"{resultado.embalses} embalses, {resultado.mediciones} mediciones. "
        f"Fecha de corte de la base: {resultado.fecha_corte}"
    )


if __name__ == "__main__":
    main()
