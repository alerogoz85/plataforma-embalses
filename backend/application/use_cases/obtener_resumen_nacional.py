from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from application.dtos.embalse_dto import (
    EmbalseResumenDTO,
    KPINacionalDTO,
    RegionResumenDTO,
    ResumenNacionalDTO,
)
from application.mappers import a_resumen_dto
from application.ports.input.use_case_ports import ObtenerResumenNacionalPort
from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.entities.region import NombreRegion
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.services.calculo_hidrico_service import CalculoHidricoService
from domain.value_objects.porcentaje import Porcentaje


@dataclass(frozen=True, slots=True)
class _EmbalseSnapshot:
    embalse: Embalse
    medicion: MedicionHidrologica
    resumen: EmbalseResumenDTO


class ObtenerResumenNacionalUseCase(ObtenerResumenNacionalPort):
    """Construye el panorama nacional: KPIs agregados, corte por region y
    listado de embalses, aplicando los filtros opcionales recibidos."""

    def __init__(
        self,
        embalse_repository: EmbalseRepository,
        medicion_repository: MedicionRepository,
    ) -> None:
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository
        self._calculo = CalculoHidricoService()

    def ejecutar(
        self,
        regiones: Optional[list[str]] = None,
        embalses: Optional[list[str]] = None,
        fecha: Optional[date] = None,
    ) -> ResumenNacionalDTO:
        candidatos = self._embalses_repo.listar()

        if regiones:
            regiones_set = {r.lower() for r in regiones}
            candidatos = [e for e in candidatos if str(e.region).lower() in regiones_set]
        if embalses:
            embalses_set = set(embalses)
            candidatos = [e for e in candidatos if e.id in embalses_set]

        snapshots = self._construir_snapshots(candidatos, fecha)
        return ResumenNacionalDTO(
            kpis=self._construir_kpis(snapshots),
            regiones=self._construir_regiones(snapshots),
            embalses=[s.resumen for s in snapshots],
        )

    def _construir_snapshots(
        self, embalses: list[Embalse], fecha: Optional[date]
    ) -> list[_EmbalseSnapshot]:
        snapshots = []
        for embalse in embalses:
            medicion = (
                self._mediciones_repo.obtener_medicion_en_fecha(embalse.id, fecha)
                if fecha
                else self._mediciones_repo.obtener_ultima_medicion(embalse.id)
            )
            if medicion is None:
                continue

            medicion_ayer = self._mediciones_repo.obtener_medicion_en_fecha(
                embalse.id, medicion.fecha - timedelta(days=1)
            )
            medicion_semana = self._mediciones_repo.obtener_medicion_en_fecha(
                embalse.id, medicion.fecha - timedelta(days=7)
            )
            resumen = a_resumen_dto(embalse, medicion, medicion_ayer, medicion_semana)
            snapshots.append(_EmbalseSnapshot(embalse, medicion, resumen))
        return snapshots

    def _pesos(self, snapshots: list[_EmbalseSnapshot]) -> list[float]:
        return [self._calculo.calcular_peso_energetico_agregacion(s.medicion) for s in snapshots]

    @staticmethod
    def _aportes_pct_media(snapshots: list[_EmbalseSnapshot]) -> Optional[float]:
        """Aportes totales / media historica total, solo entre embalses que
        publican ambos datos; None si ninguno los publica."""
        aportes = 0.0
        media = 0.0
        for s in snapshots:
            if s.medicion.aportes is not None and s.medicion.aportes_media_historica_m3s:
                aportes += s.medicion.aportes.valor_m3s
                media += s.medicion.aportes_media_historica_m3s
        return round(aportes / media * 100, 2) if media > 0 else None

    def _construir_kpis(self, snapshots: list[_EmbalseSnapshot]) -> KPINacionalDTO:
        if not snapshots:
            return KPINacionalDTO(
                fecha_corte=date.today(),
                pct_volumen_util_nacional=0.0,
                delta_diario_pct=0.0,
                delta_semanal_pct=0.0,
                aportes_pct_media_nacional=None,
                capacidad_guardada_gwh=0.0,
                nivel_riesgo_sistema=Porcentaje(0.0).nivel_riesgo.value,
                total_embalses=0,
            )

        pesos = self._pesos(snapshots)
        peso_total = sum(pesos) or 1.0

        pct_nacional = (
            sum(s.resumen.pct_volumen_util * p for s, p in zip(snapshots, pesos)) / peso_total
        )
        delta_diario = (
            sum(s.resumen.delta_diario_pct * p for s, p in zip(snapshots, pesos)) / peso_total
        )
        delta_semanal = (
            sum(s.resumen.delta_semanal_pct * p for s, p in zip(snapshots, pesos)) / peso_total
        )
        capacidad_guardada = sum(
            self._calculo.calcular_capacidad_guardada_gwh(s.medicion) for s in snapshots
        )
        fecha_corte = max(s.resumen.fecha for s in snapshots)

        return KPINacionalDTO(
            fecha_corte=fecha_corte,
            pct_volumen_util_nacional=round(pct_nacional, 2),
            delta_diario_pct=round(delta_diario, 2),
            delta_semanal_pct=round(delta_semanal, 2),
            aportes_pct_media_nacional=self._aportes_pct_media(snapshots),
            capacidad_guardada_gwh=round(capacidad_guardada, 2),
            nivel_riesgo_sistema=Porcentaje(pct_nacional).nivel_riesgo.value,
            total_embalses=len(snapshots),
        )

    def _construir_regiones(self, snapshots: list[_EmbalseSnapshot]) -> list[RegionResumenDTO]:
        por_region: dict[str, list[_EmbalseSnapshot]] = {}
        for snapshot in snapshots:
            por_region.setdefault(str(snapshot.embalse.region), []).append(snapshot)

        salida = []
        for nombre_region in NombreRegion:
            items = por_region.get(nombre_region.value)
            if not items:
                continue
            pesos = self._pesos(items)
            peso_total = sum(pesos) or 1.0
            pct = sum(s.resumen.pct_volumen_util * p for s, p in zip(items, pesos)) / peso_total
            salida.append(
                RegionResumenDTO(
                    region=nombre_region.value,
                    pct_volumen_util=round(pct, 2),
                    aportes_pct_media=self._aportes_pct_media(items),
                    nivel_riesgo=Porcentaje(pct).nivel_riesgo.value,
                    num_embalses=len(items),
                    energia_util_gwh=round(sum(s.medicion.energia_util_gwh or 0.0 for s in items), 2),
                )
            )
        return salida
