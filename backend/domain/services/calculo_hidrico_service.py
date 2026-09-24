from __future__ import annotations

from datetime import date
from typing import Optional

from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.value_objects.porcentaje import Porcentaje


class CalculoHidricoService:
    """Reglas de calculo hidrico: funciones puras sobre entidades y value
    objects, sin dependencias de infraestructura."""

    @staticmethod
    def calcular_porcentaje_volumen_util(medicion: MedicionHidrologica) -> Porcentaje:
        """%V_util = volumen util del dia / capacidad util del dia * 100.

        La capacidad util es la que XM publica ese mismo dia, porque XM la
        revisa con el tiempo.
        """
        capacidad = medicion.capacidad_util.valor_mm3
        if capacidad <= 0:
            return Porcentaje(0.0)
        return Porcentaje(medicion.volumen_util.valor_mm3 / capacidad * 100)

    @staticmethod
    def calcular_delta_porcentual(
        porcentaje_actual: Porcentaje, porcentaje_anterior: Porcentaje
    ) -> float:
        """Variacion en puntos porcentuales entre dos mediciones de %V_util."""
        return round(porcentaje_actual.valor - porcentaje_anterior.valor, 2)

    @staticmethod
    def calcular_aportes_pct_media(medicion: MedicionHidrologica) -> Optional[float]:
        """Aportes del dia como % de la media historica; None si falta alguno."""
        if medicion.aportes is None or not medicion.aportes_media_historica_m3s:
            return None
        return medicion.aportes.porcentaje_de_media_historica(
            medicion.aportes_media_historica_m3s
        )

    @staticmethod
    def calcular_capacidad_guardada_gwh(medicion: MedicionHidrologica) -> float:
        """Energia almacenada en el volumen util del dia (dato real de XM);
        0 si XM no la publico ese dia."""
        return medicion.energia_util_gwh or 0.0

    @staticmethod
    def calcular_peso_energetico_agregacion(medicion: MedicionHidrologica) -> float:
        """Peso al agregar %V_util por region o pais: la capacidad util en
        energia (GWh) del dia. Es la convencion de la metrica oficial de XM
        «% Volumen Util Diario (GWh)», que pondera por energia y no por
        volumen crudo: un embalse de caida alta almacena mucha mas energia
        por m3 que uno de caida baja."""
        return medicion.capacidad_util_energia_gwh

    @staticmethod
    def agregar_pct_mensual(serie_diaria: list[tuple[date, float]]) -> list[tuple[date, float]]:
        """Agrega una serie diaria de %V_util a promedios mensuales.

        Cada mes se representa con la fecha de su ultimo dia observado (para
        poder encadenar la proyeccion a partir de ahi) y el promedio de los
        valores diarios disponibles en ese mes.
        """
        acumulado: dict[tuple[int, int], list[float]] = {}
        ultima_fecha_del_mes: dict[tuple[int, int], date] = {}
        for fecha, valor in sorted(serie_diaria, key=lambda par: par[0]):
            clave = (fecha.year, fecha.month)
            acumulado.setdefault(clave, []).append(valor)
            ultima_fecha_del_mes[clave] = fecha

        return [
            (ultima_fecha_del_mes[clave], round(sum(valores) / len(valores), 2))
            for clave, valores in sorted(acumulado.items())
        ]
