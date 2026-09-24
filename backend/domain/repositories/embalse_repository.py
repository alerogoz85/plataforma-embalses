from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from domain.entities.embalse import Embalse
from domain.entities.region import NombreRegion


class EmbalseRepository(ABC):
    """Puerto de salida: contrato de persistencia para la entidad Embalse.

    La capa de dominio depende solo de esta interfaz; la implementacion
    concreta (DuckDB, SQLAlchemy, memoria, etc.) vive en infrastructure/.
    """

    @abstractmethod
    def obtener_por_id(self, embalse_id: str) -> Optional[Embalse]:
        raise NotImplementedError

    @abstractmethod
    def listar(self, region: Optional[NombreRegion] = None) -> list[Embalse]:
        raise NotImplementedError

    @abstractmethod
    def guardar(self, embalse: Embalse) -> None:
        raise NotImplementedError
