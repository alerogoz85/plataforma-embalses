"""Lectores de las salidas de cada modelo analitico: uno por modelo, todos devuelven un ResultadoModelo."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from domain.entities.modelo_analitico import ResultadoModelo
from infrastructure.ingesta.resultados_modelos.apagon import leer_apagon
from infrastructure.ingesta.resultados_modelos.comun import SalidaModeloInvalidaError
from infrastructure.ingesta.resultados_modelos.gas import leer_gas
from infrastructure.ingesta.resultados_modelos.optimizacion import leer_optimizacion

LECTORES: dict[str, Callable[[Path], ResultadoModelo]] = {
    "gas": leer_gas,
    "optimizacion": leer_optimizacion,
    "apagon": leer_apagon,
}

__all__ = ["LECTORES", "SalidaModeloInvalidaError"]
