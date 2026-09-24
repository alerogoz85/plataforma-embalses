from __future__ import annotations

from datetime import timezone
from typing import Optional

from domain.entities.metadatos_datos import MetadatosDatos
from domain.repositories.metadatos_repository import MetadatosRepository
from infrastructure.persistence.duckdb_connection import DuckDBConnection

_ID_UNICO = 1


class DuckDBMetadatosRepository(MetadatosRepository):
    """Guarda un unico registro con la procedencia de los datos cargados."""

    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    def obtener(self) -> Optional[MetadatosDatos]:
        fila = self._db.obtener_una_fila(
            "SELECT fuente, descripcion, fecha_corte, actualizado_en, es_real "
            "FROM fuente_datos WHERE id = ?",
            [_ID_UNICO],
        )
        if fila is None:
            return None
        fuente, descripcion, fecha_corte, actualizado_en, es_real = fila
        return MetadatosDatos(
            fuente=fuente,
            descripcion=descripcion,
            fecha_corte=fecha_corte,
            actualizado_en=actualizado_en.replace(tzinfo=timezone.utc),
            es_real=es_real,
        )

    def guardar(self, metadatos: MetadatosDatos) -> None:
        actualizado_utc = metadatos.actualizado_en.astimezone(timezone.utc).replace(tzinfo=None)
        self._db.ejecutar(
            """
            INSERT INTO fuente_datos (id, fuente, descripcion, fecha_corte, actualizado_en, es_real)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (id) DO UPDATE SET
                fuente = excluded.fuente,
                descripcion = excluded.descripcion,
                fecha_corte = excluded.fecha_corte,
                actualizado_en = excluded.actualizado_en,
                es_real = excluded.es_real
            """,
            [
                _ID_UNICO,
                metadatos.fuente,
                metadatos.descripcion,
                metadatos.fecha_corte,
                actualizado_utc,
                metadatos.es_real,
            ],
        )
