from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.modelo_dns import PaqueteModeloDns


class ModeloDnsRepository(ABC):
    """Puerto de salida: persistencia de la corrida vigente del modelo DNS."""

    @abstractmethod
    def obtener(self) -> Optional[PaqueteModeloDns]:
        """La corrida vigente, o None si aun no se ha importado ninguna."""
        raise NotImplementedError

    @abstractmethod
    def reemplazar(self, paquete: PaqueteModeloDns) -> None:
        """Sustituye por completo la corrida vigente por una nueva."""
        raise NotImplementedError
