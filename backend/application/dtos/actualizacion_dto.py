"""DTOs del modulo de actualizacion de tableros (/api/v1/admin/*)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_serializer


class UsuarioDTO(BaseModel):
    nombre_usuario: str
    nombre: str
    rol: str
    tableros: list[str]


class SesionDTO(BaseModel):
    usuario: UsuarioDTO
    token_csrf: str
    vence_en: datetime

    @field_serializer("vence_en")
    def _utc(self, v: datetime) -> str:
        return v.isoformat() + "Z"  # los instantes se guardan en UTC sin zona; se entregan con «Z» para que el navegador los convierta bien


class ArchivoRequeridoDTO(BaseModel):
    clave: str
    etiqueta: str
    formatos: list[str]
    obligatorio: bool
    descripcion: str
    patron_nombre: Optional[str] = None


class TableroActualizableDTO(BaseModel):
    id: str
    titulo: str
    descripcion: str
    archivos: list[ArchivoRequeridoDTO]


class CatalogoActualizacionDTO(BaseModel):
    tableros: list[TableroActualizableDTO]
    limite_bytes: int
    limite_total_bytes: int
    limite_contenido_bytes: int
    almacenamiento_persistente: bool


class DatoResumenDTO(BaseModel):
    etiqueta: str
    valor: str


class HuellaArchivoDTO(BaseModel):
    clave: str
    sha256: str


class ResultadoCargaDTO(BaseModel):
    """Informe de validar o aplicar: `valido` indica si los archivos pasaron todas las revisiones; `aplicada` si se escribio en la base."""

    tablero: str
    valido: bool
    aplicada: bool
    resumen: list[DatoResumenDTO]
    errores: list[str]
    advertencias: list[str]
    huellas: list[HuellaArchivoDTO]


class RegistroAuditoriaDTO(BaseModel):
    momento: datetime
    usuario: str
    accion: str
    tablero: Optional[str]
    resultado: str
    detalle: str
    ip: str

    @field_serializer("momento")
    def _utc(self, v: datetime) -> str:
        return v.isoformat() + "Z"
