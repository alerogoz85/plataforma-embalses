from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Listas cerradas: son las unicas que acepta la API (cualquier otro valor responde 422).
PERIODOS_PERMITIDOS_MESES = (12, 36, 60, 0)  # 0 = todo el historico
ORIGENES_PERMITIDOS = ("programada", "no_programada")


@dataclass(frozen=True)
class FiltroDns:
    """Filtros globales del tablero DNS. Todos los bloques calculados sobre eventos los respetan.

    * periodo_meses: ventana que termina en el mes del ultimo evento (0 = todo el historico)
    * region / subarea: ambito geografico (la subarea gana si ambas vienen)
    * origen: solo eventos programados o no programados (None = ambos)"""

    periodo_meses: int = 36
    region: Optional[str] = None
    subarea: Optional[str] = None
    origen: Optional[str] = None

    def __post_init__(self) -> None:
        if self.periodo_meses not in PERIODOS_PERMITIDOS_MESES:
            raise ValueError(f"periodo_meses debe ser uno de {PERIODOS_PERMITIDOS_MESES}")
        if self.origen is not None and self.origen not in ORIGENES_PERMITIDOS:
            raise ValueError(f"origen debe ser uno de {ORIGENES_PERMITIDOS}")
