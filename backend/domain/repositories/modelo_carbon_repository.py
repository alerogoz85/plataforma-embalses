from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.modelo_carbon import PaqueteModeloCarbon


class ModeloCarbonRepository(ABC):
    """Puerto de salida: persistencia de la corrida vigente del modelo de carbon."""

    @abstractmethod
    def obtener(self) -> Optional[PaqueteModeloCarbon]:
        """La corrida vigente, o None si aun no se ha importado ninguna."""
        raise NotImplementedError

    @abstractmethod
    def reemplazar(self, paquete: PaqueteModeloCarbon) -> None:
        """Sustituye por completo la corrida vigente por una nueva."""
        raise NotImplementedError
