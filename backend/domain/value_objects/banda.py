from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Banda:
    """Escenarios de una variable proyectada: P10 (bajo), P50 (central) y P90 (alto).

    Son percentiles de una simulacion Monte Carlo, no un intervalo de confianza
    estadistico. Se exige P10 <= P50 <= P90 para que la banda sea coherente."""

    p10: float
    p50: float
    p90: float

    def __post_init__(self) -> None:
        if not self.p10 <= self.p50 <= self.p90:
            raise ValueError(
                f"Banda inconsistente: se espera P10 <= P50 <= P90 y llego "
                f"{self.p10}, {self.p50}, {self.p90}"
            )
