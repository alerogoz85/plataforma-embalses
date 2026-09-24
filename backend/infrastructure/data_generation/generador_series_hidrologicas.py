"""Generador autosuficiente de series temporales hidrologicas sinteticas.

No depende de dominio/aplicacion: produce estructuras de datos crudas
(RegistroSintetico) que luego el script de seed traduce a entidades de
dominio antes de persistirlas. Esto mantiene el generador reutilizable
tambien para pruebas de carga o notebooks de analisis exploratorio.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from infrastructure.data_generation.catalogo_embalses import (
    CATALOGO_EMBALSES,
    DefinicionEmbalse,
)

SEGUNDOS_POR_DIA = 86_400

# Factor climatologico mensual del regimen bimodal andino colombiano
# (lluvias en abril-mayo y octubre-noviembre); 1.0 representa la media anual.
FACTOR_ESTACIONAL_MENSUAL = {
    1: 0.75, 2: 0.80, 3: 0.95, 4: 1.25, 5: 1.35, 6: 1.05,
    7: 0.80, 8: 0.75, 9: 0.95, 10: 1.30, 11: 1.35, 12: 1.00,
}
MESES_SECOS = {1, 2, 7, 8}

PCT_UTIL_MINIMO = 2.0
PCT_UTIL_MAXIMO = 99.5
UMBRAL_PCT_VERTIMIENTO = 90.0
FACTOR_CORRECCION_OBJETIVO = 0.02


@dataclass(frozen=True, slots=True)
class RegistroSintetico:
    embalse_id: str
    fecha: date
    volumen_util_mm3: float
    aportes_m3s: float
    aportes_media_historica_m3s: float
    vertimientos_m3s: float
    turbinado_m3s: float


class GeneradorSeriesHidrologicas:
    """Simula, por embalse, una serie diaria hidrologicamente coherente
    mediante un balance de masa porcentual: el %V_util del dia siguiente es
    el actual mas los aportes menos turbinado, vertimientos y evaporacion,
    todos expresados como variacion porcentual del volumen util maximo.
    """

    def __init__(self, semilla: int = 42) -> None:
        self._semilla = semilla

    def catalogo(self) -> list[DefinicionEmbalse]:
        return list(CATALOGO_EMBALSES)

    def generar_serie(
        self, definicion: DefinicionEmbalse, fecha_inicio: date, fecha_fin: date
    ) -> list[RegistroSintetico]:
        rng = random.Random(f"{self._semilla}-{definicion.id}")
        volumen_util_maximo = definicion.volumen_maximo_mm3 - definicion.volumen_muerto_mm3
        pct_util = definicion.pct_volumen_util_inicial
        anomalia_previa = 0.0

        registros: list[RegistroSintetico] = []
        dias_totales = (fecha_fin - fecha_inicio).days + 1

        for i in range(dias_totales):
            fecha = fecha_inicio + timedelta(days=i)
            media_historica = definicion.aportes_media_base_m3s * FACTOR_ESTACIONAL_MENSUAL[
                fecha.month
            ]

            anomalia_previa = 0.6 * anomalia_previa + rng.gauss(0, 0.18)
            aportes_m3s = max(0.0, media_historica * (1 + anomalia_previa))

            vertimientos_m3s = self._estimar_vertimiento(pct_util, aportes_m3s)
            evaporacion_m3s = self._estimar_evaporacion(definicion, fecha.month)
            turbinado_pct = self._estimar_turbinado_pct(definicion, pct_util)

            aportes_pct = self._m3s_a_pct_volumen(aportes_m3s, volumen_util_maximo)
            vertimientos_pct = self._m3s_a_pct_volumen(vertimientos_m3s, volumen_util_maximo)
            evaporacion_pct = self._m3s_a_pct_volumen(evaporacion_m3s, volumen_util_maximo)

            pct_util = pct_util + aportes_pct - turbinado_pct - vertimientos_pct - evaporacion_pct
            pct_util = max(PCT_UTIL_MINIMO, min(PCT_UTIL_MAXIMO, pct_util))

            volumen_util_mm3 = (pct_util / 100) * volumen_util_maximo
            turbinado_m3s = (
                turbinado_pct / 100 * volumen_util_maximo * 1_000_000 / SEGUNDOS_POR_DIA
            )

            registros.append(
                RegistroSintetico(
                    embalse_id=definicion.id,
                    fecha=fecha,
                    volumen_util_mm3=round(volumen_util_mm3, 3),
                    aportes_m3s=round(aportes_m3s, 3),
                    aportes_media_historica_m3s=round(media_historica, 3),
                    vertimientos_m3s=round(vertimientos_m3s, 3),
                    turbinado_m3s=round(turbinado_m3s, 3),
                )
            )

        return registros

    @staticmethod
    def _m3s_a_pct_volumen(caudal_m3s: float, volumen_util_maximo_mm3: float) -> float:
        if volumen_util_maximo_mm3 <= 0:
            return 0.0
        volumen_diario_mm3 = (caudal_m3s * SEGUNDOS_POR_DIA) / 1_000_000
        return (volumen_diario_mm3 / volumen_util_maximo_mm3) * 100

    @staticmethod
    def _estimar_turbinado_pct(definicion: DefinicionEmbalse, pct_util: float) -> float:
        """Politica de operacion: se turbina mas agua cuanto mas por encima
        del nivel objetivo este el embalse, y menos cuando esta por debajo.
        Esta realimentacion negativa evita que la simulacion derive
        indefinidamente hacia los limites y mantiene el embalse oscilando
        en torno a su rango operativo historico.
        """
        factor_disponibilidad = min(1.0, max(0.2, pct_util / 70))
        base_pct = (definicion.capacidad_instalada_mw / 500) * 0.35
        correccion_objetivo = (pct_util - definicion.pct_volumen_util_inicial) * FACTOR_CORRECCION_OBJETIVO
        return max(0.05, base_pct * factor_disponibilidad + correccion_objetivo)

    @staticmethod
    def _estimar_vertimiento(pct_util: float, aportes_m3s: float) -> float:
        if pct_util < UMBRAL_PCT_VERTIMIENTO:
            return max(0.0, aportes_m3s * 0.01)
        exceso = (pct_util - UMBRAL_PCT_VERTIMIENTO) / (100 - UMBRAL_PCT_VERTIMIENTO)
        return aportes_m3s * (0.05 + 0.6 * exceso)

    @staticmethod
    def _estimar_evaporacion(definicion: DefinicionEmbalse, mes: int) -> float:
        factor_seco = 1.3 if mes in MESES_SECOS else 1.0
        superficie_proxy = definicion.volumen_maximo_mm3 ** 0.5
        return 0.002 * superficie_proxy * factor_seco
