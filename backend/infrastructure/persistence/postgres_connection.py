"""Conexion a Postgres (Neon / Vercel Postgres) con la MISMA interfaz que `DuckDBConnection` (`obtener_una_fila`, `obtener_filas`,
`ejecutar`, `ejecutar_lote`): asi los repositorios de los modelos y de la seguridad funcionan igual sobre las dos bases.

Guarda lo que cambia con las cargas del modulo de actualizacion (carbon, DNS, resultados y escenarios de los modelos, usuarios, sesiones y
bitacora). Los datos de embalses siguen en el DuckDB empaquetado, que es de solo lectura en produccion.

Detalles: se escribe `?` como marcador (se traduce a `%s`), la conexion esta en autocommit (las transacciones se abren con BEGIN/COMMIT
explicitos, como ya hacen los repositorios) y si la conexion se cae (las bases serverless la cierran al estar inactivas) se reconecta una vez."""
from __future__ import annotations

import re
from pathlib import Path
from threading import Lock
from typing import Optional, Sequence

_SCHEMA = Path(__file__).parent / "schema.sql"
_SCHEMA_SEGURIDAD = Path(__file__).parent / "schema_seguridad.sql"
_TABLAS_MODELOS = re.compile(r"CREATE TABLE IF NOT EXISTS (?:carbon_|dns_|modelo_)", re.IGNORECASE)
TABLAS_MODELOS_PREFIJOS = ("carbon_", "dns_", "modelo_")


def adaptar_consulta(consulta: str) -> str:
    """`?` -> `%s` (y `%` literal -> `%%`, que psycopg interpretaria como marcador)."""
    return consulta.replace("%", "%%").replace("?", "%s")


def esquema_postgres() -> str:
    """DDL de las tablas de modelos (carbon_*, dns_*, modelo_*) y de seguridad, traducido de DuckDB: DOUBLE -> DOUBLE PRECISION."""
    sin_comentarios = re.sub(r"--[^\n]*", "", _SCHEMA.read_text(encoding="utf-8"))  # un «;» dentro de un comentario partiria mal las sentencias
    sentencias = [s.strip() for s in sin_comentarios.split(";")]
    de_modelos = [s for s in sentencias if _TABLAS_MODELOS.search(s)]
    ddl = ";\n".join(de_modelos) + ";\n" + _SCHEMA_SEGURIDAD.read_text(encoding="utf-8")
    return re.sub(r"\bDOUBLE\b(?! PRECISION)", "DOUBLE PRECISION", ddl)


class PostgresConnection:
    def __init__(self, dsn: str, aplicar_esquema: bool = True) -> None:
        self._dsn = dsn
        self._lock = Lock()
        self._conexion = self._conectar()
        if aplicar_esquema:
            self.ejecutar_script(esquema_postgres())

    def _conectar(self):
        import psycopg  # importado aqui: solo hace falta cuando hay DATABASE_URL

        return psycopg.connect(self._dsn, autocommit=True, connect_timeout=10)

    def _con_reintento(self, accion):
        import psycopg

        with self._lock:
            try:
                return accion(self._conexion)
            except (psycopg.OperationalError, psycopg.InterfaceError):
                self._conexion = self._conectar()
                return accion(self._conexion)

    def obtener_una_fila(self, consulta: str, parametros: Sequence = ()) -> Optional[tuple]:
        return self._con_reintento(lambda c: c.execute(adaptar_consulta(consulta), list(parametros)).fetchone())

    def obtener_filas(self, consulta: str, parametros: Sequence = ()) -> list[tuple]:
        return self._con_reintento(lambda c: c.execute(adaptar_consulta(consulta), list(parametros)).fetchall())

    def ejecutar(self, consulta: str, parametros: Sequence = ()) -> None:
        # BEGIN/COMMIT/ROLLBACK no se reintentan: perderian la transaccion a medias.
        if consulta.strip().upper().split()[0] in ("BEGIN", "COMMIT", "ROLLBACK"):
            with self._lock:
                self._conexion.execute(consulta)
            return
        self._con_reintento(lambda c: c.execute(adaptar_consulta(consulta), list(parametros)) and None)

    def ejecutar_lote(self, consulta: str, filas: Sequence[Sequence]) -> None:
        def accion(c):
            with c.cursor() as cur:
                cur.executemany(adaptar_consulta(consulta), [list(f) for f in filas])

        with self._lock:  # dentro de una transaccion abierta: no se reintenta
            accion(self._conexion)

    def ejecutar_script(self, ddl: str) -> None:
        with self._lock:
            self._conexion.execute(ddl)

    def cerrar(self) -> None:
        self._conexion.close()
