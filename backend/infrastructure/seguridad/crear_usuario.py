"""Crea o actualiza un usuario del modulo de actualizacion. No hay registro por la web: las cuentas se crean aqui.

Uso (desde backend/; con DATABASE_URL va a Postgres, sin ella al DuckDB local):
    python -m infrastructure.seguridad.crear_usuario --usuario ana --nombre "Ana Pérez" --rol administrador
    python -m infrastructure.seguridad.crear_usuario --usuario luis --nombre "Luis Gómez" --rol cargador --tableros gas,dns

La contraseña se pide por teclado sin mostrarla (o en la variable CONTRASENA_USUARIO para automatizar); nunca va en la linea de comandos.
Politica: 12 caracteres o mas, letras y números/símbolos, sin el nombre de usuario. Si el usuario existe, cambia su contraseña/rol y
cierra sus sesiones abiertas."""
from __future__ import annotations

import argparse
import getpass
import os

from domain.entities.seguridad import ROL_ADMINISTRADOR, ROLES, Usuario, validar_contrasena
from infrastructure.actualizacion.tableros import construir_adaptadores
from infrastructure.persistence.sql_seguridad_repository import SqlSesionRepository, SqlUsuarioRepository
from infrastructure.seguridad import contrasenas
from domain.entities.seguridad import CredencialUsuario

RUTA_BASE_DATOS_POR_DEFECTO = "../data/hidrologia.duckdb"


def ids_de_tableros() -> list[str]:
    return list(construir_adaptadores(None, None, None, None))  # type: ignore[arg-type]


def crear(conexion, nombre_usuario: str, nombre: str, rol: str, tableros: tuple[str, ...], contrasena: str) -> None:
    usuario = Usuario(nombre_usuario=nombre_usuario.strip().lower(), nombre=nombre.strip(), rol=rol, tableros_permitidos=tableros)
    validar_contrasena(contrasena, usuario.nombre_usuario)
    desconocidos = set(tableros) - set(ids_de_tableros())
    if desconocidos:
        raise ValueError(f"Tableros desconocidos: {', '.join(sorted(desconocidos))}. Disponibles: {', '.join(ids_de_tableros())}")
    if rol != ROL_ADMINISTRADOR and not tableros:
        raise ValueError("Un cargador necesita al menos un tablero (--tableros)")
    SqlUsuarioRepository(conexion).guardar(CredencialUsuario(usuario=usuario, hash_contrasena=contrasenas.hashear(contrasena)))
    SqlSesionRepository(conexion).revocar_de_usuario(usuario.nombre_usuario)


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea o actualiza un usuario del módulo de actualización")
    parser.add_argument("--usuario", required=True)
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--rol", choices=ROLES, required=True)
    parser.add_argument("--tableros", default="", help="Para cargadores: ids separados por coma (%s)" % ", ".join(ids_de_tableros()))
    parser.add_argument("--db-path", default=RUTA_BASE_DATOS_POR_DEFECTO)
    args = parser.parse_args()

    contrasena = os.environ.get("CONTRASENA_USUARIO") or getpass.getpass("Contraseña: ")
    if not os.environ.get("CONTRASENA_USUARIO") and getpass.getpass("Repite la contraseña: ") != contrasena:
        raise SystemExit("Las contraseñas no coinciden")

    dsn = os.environ.get("DATABASE_URL")
    if dsn:
        from infrastructure.persistence.postgres_connection import PostgresConnection

        conexion = PostgresConnection(dsn)
    else:
        from infrastructure.persistence.duckdb_connection import DuckDBConnection

        conexion = DuckDBConnection.obtener_instancia(args.db_path)
    try:
        crear(conexion, args.usuario, args.nombre, args.rol, tuple(t for t in args.tableros.split(",") if t), contrasena)
    except ValueError as error:
        raise SystemExit(f"No se creó el usuario: {error}") from error
    print(f"Usuario «{args.usuario.strip().lower()}» ({args.rol}) guardado.")


if __name__ == "__main__":
    main()
