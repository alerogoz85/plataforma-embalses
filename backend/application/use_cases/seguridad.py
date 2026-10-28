"""Casos de uso de autenticacion y sesion del modulo de actualizacion."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional, Protocol

from application.dtos.actualizacion_dto import RegistroAuditoriaDTO, SesionDTO, UsuarioDTO
from domain.entities.seguridad import (
    BLOQUEO,
    MAX_INTENTOS_FALLIDOS,
    VIGENCIA_SESION,
    CredencialUsuario,
    RegistroAuditoria,
    Sesion,
    Usuario,
)
from domain.exceptions import AccesoDenegadoError, CredencialesInvalidasError, CuentaBloqueadaError, SesionInvalidaError
from domain.repositories.seguridad_repository import AuditoriaRepository, SesionRepository, UsuarioRepository

Reloj = Callable[[], datetime]
MAX_FALLOS_POR_IP = 20
VENTANA_IP = timedelta(minutes=15)
ACTUALIZAR_ACTIVIDAD_CADA = timedelta(minutes=1)
MAX_LARGO_CAMPO = 80


class ServicioContrasenas(Protocol):
    def verificar(self, contrasena: str, almacenado: str) -> bool: ...
    def verificar_falso(self, contrasena: str) -> None: ...


def huella_de(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def usuario_dto(u: Usuario, todos_los_tableros: tuple[str, ...] = ()) -> UsuarioDTO:
    tableros = list(todos_los_tableros) if u.es_administrador else list(u.tableros_permitidos)
    return UsuarioDTO(nombre_usuario=u.nombre_usuario, nombre=u.nombre, rol=u.rol, tableros=tableros)


@dataclass(frozen=True)
class SesionIniciada:
    token: str  # solo se entrega aqui, una vez: en la base queda su huella
    sesion: Sesion
    usuario: Usuario


@dataclass(frozen=True)
class ContextoSesion:
    sesion: Sesion
    usuario: Usuario


class IniciarSesionUseCase:
    def __init__(
        self, usuarios: UsuarioRepository, sesiones: SesionRepository, auditoria: AuditoriaRepository, contrasenas: ServicioContrasenas, reloj: Reloj
    ) -> None:
        self._usuarios, self._sesiones, self._auditoria, self._contrasenas, self._reloj = usuarios, sesiones, auditoria, contrasenas, reloj

    def _auditar(self, usuario: str, accion: str, resultado: str, detalle: str, ip: str) -> None:
        self._auditoria.registrar(RegistroAuditoria(self._reloj(), usuario, accion, None, resultado, detalle, ip))

    def ejecutar(self, nombre_usuario: str, contrasena: str, ip: str) -> SesionIniciada:
        ahora = self._reloj()
        nombre = nombre_usuario.strip().lower()[:MAX_LARGO_CAMPO]
        # Freno por origen: muchos fallos desde una misma direccion se bloquean aunque cambie de usuario.
        if self._auditoria.contar_fallos_desde_ip(ip, ahora - VENTANA_IP) >= MAX_FALLOS_POR_IP:
            raise CuentaBloqueadaError(int(VENTANA_IP.total_seconds() // 60))

        cred = self._usuarios.obtener(nombre) if nombre else None
        if cred is None or not cred.usuario.activo:
            self._contrasenas.verificar_falso(contrasena)  # mismo tiempo que una verificacion real
            self._auditar(nombre, "inicio_sesion_fallido", "rechazado", "usuario desconocido o inactivo", ip)
            raise CredencialesInvalidasError()

        if cred.bloqueado(ahora):
            restante = max(1, int((cred.bloqueado_hasta - ahora).total_seconds() // 60) + 1)
            self._auditar(nombre, "cuenta_bloqueada", "rechazado", "intento con la cuenta bloqueada", ip)
            raise CuentaBloqueadaError(restante)

        if not self._contrasenas.verificar(contrasena, cred.hash_contrasena):
            previos = 0 if cred.bloqueado_hasta is not None else cred.intentos_fallidos  # bloqueo vencido: se empieza de cero
            intentos = previos + 1
            if intentos >= MAX_INTENTOS_FALLIDOS:
                self._usuarios.registrar_resultado_acceso(nombre, intentos, ahora + BLOQUEO)
                self._sesiones.revocar_de_usuario(nombre)
                self._auditar(nombre, "cuenta_bloqueada", "rechazado", f"{intentos} intentos fallidos: cuenta bloqueada", ip)
                raise CuentaBloqueadaError(int(BLOQUEO.total_seconds() // 60))
            self._usuarios.registrar_resultado_acceso(nombre, intentos, None)
            self._auditar(nombre, "inicio_sesion_fallido", "rechazado", f"contraseña incorrecta ({intentos}/{MAX_INTENTOS_FALLIDOS})", ip)
            raise CredencialesInvalidasError()

        if cred.intentos_fallidos or cred.bloqueado_hasta:
            self._usuarios.registrar_resultado_acceso(nombre, 0, None)
        self._sesiones.purgar_vencidas(ahora - VIGENCIA_SESION)
        token = secrets.token_urlsafe(32)
        sesion = Sesion(huella_de(token), nombre, secrets.token_urlsafe(24), ahora, ahora, ip)
        self._sesiones.crear(sesion)
        self._auditar(nombre, "inicio_sesion", "ok", "sesión iniciada", ip)
        return SesionIniciada(token=token, sesion=sesion, usuario=cred.usuario)


class ObtenerSesionUseCase:
    """Resuelve el token de la cookie en una sesion vigente. Para peticiones que escriben exige ademas el token CSRF."""

    def __init__(self, usuarios: UsuarioRepository, sesiones: SesionRepository, reloj: Reloj) -> None:
        self._usuarios, self._sesiones, self._reloj = usuarios, sesiones, reloj

    def ejecutar(self, token: Optional[str], token_csrf: Optional[str] = None, exigir_csrf: bool = False) -> ContextoSesion:
        if not token or len(token) > 200:
            raise SesionInvalidaError()
        huella = huella_de(token)
        sesion = self._sesiones.obtener(huella)
        ahora = self._reloj()
        if sesion is None:
            raise SesionInvalidaError()
        if not sesion.vigente(ahora):
            self._sesiones.revocar(huella)
            raise SesionInvalidaError("La sesión venció; inicia sesión de nuevo")
        cred = self._usuarios.obtener(sesion.nombre_usuario)
        if cred is None or not cred.usuario.activo:
            self._sesiones.revocar(huella)
            raise SesionInvalidaError()
        if exigir_csrf and not (token_csrf and hmac.compare_digest(token_csrf.encode(), sesion.token_csrf.encode())):
            raise SesionInvalidaError("Falta o no coincide el token de seguridad (CSRF)")
        if ahora - sesion.ultima_actividad > ACTUALIZAR_ACTIVIDAD_CADA:
            self._sesiones.registrar_actividad(huella, ahora)
        return ContextoSesion(sesion=sesion, usuario=cred.usuario)


class CerrarSesionUseCase:
    def __init__(self, sesiones: SesionRepository, auditoria: AuditoriaRepository, reloj: Reloj) -> None:
        self._sesiones, self._auditoria, self._reloj = sesiones, auditoria, reloj

    def ejecutar(self, contexto: ContextoSesion, ip: str) -> None:
        self._sesiones.revocar(contexto.sesion.huella_token)
        self._auditoria.registrar(RegistroAuditoria(self._reloj(), contexto.usuario.nombre_usuario, "cierre_sesion", None, "ok", "sesión cerrada", ip))


class ListarAuditoriaUseCase:
    def __init__(self, auditoria: AuditoriaRepository) -> None:
        self._auditoria = auditoria

    def ejecutar(self, contexto: ContextoSesion, limite: int = 100) -> list[RegistroAuditoriaDTO]:
        if not contexto.usuario.es_administrador:
            raise AccesoDenegadoError("La bitácora es solo para administradores")
        return [
            RegistroAuditoriaDTO(momento=r.momento, usuario=r.nombre_usuario, accion=r.accion, tablero=r.tablero, resultado=r.resultado, detalle=r.detalle, ip=r.ip)
            for r in self._auditoria.listar(max(1, min(limite, 500)))
        ]


def crear_credencial(usuario: Usuario, hash_contrasena: str) -> CredencialUsuario:
    return CredencialUsuario(usuario=usuario, hash_contrasena=hash_contrasena)


def sesion_dto(contexto_usuario: Usuario, sesion: Sesion, todos_los_tableros: tuple[str, ...]) -> SesionDTO:
    return SesionDTO(usuario=usuario_dto(contexto_usuario, todos_los_tableros), token_csrf=sesion.token_csrf, vence_en=sesion.vence_en)
