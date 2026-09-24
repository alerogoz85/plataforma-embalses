from __future__ import annotations

from dataclasses import dataclass

from domain.exceptions import CaudalInvalidoError

SEGUNDOS_POR_DIA = 86_400


@dataclass(frozen=True, slots=True)
class Caudal:
    """Caudal expresado en metros cubicos por segundo (m3/s)."""

    valor_m3s: float

    def __post_init__(self) -> None:
        if self.valor_m3s < 0:
            raise CaudalInvalidoError(
                f"El caudal no puede ser negativo, se recibio {self.valor_m3s}"
            )

    def a_volumen_diario_mm3(self) -> float:
        """Convierte el caudal a volumen equivalente en un dia, en Mm3."""
        return (self.valor_m3s * SEGUNDOS_POR_DIA) / 1_000_000

    def porcentaje_de_media_historica(self, media_historica_m3s: float) -> float:
        if media_historica_m3s <= 0:
            return 0.0
        return round((self.valor_m3s / media_historica_m3s) * 100, 2)

    def __str__(self) -> str:
        return f"{self.valor_m3s:,.2f} m3/s"
