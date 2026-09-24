from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Optional, Sequence

import duckdb

from domain.exceptions import EsquemaIncompatibleError

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"
_TABLAS = ("mediciones", "embalses", "fuente_datos")


class DuckDBConnection:
    """Envuelve una unica conexion DuckDB compartida por la aplicacion.

    Una conexion de DuckDB no es segura para uso concurrente desde multiples
    hilos: FastAPI ejecuta los endpoints sincronos en un threadpool, por lo
    que dos requests simultaneas pueden ejecutar consultas al mismo tiempo.
    Esta clase serializa todo acceso de lectura/escritura con un lock de
    instancia para evitar resultados corruptos o caidas del proceso.
    """

    _instancia: "DuckDBConnection | None" = None
    _lock_singleton = Lock()

    def __init__(self, ruta_base_datos: str, reiniciar: bool = False) -> None:
        self._conexion = duckdb.connect(ruta_base_datos)
        self._lock_consultas = Lock()
        if reiniciar:
            self._eliminar_tablas()
        self._verificar_esquema_compatible()
        self._aplicar_esquema()

    @classmethod
    def obtener_instancia(cls, ruta_base_datos: str, reiniciar: bool = False) -> "DuckDBConnection":
        with cls._lock_singleton:
            if cls._instancia is None:
                cls._instancia = cls(ruta_base_datos, reiniciar=reiniciar)
            return cls._instancia

    def _eliminar_tablas(self) -> None:
        for tabla in _TABLAS:
            self._conexion.execute(f"DROP TABLE IF EXISTS {tabla}")

    def _verificar_esquema_compatible(self) -> None:
        """Una base creada con la version anterior (datos sinteticos con cota
        y generacion) no es compatible; se exige reiniciarla de forma
        explicita en lugar de borrarla sin avisar."""
        columnas = {
            fila[0]
            for fila in self._conexion.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'mediciones'"
            ).fetchall()
        }
        if columnas and "volumen_util_mm3" not in columnas:
            raise EsquemaIncompatibleError(
                "La base de datos tiene un esquema anterior. Reinicialala con: "
                "python -m infrastructure.ingesta.sincronizar --fuente simem --reiniciar"
            )

    def _aplicar_esquema(self) -> None:
        ddl = _SCHEMA_PATH.read_text(encoding="utf-8")
        with self._lock_consultas:
            self._conexion.execute(ddl)

    def obtener_una_fila(self, consulta: str, parametros: Sequence = ()) -> Optional[tuple]:
        with self._lock_consultas:
            return self._conexion.execute(consulta, list(parametros)).fetchone()

    def obtener_filas(self, consulta: str, parametros: Sequence = ()) -> list[tuple]:
        with self._lock_consultas:
            return self._conexion.execute(consulta, list(parametros)).fetchall()

    def ejecutar(self, consulta: str, parametros: Sequence = ()) -> None:
        with self._lock_consultas:
            self._conexion.execute(consulta, list(parametros))

    def ejecutar_lote(self, consulta: str, filas: Sequence[Sequence]) -> None:
        with self._lock_consultas:
            self._conexion.executemany(consulta, list(filas))

    def cerrar(self) -> None:
        self._conexion.close()
