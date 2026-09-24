from __future__ import annotations

from abc import ABC, abstractmethod

from domain.entities.proyeccion_senda import ProyeccionSendaMensual


class ProyeccionSendaRepository(ABC):
    @abstractmethod
    def obtener(self, embalse_id: str) -> list[ProyeccionSendaMensual]:
        """Proyeccion del embalse ordenada por mes; vacia si no hay una publicada."""
        raise NotImplementedError

    @abstractmethod
    def reemplazar_todas(self, proyecciones: list[ProyeccionSendaMensual]) -> None:
        """Sustituye la proyeccion completa por la de la nueva corrida."""
        raise NotImplementedError
