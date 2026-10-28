"""Seguridad del modulo de actualizacion de tableros: usuarios, roles, sesiones y bitacora.

Reglas de dominio (no dependen de FastAPI ni de la base):
* Un usuario tiene un rol. El ADMINISTRADOR puede actualizar todos los tableros y ver la bitacora; el CARGADOR solo
  actualiza los tableros que se le asignaron.
* Una sesion vence por inactividad y por antigüedad (lo que ocurra primero).
* Tras demasiados intentos fallidos la cuenta se bloquea un tiempo."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

ROL_ADMINISTRADOR = "administrador"
ROL_CARGADOR = "cargador"
ROLES = (ROL_ADMINISTRADOR, ROL_CARGADOR)

MAX_INTENTOS_FALLIDOS = 5
BLOQUEO = timedelta(minutes=15)
VIGENCIA_SESION = timedelta(hours=8)
INACTIVIDAD_SESION = timedelta(minutes=30)
LARGO_MINIMO_CONTRASENA = 12

ACCIONES = ("inicio_sesion", "inicio_sesion_fallido", "cuenta_bloqueada", "cierre_sesion", "validacion", "actualizacion", "acceso_denegado")


def validar_contrasena(contrasena: str, nombre_usuario: str) -> None:
    """Politica de contraseñas: largo minimo, mezcla de letras y numeros/simbolos y distinta del usuario."""
    if len(contrasena) < LARGO_MINIMO_CONTRASENA:
        raise ValueError(f"La contraseña debe tener al menos {LARGO_MINIMO_CONTRASENA} caracteres")
    if contrasena.lower() == nombre_usuario.lower() or nombre_usuario.lower() in contrasena.lower():
        raise ValueError("La contraseña no puede contener el nombre de usuario")
    if not any(c.isalpha() for c in contrasena) or not any(not c.isalpha() for c in contrasena):
        raise ValueError("La contraseña debe combinar letras con números o símbolos")
    if len(set(contrasena)) < 5:
        raise ValueError("La contraseña es demasiado repetitiva")


@dataclass(frozen=True)
class Usuario:
    nombre_usuario: str
    nombre: str
    rol: str
    tableros_permitidos: tuple[str, ...]
    activo: bool = True

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", self.nombre_usuario):
            raise ValueError("El nombre de usuario solo admite letras, números, punto, guion y guion bajo")
        if self.rol not in ROLES:
            raise ValueError(f"Rol '{self.rol}' desconocido; admitidos: {', '.join(ROLES)}")

    @property
    def es_administrador(self) -> bool:
        return self.rol == ROL_ADMINISTRADOR

    def puede_actualizar(self, tablero_id: str) -> bool:
        return self.activo and (self.es_administrador or tablero_id in self.tableros_permitidos)


@dataclass(frozen=True)
class CredencialUsuario:
    """Lo que guarda la base de un usuario: su hash (nunca la contraseña) y el estado de bloqueo."""

    usuario: Usuario
    hash_contrasena: str
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None

    def bloqueado(self, ahora: datetime) -> bool:
        return self.bloqueado_hasta is not None and self.bloqueado_hasta > ahora


@dataclass(frozen=True)
class Sesion:
    """Sesion activa. Solo se guarda la huella (sha256) del token: quien lea la base no puede usarla."""

    huella_token: str
    nombre_usuario: str
    token_csrf: str
    creada_en: datetime
    ultima_actividad: datetime
    ip: str

    def vigente(self, ahora: datetime) -> bool:
        return ahora - self.creada_en < VIGENCIA_SESION and ahora - self.ultima_actividad < INACTIVIDAD_SESION

    @property
    def vence_en(self) -> datetime:
        return min(self.creada_en + VIGENCIA_SESION, self.ultima_actividad + INACTIVIDAD_SESION)


@dataclass(frozen=True)
class RegistroAuditoria:
    momento: datetime
    nombre_usuario: str
    accion: str
    tablero: Optional[str]
    resultado: str  # ok | rechazado | error
    detalle: str
    ip: str

    def __post_init__(self) -> None:
        if self.accion not in ACCIONES:
            raise ValueError(f"Accion de auditoria '{self.accion}' desconocida")
