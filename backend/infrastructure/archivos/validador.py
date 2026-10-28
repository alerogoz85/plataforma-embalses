"""Validacion de seguridad de un archivo subido, ANTES de que nadie lo abra con un lector de datos.

Que se comprueba (todo lo que no pase se rechaza con un motivo claro; nada se «arregla» en silencio):
* nombre: sin rutas ni caracteres de control, largo acotado, extension de la lista cerrada de ese archivo y, si el archivo lo pide, nombre exacto;
* tamaño: no vacio y por debajo del limite (`MAX_UPLOAD_BYTES`, 4 MB por defecto: el tope de una funcion de Vercel);
* contenido real, no el declarado: Excel debe ser un ZIP con la estructura de un libro .xlsx, sin macros, sin vinculos externos, sin
  entradas cifradas ni rutas peligrosas y sin ser una bomba de compresion; CSV y JSON deben ser UTF-8 validos (sin bytes nulos); Parquet
  lleva su marca «PAR1» al inicio y al final.
El nombre que envia el navegador nunca se usa como ruta: cada archivo se guarda donde dice el catalogo."""
from __future__ import annotations

import io
import json
import os
import re
import zipfile
from pathlib import PurePosixPath

from domain.entities.actualizacion import ArchivoRequerido

LIMITE_POR_DEFECTO = 4 * 1024 * 1024
LIMITE_TOTAL_POR_DEFECTO = 4_400_000  # una peticion a una funcion de Vercel admite 4,5 MB en total
LIMITE_CONTENIDO_POR_DEFECTO = 60 * 1024 * 1024  # CSV/JSON ya descomprimidos
MAX_ENTRADAS_ZIP = 2000
MAX_DESCOMPRIMIDO = 120 * 1024 * 1024
MAX_RAZON_COMPRESION = 200
MAX_LARGO_NOMBRE = 150
PROFUNDIDAD_JSON = 50
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def limite_de_bytes() -> int:
    """Tamaño maximo por archivo; configurable (sube en un servidor propio, no en Vercel)."""
    try:
        valor = int(os.environ.get("MAX_UPLOAD_BYTES", LIMITE_POR_DEFECTO))
    except ValueError:
        return LIMITE_POR_DEFECTO
    return valor if valor > 0 else LIMITE_POR_DEFECTO


def _limite_env(nombre: str, defecto: int) -> int:
    try:
        valor = int(os.environ.get(nombre, defecto))
    except ValueError:
        return defecto
    return valor if valor > 0 else defecto


def limite_total_de_bytes() -> int:
    """Suma maxima de los archivos de una peticion (lo que se envia por la red, ya comprimido)."""
    return _limite_env("MAX_UPLOAD_TOTAL_BYTES", LIMITE_TOTAL_POR_DEFECTO)


def limite_de_contenido() -> int:
    """Tamaño maximo de un CSV o JSON ya descomprimido."""
    return _limite_env("MAX_CONTENT_BYTES", LIMITE_CONTENIDO_POR_DEFECTO)


def _extension(nombre: str) -> str:
    return nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""


def validar_nombre(requerido: ArchivoRequerido, nombre: str) -> list[str]:
    errores: list[str] = []
    if not nombre or len(nombre) > MAX_LARGO_NOMBRE:
        return [f"{requerido.etiqueta}: el nombre del archivo es obligatorio y de máximo {MAX_LARGO_NOMBRE} caracteres"]
    if _CONTROL.search(nombre) or "/" in nombre or "\\" in nombre or nombre.startswith(".") or ".." in nombre:
        errores.append(f"{requerido.etiqueta}: el nombre del archivo tiene caracteres no permitidos")
    ext = _extension(nombre)
    if ext not in requerido.formatos:
        errores.append(f"{requerido.etiqueta}: formato «.{ext or '?'}» no admitido (se aceptan: {', '.join('.' + f for f in requerido.formatos)})")
    if requerido.patron_nombre and not re.fullmatch(requerido.patron_nombre, nombre):
        errores.append(f"{requerido.etiqueta}: el nombre «{nombre[:60]}» no tiene la forma esperada")
    return errores


def _validar_xlsx(contenido: bytes, etiqueta: str) -> list[str]:
    if not contenido.startswith(b"PK\x03\x04"):
        return [f"{etiqueta}: no es un libro de Excel .xlsx válido (el contenido no corresponde a la extensión)"]
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as z:
            entradas = z.infolist()
            nombres = [e.filename for e in entradas]
            if len(entradas) > MAX_ENTRADAS_ZIP:
                return [f"{etiqueta}: el libro tiene demasiadas partes internas"]
            total = sum(e.file_size for e in entradas)
            comprimido = max(1, sum(e.compress_size for e in entradas))
            if total > MAX_DESCOMPRIMIDO or total / comprimido > MAX_RAZON_COMPRESION:
                return [f"{etiqueta}: el libro se expande de forma sospechosa (posible bomba de compresión)"]
            errores: list[str] = []
            if "[Content_Types].xml" not in nombres or "xl/workbook.xml" not in nombres:
                errores.append(f"{etiqueta}: no tiene la estructura de un libro de Excel")
            if any(n.startswith("/") or ".." in PurePosixPath(n).parts or "\\" in n for n in nombres):
                errores.append(f"{etiqueta}: contiene rutas internas no permitidas")
            if any("vbaproject" in n.lower() or n.lower().startswith("xl/macrosheets") for n in nombres):
                errores.append(f"{etiqueta}: contiene macros; solo se aceptan libros sin macros")
            if any(n.lower().startswith("xl/externallinks/") for n in nombres):
                errores.append(f"{etiqueta}: contiene vínculos a libros externos")
            if any(e.flag_bits & 0x1 for e in entradas):
                errores.append(f"{etiqueta}: el libro está cifrado o protegido con contraseña")
            return errores
    except zipfile.BadZipFile:
        return [f"{etiqueta}: el archivo está dañado o no es un .xlsx"]


def _texto_utf8(contenido: bytes, etiqueta: str) -> tuple[str | None, list[str]]:
    if b"\x00" in contenido:
        return None, [f"{etiqueta}: contiene bytes nulos; no es un archivo de texto"]
    try:
        return contenido.decode("utf-8-sig"), []
    except UnicodeDecodeError:
        return None, [f"{etiqueta}: el archivo debe estar codificado en UTF-8"]


def _validar_csv(contenido: bytes, etiqueta: str) -> list[str]:
    texto, errores = _texto_utf8(contenido, etiqueta)
    if texto is not None and not texto.strip():
        errores.append(f"{etiqueta}: el archivo está vacío")
    elif texto is not None and "\n" not in texto.strip() and "\r" not in texto.strip():
        errores.append(f"{etiqueta}: debe tener un encabezado y al menos una fila de datos")
    return errores


def _profundidad(valor: object, nivel: int = 0) -> int:
    if nivel > PROFUNDIDAD_JSON:
        return nivel
    if isinstance(valor, dict):
        return max([_profundidad(v, nivel + 1) for v in valor.values()] or [nivel + 1])
    if isinstance(valor, list):
        return max([_profundidad(v, nivel + 1) for v in valor] or [nivel + 1])
    return nivel


def _validar_json(contenido: bytes, etiqueta: str) -> list[str]:
    texto, errores = _texto_utf8(contenido, etiqueta)
    if texto is None:
        return errores
    try:
        valor = json.loads(texto)
    except (ValueError, RecursionError):
        return [f"{etiqueta}: no es un JSON válido"]
    if not isinstance(valor, (dict, list)):
        return [f"{etiqueta}: el JSON debe ser un objeto o una lista"]
    if _profundidad(valor) > PROFUNDIDAD_JSON:
        return [f"{etiqueta}: el JSON está anidado de forma excesiva"]
    return []


def _validar_parquet(contenido: bytes, etiqueta: str) -> list[str]:
    if not (contenido.startswith(b"PAR1") and contenido.endswith(b"PAR1")):
        return [f"{etiqueta}: no es un archivo Parquet válido"]
    return []


_POR_FORMATO = {"xlsx": _validar_xlsx, "csv": _validar_csv, "json": _validar_json, "parquet": _validar_parquet}


def validar_archivo(requerido: ArchivoRequerido, nombre: str, contenido: bytes) -> list[str]:
    """Todos los motivos por los que el archivo no se acepta (lista vacia = pasa la revision de seguridad)."""
    errores = validar_nombre(requerido, nombre)
    if errores:
        return errores
    if not contenido:
        return [f"{requerido.etiqueta}: el archivo está vacío"]
    # xlsx y parquet ya vienen comprimidos: su tamaño es el de la red. CSV y JSON pueden llegar en .gz y se miden descomprimidos.
    limite = limite_de_contenido() if _extension(nombre) in ("csv", "json") else limite_de_bytes()
    if len(contenido) > limite:
        return [f"{requerido.etiqueta}: pesa {len(contenido) / 1_048_576:.1f} MB y el máximo es {limite / 1_048_576:.1f} MB"]
    return _POR_FORMATO[_extension(nombre)](contenido, requerido.etiqueta)
