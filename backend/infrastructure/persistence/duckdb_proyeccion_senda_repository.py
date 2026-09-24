from __future__ import annotations

from domain.entities.proyeccion_senda import ProyeccionSendaMensual
from domain.repositories.proyeccion_senda_repository import ProyeccionSendaRepository
from infrastructure.persistence.duckdb_connection import DuckDBConnection


class DuckDBProyeccionSendaRepository(ProyeccionSendaRepository):
    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    def obtener(self, embalse_id: str) -> list[ProyeccionSendaMensual]:
        filas = self._db.obtener_filas(
            "SELECT embalse_id, mes, limite_inferior, valor_esperado, limite_superior, origen "
            "FROM proyecciones_senda WHERE embalse_id = ? ORDER BY mes",
            [embalse_id],
        )
        return [ProyeccionSendaMensual(*fila) for fila in filas]

    def reemplazar_todas(self, proyecciones: list[ProyeccionSendaMensual]) -> None:
        self._db.ejecutar("DELETE FROM proyecciones_senda")
        self._db.ejecutar_lote(
            "INSERT INTO proyecciones_senda VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    p.embalse_id,
                    p.mes,
                    p.limite_inferior,
                    p.valor_esperado,
                    p.limite_superior,
                    p.origen,
                )
                for p in proyecciones
            ],
        )
