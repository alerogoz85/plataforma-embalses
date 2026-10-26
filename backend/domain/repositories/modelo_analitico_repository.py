from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.modelo_analitico import FichaModelo, ResultadoModelo


class FichaModeloRepository(ABC):
    """Puerto de salida: fichas documentadas de los modelos."""

    @abstractmethod
    def obtener(self, modelo_id: str) -> Optional[FichaModelo]:
        raise NotImplementedError


class ResultadoModeloRepository(ABC):
    """Puerto de salida: ultimo resultado importado de cada modelo."""

    @abstractmethod
    def obtener(self, modelo_id: str) -> Optional[ResultadoModelo]:
        """El resultado vigente del modelo, o None si aun no se ha importado ninguno."""
        raise NotImplementedError

    @abstractmethod
    def reemplazar(self, resultado: ResultadoModelo) -> None:
        """Sustituye el resultado vigente de ese modelo (los de otros modelos no se tocan)."""
        raise NotImplementedError
