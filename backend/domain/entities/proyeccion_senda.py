from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class ProyeccionSendaMensual:
    """Proyeccion mensual de %V. util publicada por el modelo de largo plazo
    (Outputs): valor central (P50) y escenarios P10/P90, en puntos porcentuales.
    `origen` describe el modelo y la corrida de la que proviene."""

    embalse_id: str
    mes: date  # primer dia del mes
    limite_inferior: float  # P10
    valor_esperado: float  # P50
    limite_superior: float  # P90
    origen: str

    def __post_init__(self) -> None:
        if not self.limite_inferior <= self.valor_esperado <= self.limite_superior:
            raise ValueError(
                f"Proyeccion inconsistente para {self.embalse_id} {self.mes:%Y-%m}: "
                f"se espera P10 <= P50 <= P90 y llego "
                f"{self.limite_inferior}, {self.valor_esperado}, {self.limite_superior}"
            )
