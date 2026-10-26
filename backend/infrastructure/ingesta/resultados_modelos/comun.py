"""Utilidades comunes de los lectores de salidas de los modelos analiticos."""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

TOPE_FILAS_TABLA = 300  # una tabla del tablero es para leerla, no un volcado de datos


class SalidaModeloInvalidaError(Exception):
    """Un archivo de salida de un modelo falta o no cumple el formato esperado."""


def leer_csv(ruta: Path, columnas: set[str]) -> list[dict[str, str]]:
    if not ruta.is_file():
        raise SalidaModeloInvalidaError(f"falta el archivo {ruta}")
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        lector = csv.DictReader(f)
        faltan = columnas - set(lector.fieldnames or [])
        if faltan:
            raise SalidaModeloInvalidaError(f"{ruta.name}: faltan columnas {sorted(faltan)}")
        filas = list(lector)
    if not filas:
        raise SalidaModeloInvalidaError(f"{ruta.name} no tiene filas")
    return filas


def leer_json(ruta: Path, *, obligatorio: bool) -> Optional[Any]:
    if not ruta.is_file():
        if obligatorio:
            raise SalidaModeloInvalidaError(f"falta el archivo {ruta}")
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SalidaModeloInvalidaError(f"{ruta.name} no es un JSON valido: {error}") from error


def numero(valor: Any, archivo: str, columna: str, *, opcional: bool = False) -> Optional[float]:
    """Convierte a float; vacio/NaN solo se permite si `opcional`. Nunca devuelve NaN ni infinito."""
    if valor is None or (isinstance(valor, str) and valor.strip() == ""):
        if opcional:
            return None
        raise SalidaModeloInvalidaError(f"{archivo}: valor vacio en '{columna}'")
    try:
        n = float(valor)
    except (TypeError, ValueError) as error:
        raise SalidaModeloInvalidaError(f"{archivo}: '{columna}' no es un numero: {valor!r}") from error
    if not math.isfinite(n):
        if opcional:
            return None
        raise SalidaModeloInvalidaError(f"{archivo}: '{columna}' no es finito")
    return n


def mes_iso(valor: str, archivo: str) -> str:
    """'2026-08-01' o '2026-08-01 00:00:00' -> '2026-08'."""
    try:
        return datetime.fromisoformat(valor.strip()[:19]).strftime("%Y-%m")
    except ValueError as error:
        raise SalidaModeloInvalidaError(f"{archivo}: fecha invalida {valor!r}") from error


def momento_de(ruta: Path) -> datetime:
    """Cuando se genero la salida: la fecha de modificacion del archivo principal."""
    return datetime.fromtimestamp(ruta.stat().st_mtime).replace(microsecond=0)


def celda(valor: Any) -> Any:
    """Valor de tabla listo para guardar: numeros redondeados, NaN -> None, el resto como texto."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    if isinstance(valor, (int, float)):
        return round(float(valor), 4) if math.isfinite(float(valor)) else None
    if isinstance(valor, datetime):
        return valor.strftime("%Y-%m-%d")
    texto = str(valor).strip()
    return texto or None
