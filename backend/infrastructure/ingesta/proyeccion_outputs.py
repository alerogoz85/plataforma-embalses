"""Lectura de la proyeccion de largo plazo del modelo de Outputs
(`proyeccion_montecarlo_enso <fecha>.xlsx`).

Columnas esperadas: CodigoEmbalse, Fecha (primer dia del mes), P10, P50, Promedio, P90,
con los porcentajes como fraccion (0-1). El valor central que se publica es el P50 y
los limites son P10/P90. Se convierten a puntos porcentuales (0-100).
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import openpyxl

from domain.entities.proyeccion_senda import ProyeccionSendaMensual

COLUMNAS_REQUERIDAS = ("CodigoEmbalse", "Fecha", "P10", "P50", "P90")
MAXIMO_FRACCION = 1.05  # margen sobre 1.0; por encima se asume que ya viene en %


class ArchivoProyeccionInvalidoError(ValueError):
    pass


def _a_fecha(valor: object, fila: int) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    raise ArchivoProyeccionInvalidoError(f"Fila {fila}: Fecha no valida ({valor!r})")


def _a_porcentaje(valor: object, nombre: str, fila: int) -> float:
    if not isinstance(valor, (int, float)) or isinstance(valor, bool):
        raise ArchivoProyeccionInvalidoError(f"Fila {fila}: {nombre} no es numerico ({valor!r})")
    if not 0 <= valor <= MAXIMO_FRACCION:
        raise ArchivoProyeccionInvalidoError(
            f"Fila {fila}: {nombre}={valor} fuera de 0-1; se esperaba una fraccion, no un porcentaje"
        )
    return round(valor * 100, 4)


def convertir_filas(filas: Iterable[tuple], origen: str) -> list[ProyeccionSendaMensual]:
    """Convierte las filas (la primera es el encabezado) en proyecciones del dominio."""
    iterador = iter(filas)
    encabezado = next(iterador, None)
    if encabezado is None:
        raise ArchivoProyeccionInvalidoError("El archivo esta vacio")
    columnas = [str(c) if c is not None else "" for c in encabezado]
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in columnas]
    if faltantes:
        raise ArchivoProyeccionInvalidoError(f"Faltan columnas: {', '.join(faltantes)}")
    indice = {c: columnas.index(c) for c in COLUMNAS_REQUERIDAS}

    proyecciones: list[ProyeccionSendaMensual] = []
    vistos: set[tuple[str, date]] = set()
    for numero, fila in enumerate(iterador, start=2):
        if fila is None or all(celda is None for celda in fila):
            continue
        embalse_id = str(fila[indice["CodigoEmbalse"]]).strip()
        mes = _a_fecha(fila[indice["Fecha"]], numero).replace(day=1)
        if (embalse_id, mes) in vistos:
            raise ArchivoProyeccionInvalidoError(f"Fila {numero}: {embalse_id} {mes:%Y-%m} repetido")
        vistos.add((embalse_id, mes))
        proyecciones.append(
            ProyeccionSendaMensual(
                embalse_id=embalse_id,
                mes=mes,
                limite_inferior=_a_porcentaje(fila[indice["P10"]], "P10", numero),
                valor_esperado=_a_porcentaje(fila[indice["P50"]], "P50", numero),
                limite_superior=_a_porcentaje(fila[indice["P90"]], "P90", numero),
                origen=origen,
            )
        )
    if not proyecciones:
        raise ArchivoProyeccionInvalidoError("El archivo no tiene filas de datos")
    return proyecciones


def leer_proyecciones(ruta: Path, origen: str) -> list[ProyeccionSendaMensual]:
    libro = openpyxl.load_workbook(ruta, read_only=True, data_only=True)
    try:
        return convertir_filas(libro.active.iter_rows(values_only=True), origen)
    finally:
        libro.close()
