from __future__ import annotations

from dataclasses import dataclass

from domain.entities.region import Region


@dataclass(frozen=True, slots=True)
class Embalse:
    """Embalse identificado por su codigo XM/SIMEM.

    Los datos que cambian con el tiempo (capacidad util, volumen, energia)
    viven en MedicionHidrologica: XM revisa las capacidades de los embalses,
    por lo que no son invariantes del embalse.

    `es_agregado` marca entidades que XM publica como agregado de varios
    embalses (p. ej. el agregado Bogota) y que entran al total nacional.
    """

    id: str
    nombre: str
    region: Region
    es_agregado: bool = False
