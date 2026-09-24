from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from application.ports.output.forecasting_port import ForecastingPort, PuntoForecast
from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.entities.metadatos_datos import MetadatosDatos
from domain.entities.proyeccion_senda import ProyeccionSendaMensual
from domain.entities.region import NombreRegion, Region
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.repositories.metadatos_repository import MetadatosRepository
from domain.repositories.proyeccion_senda_repository import ProyeccionSendaRepository
from domain.value_objects.caudal import Caudal
from domain.value_objects.volumen import Volumen

CAPACIDAD_UTIL_MM3 = 100.0


def crear_embalse(
    id_: str, region: NombreRegion = NombreRegion.ANTIOQUIA, es_agregado: bool = False
) -> Embalse:
    return Embalse(id=id_, nombre=f"Embalse {id_}", region=Region(region), es_agregado=es_agregado)


def crear_medicion(
    embalse: Embalse,
    fecha: date,
    pct: float,
    capacidad_energia_gwh: float = 100.0,
    capacidad_mm3: float = CAPACIDAD_UTIL_MM3,
    **opcionales,
) -> MedicionHidrologica:
    """Medicion cuyo %V_util es exactamente `pct` (volumen util = pct% de la capacidad)."""
    campos = dict(
        embalse_id=embalse.id,
        fecha=fecha,
        volumen_util=Volumen(pct / 100 * capacidad_mm3),
        capacidad_util=Volumen(capacidad_mm3),
        capacidad_util_energia_gwh=capacidad_energia_gwh,
        energia_util_gwh=pct / 100 * capacidad_energia_gwh,
    )
    campos.update(opcionales)
    return MedicionHidrologica(**campos)


def serie_mensual_constante(
    embalse: Embalse,
    porcentajes_por_mes: list[float],
    capacidad_energia_gwh: float = 100.0,
    inicio: date = date(2024, 1, 1),
) -> list[MedicionHidrologica]:
    """Dos mediciones (dias 1 y 2) por mes, ambas con el mismo %V_util del mes."""
    mediciones = []
    for indice, pct in enumerate(porcentajes_por_mes):
        anio = inicio.year + (inicio.month - 1 + indice) // 12
        mes = (inicio.month - 1 + indice) % 12 + 1
        for dia in (1, 2):
            mediciones.append(
                crear_medicion(embalse, date(anio, mes, dia), pct, capacidad_energia_gwh)
            )
    return mediciones


def caudal(valor: Optional[float]) -> Optional[Caudal]:
    return Caudal(valor) if valor is not None else None


class EmbalseRepositoryEnMemoria(EmbalseRepository):
    def __init__(self, embalses: list[Embalse]) -> None:
        self._embalses = {e.id: e for e in embalses}

    def obtener_por_id(self, embalse_id: str) -> Optional[Embalse]:
        return self._embalses.get(embalse_id)

    def listar(self, region: Optional[NombreRegion] = None) -> list[Embalse]:
        return [
            e for e in self._embalses.values() if region is None or e.region.nombre == region
        ]

    def guardar(self, embalse: Embalse) -> None:
        self._embalses[embalse.id] = embalse


class MedicionRepositoryEnMemoria(MedicionRepository):
    def __init__(self, mediciones: list[MedicionHidrologica]) -> None:
        self._mediciones = {(m.embalse_id, m.fecha): m for m in mediciones}

    def _ordenadas(self) -> list[MedicionHidrologica]:
        return sorted(self._mediciones.values(), key=lambda m: (m.embalse_id, m.fecha))

    def obtener_serie(
        self,
        embalse_id: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> list[MedicionHidrologica]:
        return [
            m
            for m in self._ordenadas()
            if m.embalse_id == embalse_id
            and (fecha_inicio is None or m.fecha >= fecha_inicio)
            and (fecha_fin is None or m.fecha <= fecha_fin)
        ]

    def obtener_ultima_medicion(self, embalse_id: str) -> Optional[MedicionHidrologica]:
        serie = self.obtener_serie(embalse_id)
        return serie[-1] if serie else None

    def obtener_medicion_en_fecha(
        self, embalse_id: str, fecha: date
    ) -> Optional[MedicionHidrologica]:
        return self._mediciones.get((embalse_id, fecha))

    def obtener_ultima_fecha(self) -> Optional[date]:
        return max((m.fecha for m in self._mediciones.values()), default=None)

    def guardar_lote(self, mediciones: list[MedicionHidrologica]) -> None:
        for m in mediciones:
            self._mediciones[(m.embalse_id, m.fecha)] = m


class MetadatosRepositoryEnMemoria(MetadatosRepository):
    def __init__(self) -> None:
        self.guardado: Optional[MetadatosDatos] = None

    def obtener(self) -> Optional[MetadatosDatos]:
        return self.guardado

    def guardar(self, metadatos: MetadatosDatos) -> None:
        self.guardado = metadatos


class ProyeccionSendaRepositoryEnMemoria(ProyeccionSendaRepository):
    def __init__(self, proyecciones: Optional[list[ProyeccionSendaMensual]] = None) -> None:
        self._proyecciones = list(proyecciones or [])

    def obtener(self, embalse_id: str) -> list[ProyeccionSendaMensual]:
        return sorted(
            (p for p in self._proyecciones if p.embalse_id == embalse_id), key=lambda p: p.mes
        )

    def reemplazar_todas(self, proyecciones: list[ProyeccionSendaMensual]) -> None:
        self._proyecciones = list(proyecciones)


def crear_proyeccion_publicada(
    embalse_id: str, meses: int = 12, inicio: date = date(2024, 9, 1), base: float = 60.0,
    origen: str = "Modelo de prueba",
) -> list[ProyeccionSendaMensual]:
    """Proyeccion descendente de `meses` meses: el minimo cae en el ultimo mes."""
    puntos = []
    for i in range(meses):
        mes = date(inicio.year + (inicio.month - 1 + i) // 12, (inicio.month - 1 + i) % 12 + 1, 1)
        central = base - 2.0 * i
        puntos.append(ProyeccionSendaMensual(embalse_id, mes, central - 3.0, central, central + 3.0, origen))
    return puntos


class ForecastingPersistencia(ForecastingPort):
    """Pronostico determinista para pruebas: repite el ultimo valor observado
    y registra cada llamada para poder inspeccionar los datos de entrenamiento."""

    def __init__(self) -> None:
        self.llamadas: list[dict] = []

    def nombre_metodo(self) -> str:
        return "Persistencia de prueba"

    def proyectar(
        self,
        serie_historica: list[float],
        fechas_historicas: list[date],
        horizonte_periodos: int,
        nivel_confianza: float = 0.95,
        paso_dias: int = 1,
    ) -> list[PuntoForecast]:
        self.llamadas.append(
            {
                "serie": list(serie_historica),
                "fechas": list(fechas_historicas),
                "horizonte": horizonte_periodos,
                "paso_dias": paso_dias,
            }
        )
        ultimo = serie_historica[-1]
        ultima_fecha = fechas_historicas[-1]
        return [
            PuntoForecast(
                fecha=ultima_fecha + timedelta(days=paso_dias * (i + 1)),
                valor_esperado=ultimo,
                limite_inferior=ultimo - 1,
                limite_superior=ultimo + 1,
            )
            for i in range(horizonte_periodos)
        ]
