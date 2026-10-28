"""Copia a Postgres las tablas de modelos y de seguridad que hoy estan en el DuckDB local (una sola vez, al pasar a produccion con base externa).

Uso (desde backend/, con DATABASE_URL apuntando a la base de Postgres):
    DATABASE_URL="postgresql://..." python -m infrastructure.persistence.migrar_a_postgres [--db-path ../data/hidrologia.duckdb]

Cada tabla se reemplaza completa dentro de una transaccion: si algo falla, esa tabla queda como estaba. La base de embalses NO se copia
(sigue empaquetada con la API). No imprime la cadena de conexion."""
from __future__ import annotations

import argparse
import os

from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.postgres_connection import TABLAS_MODELOS_PREFIJOS, PostgresConnection

TABLAS_SEGURIDAD = ("seg_usuarios",)  # usuarios sí; sesiones y bitacora no se arrastran


def tablas_a_migrar(origen: DuckDBConnection) -> list[str]:
    filas = origen.obtener_filas("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name")
    return [t for (t,) in filas if t.startswith(TABLAS_MODELOS_PREFIJOS) or t in TABLAS_SEGURIDAD]


def migrar(origen: DuckDBConnection, destino: PostgresConnection) -> dict[str, int]:
    copiadas: dict[str, int] = {}
    for tabla in tablas_a_migrar(origen):  # nombres que salen del catalogo de la base, no de un usuario
        filas = origen.obtener_filas(f"SELECT * FROM {tabla}")
        destino.ejecutar("BEGIN")
        try:
            destino.ejecutar(f"DELETE FROM {tabla}")
            if filas:
                destino.ejecutar_lote(f"INSERT INTO {tabla} VALUES ({', '.join(['?'] * len(filas[0]))})", filas)
        except Exception:
            destino.ejecutar("ROLLBACK")
            raise
        destino.ejecutar("COMMIT")
        copiadas[tabla] = len(filas)
    return copiadas


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra las tablas de modelos y seguridad de DuckDB a Postgres")
    parser.add_argument("--db-path", default="../data/hidrologia.duckdb")
    args = parser.parse_args()
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("Define DATABASE_URL con la cadena de conexión de Postgres")
    copiadas = migrar(DuckDBConnection.obtener_instancia(args.db_path), PostgresConnection(dsn))
    for tabla, n in copiadas.items():
        print(f"  {tabla}: {n} filas")
    print(f"Migradas {len(copiadas)} tablas.")


if __name__ == "__main__":
    main()
