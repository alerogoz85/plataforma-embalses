from __future__ import annotations

from typing import Optional

from domain.entities.embalse import Embalse
from domain.entities.region import NombreRegion, Region
from domain.repositories.embalse_repository import EmbalseRepository
from infrastructure.persistence.duckdb_connection import DuckDBConnection

_COLUMNAS = "id, nombre, region, es_agregado"


class DuckDBEmbalseRepository(EmbalseRepository):
    """Adaptador de persistencia para Embalse sobre DuckDB."""

    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    def obtener_por_id(self, embalse_id: str) -> Optional[Embalse]:
        fila = self._db.obtener_una_fila(
            f"SELECT {_COLUMNAS} FROM embalses WHERE id = ?", [embalse_id]
        )
        return self._fila_a_embalse(fila) if fila else None

    def listar(self, region: Optional[NombreRegion] = None) -> list[Embalse]:
        if region is not None:
            filas = self._db.obtener_filas(
                f"SELECT {_COLUMNAS} FROM embalses WHERE region = ? ORDER BY nombre",
                [region.value],
            )
        else:
            filas = self._db.obtener_filas(
                f"SELECT {_COLUMNAS} FROM embalses ORDER BY region, nombre"
            )
        return [self._fila_a_embalse(fila) for fila in filas]

    def guardar(self, embalse: Embalse) -> None:
        self._db.ejecutar(
            f"""
            INSERT INTO embalses ({_COLUMNAS}) VALUES (?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                nombre = excluded.nombre,
                region = excluded.region,
                es_agregado = excluded.es_agregado
            """,
            [embalse.id, embalse.nombre, embalse.region.nombre.value, embalse.es_agregado],
        )

    @staticmethod
    def _fila_a_embalse(fila: tuple) -> Embalse:
        id_, nombre, region, es_agregado = fila
        return Embalse(
            id=id_, nombre=nombre, region=Region(NombreRegion(region)), es_agregado=es_agregado
        )
