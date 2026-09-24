from __future__ import annotations

from typing import Optional

from domain.entities.medicion_hidrologica import MedicionHidrologica


class AutonomiaService:
    """Estima los dias que tardaria el embalse en agotar su volumen util.

    Balance diario = descarga turbinada + vertimientos - aportes. XM no
    publica evaporacion, asi que no se incluye; la turbinada si, porque es la
    principal salida real. Si falta alguno de los tres datos no se estima
    (None), y si los aportes superan las salidas no hay horizonte de
    agotamiento (tambien None).

    Es una estimacion aproximada: los aportes son los de la serie de rio
    asociada al embalse y no incluyen otras entradas.
    """

    @staticmethod
    def calcular_dias_autonomia(medicion: MedicionHidrologica) -> Optional[int]:
        if medicion.aportes is None or medicion.turbinado is None or medicion.vertimientos is None:
            return None

        salida_diaria_mm3 = (
            medicion.turbinado.a_volumen_diario_mm3() + medicion.vertimientos.a_volumen_diario_mm3()
        )
        balance_neto_mm3 = salida_diaria_mm3 - medicion.aportes.a_volumen_diario_mm3()
        if balance_neto_mm3 <= 0:
            return None

        volumen_disponible_mm3 = medicion.volumen_util.valor_mm3
        if volumen_disponible_mm3 <= 0:
            return 0
        return max(0, int(volumen_disponible_mm3 / balance_neto_mm3))
