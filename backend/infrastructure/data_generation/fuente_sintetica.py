from __future__ import annotations

from datetime import date

from application.ports.output.fuente_mediciones_port import DescargaMediciones, FuenteMedicionesPort
from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.entities.region import NombreRegion, Region
from domain.value_objects.caudal import Caudal
from domain.value_objects.volumen import Volumen
from infrastructure.data_generation.generador_series_hidrologicas import GeneradorSeriesHidrologicas

# Factor de energia por m3 usado solo para poblar los campos de energia de la
# fuente sintetica; en datos reales la energia la publica XM.
FACTOR_ENERGIA_GWH_POR_MM3 = 0.6


class FuenteSintetica(FuenteMedicionesPort):
    """Fuente alternativa para demostraciones sin red: series simuladas,
    hidrologicamente coherentes pero que NO representan mediciones reales."""

    def __init__(self, semilla: int = 42) -> None:
        self._generador = GeneradorSeriesHidrologicas(semilla=semilla)

    def descargar(self, desde: date, hasta: date) -> DescargaMediciones:
        embalses: list[Embalse] = []
        mediciones: list[MedicionHidrologica] = []

        for definicion in self._generador.catalogo():
            embalses.append(
                Embalse(
                    id=definicion.id,
                    nombre=definicion.nombre,
                    region=Region(NombreRegion(definicion.region)),
                )
            )
            capacidad_mm3 = definicion.volumen_maximo_mm3 - definicion.volumen_muerto_mm3
            for registro in self._generador.generar_serie(definicion, desde, hasta):
                mediciones.append(
                    MedicionHidrologica(
                        embalse_id=registro.embalse_id,
                        fecha=registro.fecha,
                        volumen_util=Volumen(registro.volumen_util_mm3),
                        capacidad_util=Volumen(capacidad_mm3),
                        capacidad_util_energia_gwh=capacidad_mm3 * FACTOR_ENERGIA_GWH_POR_MM3,
                        energia_util_gwh=registro.volumen_util_mm3 * FACTOR_ENERGIA_GWH_POR_MM3,
                        aportes=Caudal(registro.aportes_m3s),
                        aportes_media_historica_m3s=registro.aportes_media_historica_m3s,
                        vertimientos=Caudal(registro.vertimientos_m3s),
                        turbinado=Caudal(registro.turbinado_m3s),
                    )
                )

        return DescargaMediciones(
            embalses=embalses,
            mediciones=mediciones,
            fuente="Datos sintéticos (simulación)",
            descripcion=(
                "Series simuladas con estacionalidad y balance de masa; "
                "no son mediciones reales."
            ),
            es_real=False,
        )
