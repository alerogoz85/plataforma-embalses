from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from domain.entities.seguridad import CredencialUsuario, RegistroAuditoria, Sesion


class UsuarioRepository(ABC):
    @abstractmethod
    def obtener(self, nombre_usuario: str) -> Optional[CredencialUsuario]:
        raise NotImplementedError

    @abstractmethod
    def guardar(self, credencial: CredencialUsuario) -> None:
        """Crea el usuario o reemplaza el existente (mismo nombre de usuario)."""
        raise NotImplementedError

    @abstractmethod
    def registrar_resultado_acceso(self, nombre_usuario: str, intentos_fallidos: int, bloqueado_hasta: Optional[datetime]) -> None:
        raise NotImplementedError

    @abstractmethod
    def listar(self) -> list[CredencialUsuario]:
        raise NotImplementedError


class SesionRepository(ABC):
    @abstractmethod
    def crear(self, sesion: Sesion) -> None:
        raise NotImplementedError

    @abstractmethod
    def obtener(self, huella_token: str) -> Optional[Sesion]:
        raise NotImplementedError

    @abstractmethod
    def registrar_actividad(self, huella_token: str, momento: datetime) -> None:
        raise NotImplementedError

    @abstractmethod
    def revocar(self, huella_token: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def revocar_de_usuario(self, nombre_usuario: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def purgar_vencidas(self, antes_de: datetime) -> None:
        raise NotImplementedError


class AuditoriaRepository(ABC):
    @abstractmethod
    def registrar(self, registro: RegistroAuditoria) -> None:
        raise NotImplementedError

    @abstractmethod
    def listar(self, limite: int) -> list[RegistroAuditoria]:
        """Los registros mas recientes primero."""
        raise NotImplementedError

    @abstractmethod
    def contar_fallos_desde_ip(self, ip: str, desde: datetime) -> int:
        raise NotImplementedError
