"""Repositorios de seguridad (usuarios, sesiones, bitacora) sobre una conexion con la interfaz comun
(`obtener_una_fila`, `obtener_filas`, `ejecutar`): sirven igual con DuckDB (local) y con Postgres (produccion)."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Protocol, Sequence

from domain.entities.seguridad import CredencialUsuario, RegistroAuditoria, Sesion, Usuario
from domain.repositories.seguridad_repository import AuditoriaRepository, SesionRepository, UsuarioRepository


class Conexion(Protocol):
    def obtener_una_fila(self, consulta: str, parametros: Sequence = ...) -> Optional[tuple]: ...
    def obtener_filas(self, consulta: str, parametros: Sequence = ...) -> list[tuple]: ...
    def ejecutar(self, consulta: str, parametros: Sequence = ...) -> None: ...


class SqlUsuarioRepository(UsuarioRepository):
    _COLUMNAS = "nombre_usuario, nombre, rol, tableros, activo, hash_contrasena, intentos_fallidos, bloqueado_hasta"

    def __init__(self, conexion: Conexion) -> None:
        self._db = conexion

    @staticmethod
    def _desde_fila(f: tuple) -> CredencialUsuario:
        tableros = tuple(t for t in f[3].split(",") if t)
        return CredencialUsuario(
            usuario=Usuario(nombre_usuario=f[0], nombre=f[1], rol=f[2], tableros_permitidos=tableros, activo=bool(f[4])),
            hash_contrasena=f[5], intentos_fallidos=int(f[6]), bloqueado_hasta=f[7],
        )

    def obtener(self, nombre_usuario: str) -> Optional[CredencialUsuario]:
        fila = self._db.obtener_una_fila(f"SELECT {self._COLUMNAS} FROM seg_usuarios WHERE nombre_usuario = ?", [nombre_usuario])
        return None if fila is None else self._desde_fila(fila)

    def guardar(self, c: CredencialUsuario) -> None:
        u = c.usuario
        self._db.ejecutar("DELETE FROM seg_usuarios WHERE nombre_usuario = ?", [u.nombre_usuario])
        self._db.ejecutar(
            f"INSERT INTO seg_usuarios ({self._COLUMNAS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [u.nombre_usuario, u.nombre, u.rol, ",".join(u.tableros_permitidos), u.activo, c.hash_contrasena, c.intentos_fallidos, c.bloqueado_hasta],
        )

    def registrar_resultado_acceso(self, nombre_usuario: str, intentos_fallidos: int, bloqueado_hasta: Optional[datetime]) -> None:
        self._db.ejecutar(
            "UPDATE seg_usuarios SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE nombre_usuario = ?",
            [intentos_fallidos, bloqueado_hasta, nombre_usuario],
        )

    def listar(self) -> list[CredencialUsuario]:
        return [self._desde_fila(f) for f in self._db.obtener_filas(f"SELECT {self._COLUMNAS} FROM seg_usuarios ORDER BY nombre_usuario")]


class SqlSesionRepository(SesionRepository):
    def __init__(self, conexion: Conexion) -> None:
        self._db = conexion

    def crear(self, s: Sesion) -> None:
        self._db.ejecutar(
            "INSERT INTO seg_sesiones VALUES (?, ?, ?, ?, ?, ?)",
            [s.huella_token, s.nombre_usuario, s.token_csrf, s.creada_en, s.ultima_actividad, s.ip],
        )

    def obtener(self, huella_token: str) -> Optional[Sesion]:
        f = self._db.obtener_una_fila(
            "SELECT huella_token, nombre_usuario, token_csrf, creada_en, ultima_actividad, ip FROM seg_sesiones WHERE huella_token = ?",
            [huella_token],
        )
        return None if f is None else Sesion(*f)

    def registrar_actividad(self, huella_token: str, momento: datetime) -> None:
        self._db.ejecutar("UPDATE seg_sesiones SET ultima_actividad = ? WHERE huella_token = ?", [momento, huella_token])

    def revocar(self, huella_token: str) -> None:
        self._db.ejecutar("DELETE FROM seg_sesiones WHERE huella_token = ?", [huella_token])

    def revocar_de_usuario(self, nombre_usuario: str) -> None:
        self._db.ejecutar("DELETE FROM seg_sesiones WHERE nombre_usuario = ?", [nombre_usuario])

    def purgar_vencidas(self, antes_de: datetime) -> None:
        self._db.ejecutar("DELETE FROM seg_sesiones WHERE ultima_actividad < ?", [antes_de])


_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _limpio(texto: str, largo: int) -> str:
    """Sin saltos de linea ni caracteres de control (no se puede falsificar una linea de la bitacora) y de largo acotado."""
    return _CONTROL.sub(" ", texto)[:largo]


class SqlAuditoriaRepository(AuditoriaRepository):
    def __init__(self, conexion: Conexion) -> None:
        self._db = conexion

    def registrar(self, r: RegistroAuditoria) -> None:
        self._db.ejecutar(
            "INSERT INTO seg_auditoria VALUES (?, ?, ?, ?, ?, ?, ?)",
            [r.momento, _limpio(r.nombre_usuario, 80), r.accion, r.tablero, r.resultado, _limpio(r.detalle, 1000), _limpio(r.ip, 64)],
        )

    def listar(self, limite: int) -> list[RegistroAuditoria]:
        filas = self._db.obtener_filas(
            "SELECT momento, nombre_usuario, accion, tablero, resultado, detalle, ip FROM seg_auditoria ORDER BY momento DESC LIMIT ?",
            [int(limite)],
        )
        return [RegistroAuditoria(*f) for f in filas]

    def contar_fallos_desde_ip(self, ip: str, desde: datetime) -> int:
        fila = self._db.obtener_una_fila(
            "SELECT COUNT(*) FROM seg_auditoria WHERE ip = ? AND accion IN ('inicio_sesion_fallido', 'cuenta_bloqueada') AND momento >= ?",
            [_limpio(ip, 64), desde],
        )
        return int(fila[0]) if fila else 0
