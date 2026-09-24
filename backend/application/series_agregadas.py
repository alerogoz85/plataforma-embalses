"""Series agregadas (nacional o por region) para los tableros que muestran
"Todos los embalses": el %V. util se pondera por la capacidad util en energia,
igual que el KPI nacional y la metrica oficial de XM."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from application.dtos.embalse_dto import EmbalseResumenDTO, SeriePuntoDTO
from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.entities.region import NombreRegion
from domain.exceptions import SinMedicionesError
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.services.calculo_hidrico_service import CalculoHidricoService
from domain.value_objects.porcentaje import Porcentaje

ID_TOTAL_NACIONAL = "TOTAL"
PREFIJO_REGION = "REGION:"
REGION_NACIONAL = "Nacional"
DIAS_VENTANA_DELTAS = 7


@dataclass(frozen=True, slots=True)
class GrupoAgregado:
    id: str
    nombre: str
    region: str
    embalses: list[Embalse]


@dataclass(frozen=True, slots=True)
class PuntoAgregado:
    fecha: date
    pct_volumen_util: float
    volumen_util_mm3: float
    capacidad_util_mm3: float
    energia_util_gwh: Optional[float]
    aportes_m3s: Optional[float]
    aportes_pct_media: Optional[float]
    vertimientos_m3s: Optional[float]
    turbinado_m3s: Optional[float]


def _suma(valores: list[Optional[float]]) -> Optional[float]:
    presentes = [v for v in valores if v is not None]
    return sum(presentes) if presentes else None


class SeriesAgregadas:
    """Resuelve ids agregados ('TOTAL' o 'REGION:<nombre>') y construye su serie diaria."""

    def __init__(
        self, embalse_repository: EmbalseRepository, medicion_repository: MedicionRepository
    ) -> None:
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository
        self._calculo = CalculoHidricoService()

    def resolver(self, embalse_id: str) -> Optional[GrupoAgregado]:
        if embalse_id == ID_TOTAL_NACIONAL:
            return GrupoAgregado(
                ID_TOTAL_NACIONAL, "Total nacional", REGION_NACIONAL, self._embalses_repo.listar()
            )
        if embalse_id.startswith(PREFIJO_REGION):
            pedida = embalse_id[len(PREFIJO_REGION):].strip().lower()
            for region in NombreRegion:
                if region.value.lower() == pedida:
                    embalses = [e for e in self._embalses_repo.listar() if str(e.region) == region.value]
                    return GrupoAgregado(
                        f"{PREFIJO_REGION}{region.value}", f"Región {region.value}", region.value, embalses
                    )
        return None

    def serie(
        self,
        grupo: GrupoAgregado,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> list[PuntoAgregado]:
        por_fecha: dict[date, list[MedicionHidrologica]] = defaultdict(list)
        for embalse in grupo.embalses:
            for medicion in self._mediciones_repo.obtener_serie(embalse.id, fecha_inicio, fecha_fin):
                por_fecha[medicion.fecha].append(medicion)
        return [self._agregar(fecha, por_fecha[fecha]) for fecha in sorted(por_fecha)]

    def serie_pct_diaria(self, grupo: GrupoAgregado) -> list[tuple[date, float]]:
        return [(p.fecha, round(p.pct_volumen_util, 2)) for p in self.serie(grupo)]

    def _agregar(self, fecha: date, mediciones: list[MedicionHidrologica]) -> PuntoAgregado:
        pesos = [self._calculo.calcular_peso_energetico_agregacion(m) for m in mediciones]
        peso_total = sum(pesos) or 1.0
        pct = sum(
            self._calculo.calcular_porcentaje_volumen_util(m).valor * p
            for m, p in zip(mediciones, pesos)
        ) / peso_total

        con_media = [m for m in mediciones if m.aportes is not None and m.aportes_media_historica_m3s]
        media = sum(m.aportes_media_historica_m3s for m in con_media)
        aportes = sum(m.aportes.valor_m3s for m in con_media)
        return PuntoAgregado(
            fecha=fecha,
            pct_volumen_util=pct,
            volumen_util_mm3=sum(m.volumen_util.valor_mm3 for m in mediciones),
            capacidad_util_mm3=sum(m.capacidad_util.valor_mm3 for m in mediciones),
            energia_util_gwh=_suma([m.energia_util_gwh for m in mediciones]),
            aportes_m3s=_suma([m.aportes.valor_m3s if m.aportes else None for m in mediciones]),
            aportes_pct_media=round(aportes / media * 100, 2) if media > 0 else None,
            vertimientos_m3s=_suma([m.vertimientos.valor_m3s if m.vertimientos else None for m in mediciones]),
            turbinado_m3s=_suma([m.turbinado.valor_m3s if m.turbinado else None for m in mediciones]),
        )

    def a_serie_dto(self, puntos: list[PuntoAgregado]) -> list[SeriePuntoDTO]:
        return [
            SeriePuntoDTO(
                fecha=p.fecha,
                pct_volumen_util=round(p.pct_volumen_util, 2),
                energia_util_gwh=p.energia_util_gwh,
                aportes_m3s=p.aportes_m3s,
                aportes_pct_media=p.aportes_pct_media,
                vertimientos_m3s=p.vertimientos_m3s,
                turbinado_m3s=p.turbinado_m3s,
            )
            for p in puntos
        ]

    def a_resumen_dto(self, grupo: GrupoAgregado, ventana: list[PuntoAgregado]) -> EmbalseResumenDTO:
        """Resumen del ultimo dia de `ventana` (debe incluir los 7 dias previos para los deltas)."""
        if not ventana:
            raise SinMedicionesError(grupo.id)
        actual = ventana[-1]
        por_fecha = {p.fecha: p for p in ventana}

        def delta(dias: int) -> float:
            anterior = por_fecha.get(actual.fecha - timedelta(days=dias))
            return round(actual.pct_volumen_util - anterior.pct_volumen_util, 2) if anterior else 0.0

        return EmbalseResumenDTO(
            id=grupo.id,
            nombre=grupo.nombre,
            region=grupo.region,
            es_agregado=True,
            fecha=actual.fecha,
            pct_volumen_util=round(actual.pct_volumen_util, 2),
            nivel_riesgo=Porcentaje(actual.pct_volumen_util).nivel_riesgo.value,
            volumen_util_mm3=actual.volumen_util_mm3,
            capacidad_util_mm3=actual.capacidad_util_mm3,
            energia_util_gwh=actual.energia_util_gwh,
            aportes_m3s=actual.aportes_m3s,
            aportes_pct_media=actual.aportes_pct_media,
            vertimientos_m3s=actual.vertimientos_m3s,
            turbinado_m3s=actual.turbinado_m3s,
            dias_autonomia=None,
            delta_diario_pct=delta(1),
            delta_semanal_pct=delta(DIAS_VENTANA_DELTAS),
        )
