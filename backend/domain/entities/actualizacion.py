"""Actualizacion de archivos de los tableros: que tableros se pueden actualizar, que archivos pide cada uno y como se reporta la validacion."""
from __future__ import annotations

from dataclasses import dataclass, field

FORMATOS = ("xlsx", "csv", "json", "parquet")


@dataclass(frozen=True)
class ArchivoRequerido:
    """Un archivo del paquete de un tablero. El nombre que trae el navegador NUNCA decide donde se guarda:
    cada archivo se ubica por su `clave`, en la ruta fija `ruta` (salvo `patron_nombre`, que valida el nombre exacto)."""

    clave: str
    etiqueta: str
    ruta: str  # relativa a la carpeta del paquete; con patron_nombre, es la carpeta donde va el archivo
    formatos: tuple[str, ...]
    obligatorio: bool = True
    patron_nombre: str | None = None  # expresion regular del nombre del archivo, p. ej. DNS pronostico_AAAA-MM.csv
    descripcion: str = ""

    def __post_init__(self) -> None:
        if not self.formatos or any(f not in FORMATOS for f in self.formatos):
            raise ValueError(f"Formatos admitidos: {', '.join(FORMATOS)}")


@dataclass(frozen=True)
class TableroActualizable:
    id: str
    titulo: str
    descripcion: str
    archivos: tuple[ArchivoRequerido, ...]

    def __post_init__(self) -> None:
        claves = [a.clave for a in self.archivos]
        if len(claves) != len(set(claves)):
            raise ValueError(f"Las claves de archivo de '{self.id}' deben ser unicas")


@dataclass(frozen=True)
class ArchivoRecibido:
    """Archivo ya leido en memoria (con su tamaño acotado) y su huella sha256."""

    clave: str
    nombre: str
    contenido: bytes
    huella: str


@dataclass(frozen=True)
class ResultadoValidacion:
    """Informe de validar (sin escribir) o de aplicar una carga."""

    valido: bool
    resumen: tuple[tuple[str, str], ...] = ()
    errores: tuple[str, ...] = ()
    advertencias: tuple[str, ...] = ()
    huellas: tuple[tuple[str, str], ...] = field(default=())  # (clave, sha256) de los archivos revisados
