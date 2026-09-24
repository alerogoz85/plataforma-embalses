from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import VolumenInvalidoError


@dataclass(frozen=True, slots=True)
class Volumen:
    """Volumen de agua expresado en millones de metros cubicos (Mm3)."""

    valor_mm3: float

    def __post_init__(self) -> None:
        if self.valor_mm3 < 0:
            raise VolumenInvalidoError(
                f"El volumen no puede ser negativo, se recibio {self.valor_mm3}"
            )

    def a_metros_cubicos(self) -> float:
        return self.valor_mm3 * 1_000_000

    def __add__(self, otro: "Volumen") -> "Volumen":
        return Volumen(self.valor_mm3 + otro.valor_mm3)

    def __sub__(self, otro: "Volumen") -> "Volumen":
        return Volumen(max(0.0, self.valor_mm3 - otro.valor_mm3))

    def __str__(self) -> str:
        return f"{self.valor_mm3:,.2f} Mm3"
