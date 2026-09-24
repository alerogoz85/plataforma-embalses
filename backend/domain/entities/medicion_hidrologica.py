from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from domain.value_objects.caudal import Caudal
from domain.value_objects.volumen import Volumen


@dataclass(frozen=True, slots=True)
class MedicionHidrologica:
    """Registro diario de un embalse tal como lo publica XM/SIMEM.

    Los campos opcionales son None cuando la fuente no publica el dato para
    ese embalse o dia (por ejemplo, Muna no tiene serie de aportes); nunca se
    rellenan con valores inventados.

    `capacidad_util_energia_gwh` es el peso de agregacion. Si XM no la publica
    un dia concreto, la fuente usa la ultima capacidad publicada del mismo
    embalse (cambia muy poco), pero `energia_util_gwh` queda en None.
    """

    embalse_id: str
    fecha: date
    volumen_util: Volumen
    capacidad_util: Volumen
    capacidad_util_energia_gwh: float
    energia_util_gwh: Optional[float] = None
    aportes: Optional[Caudal] = None
    aportes_media_historica_m3s: Optional[float] = None
    vertimientos: Optional[Caudal] = None
    turbinado: Optional[Caudal] = None
