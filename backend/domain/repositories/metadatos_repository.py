from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.metadatos_datos import MetadatosDatos


class MetadatosRepository(ABC):
    @abstractmethod
    def obtener(self) -> Optional[MetadatosDatos]:
        raise NotImplementedError

    @abstractmethod
    def guardar(self, metadatos: MetadatosDatos) -> None:
        raise NotImplementedError
