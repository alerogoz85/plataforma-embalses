from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from domain.entities.medicion_hidrologica import MedicionHidrologica


class MedicionRepository(ABC):
    """Puerto de salida: contrato de persistencia para series de mediciones."""

    @abstractmethod
    def obtener_serie(
        self,
        embalse_id: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> list[MedicionHidrologica]:
        raise NotImplementedError

    @abstractmethod
    def obtener_ultima_medicion(self, embalse_id: str) -> Optional[MedicionHidrologica]:
        raise NotImplementedError

    @abstractmethod
    def obtener_medicion_en_fecha(
        self, embalse_id: str, fecha: date
    ) -> Optional[MedicionHidrologica]:
        raise NotImplementedError

    @abstractmethod
    def obtener_ultima_fecha(self) -> Optional[date]:
        """Fecha mas reciente con datos en todo el repositorio (para
        sincronizaciones incrementales)."""
        raise NotImplementedError

    @abstractmethod
    def guardar_lote(self, mediciones: list[MedicionHidrologica]) -> None:
        raise NotImplementedError
