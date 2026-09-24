from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from application.dtos.embalse_dto import EmbalseDetalleDTO, ResumenNacionalDTO
from application.dtos.prediccion_dto import PrediccionDTO
from application.dtos.senda_volumen_dto import SendaVolumenDTO


class ObtenerResumenNacionalPort(ABC):
    """Puerto de entrada: caso de uso invocado por la capa de presentacion
    para construir el resumen nacional (KPIs + regiones + embalses)."""

    @abstractmethod
    def ejecutar(
        self,
        regiones: Optional[list[str]] = None,
        embalses: Optional[list[str]] = None,
        fecha: Optional[date] = None,
    ) -> ResumenNacionalDTO:
        raise NotImplementedError


class ListarEmbalsesPort(ABC):
    @abstractmethod
    def ejecutar(
        self,
        region: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> list[EmbalseDetalleDTO]:
        raise NotImplementedError


class ObtenerDetalleEmbalsePort(ABC):
    @abstractmethod
    def ejecutar(
        self,
        embalse_id: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> EmbalseDetalleDTO:
        raise NotImplementedError


class GenerarPrediccionPort(ABC):
    @abstractmethod
    def ejecutar(self, embalse_id: str, horizonte_dias: int) -> PrediccionDTO:
        raise NotImplementedError


class ObtenerSendaVolumenPort(ABC):
    """Puerto de entrada: senda mensual observada + proyectada de %V. util,
    con validacion walk-forward, para un embalse o el agregado ('TOTAL')."""

    @abstractmethod
    def ejecutar(self, embalse_id: str = "TOTAL", horizonte_meses: int = 12) -> SendaVolumenDTO:
        raise NotImplementedError
