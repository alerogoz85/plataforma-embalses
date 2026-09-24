from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from application.dtos.prediccion_dto import PrediccionDTO, PrediccionPuntoDTO
from application.ports.input.use_case_ports import GenerarPrediccionPort
from application.ports.output.forecasting_port import ForecastingPort
from application.series_agregadas import SeriesAgregadas
from domain.exceptions import DatosHistoricosInsuficientesError, EmbalseNoEncontradoError
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.repositories.proyeccion_senda_repository import ProyeccionSendaRepository
from domain.services.calculo_hidrico_service import CalculoHidricoService
from domain.services.proyeccion_diaria_service import AnclaMensual, ProyeccionDiariaService

MINIMO_REGISTROS_HISTORICOS = 30
NIVEL_CONFIANZA = 0.95
ORIGEN_OUTPUTS = "outputs"
ORIGEN_HOLT_WINTERS = "holt_winters"


class GenerarPrediccionUseCase(GenerarPrediccionPort):
    """Proyecta el %V_util futuro de un embalse.

    Si el modelo de largo plazo (Outputs) publico una proyeccion para el embalse, el
    pronostico diario es esa proyeccion interpolada a diario: asi coincide con la senda
    mensual y respeta los escenarios climaticos (ENSO). Sin ella se delega en un
    ForecastingPort estadistico (Holt-Winters) que solo ve la serie historica."""

    def __init__(
        self,
        embalse_repository: EmbalseRepository,
        medicion_repository: MedicionRepository,
        forecasting_service: ForecastingPort,
        proyeccion_repository: Optional[ProyeccionSendaRepository] = None,
    ) -> None:
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository
        self._forecasting = forecasting_service
        self._proyecciones = proyeccion_repository
        self._calculo = CalculoHidricoService()
        self._agregadas = SeriesAgregadas(embalse_repository, medicion_repository)

    def ejecutar(self, embalse_id: str, horizonte_dias: int) -> PrediccionDTO:
        grupo = self._agregadas.resolver(embalse_id)
        if grupo is not None:
            serie_pct = self._agregadas.serie_pct_diaria(grupo)
            if len(serie_pct) < MINIMO_REGISTROS_HISTORICOS:
                raise DatosHistoricosInsuficientesError(
                    embalse_id, MINIMO_REGISTROS_HISTORICOS, len(serie_pct)
                )
            fechas = [f for f, _ in serie_pct]
            valores_pct = [v for _, v in serie_pct]
        else:
            embalse = self._embalses_repo.obtener_por_id(embalse_id)
            if embalse is None:
                raise EmbalseNoEncontradoError(embalse_id)

            serie = self._mediciones_repo.obtener_serie(embalse_id)
            if len(serie) < MINIMO_REGISTROS_HISTORICOS:
                raise DatosHistoricosInsuficientesError(
                    embalse_id, MINIMO_REGISTROS_HISTORICOS, len(serie)
                )
            valores_pct = [
                self._calculo.calcular_porcentaje_volumen_util(m).valor for m in serie
            ]
            fechas = [m.fecha for m in serie]

        publicada = self._proyecciones.obtener(embalse_id) if self._proyecciones else []
        puntos_outputs = ProyeccionDiariaService.interpolar(
            ultima_fecha=fechas[-1],
            ultimo_valor=valores_pct[-1],
            anclas=[
                AnclaMensual.de_mes(p.mes, p.limite_inferior, p.valor_esperado, p.limite_superior)
                for p in publicada
            ],
            horizonte_dias=horizonte_dias,
        )
        if puntos_outputs:
            return self._dto(
                embalse_id, horizonte_dias, puntos_outputs,
                metodo=f"{publicada[0].origen} · interpolación diaria",
                nivel_confianza=None, origen=ORIGEN_OUTPUTS,
            )

        puntos_forecast = self._forecasting.proyectar(
            serie_historica=valores_pct,
            fechas_historicas=fechas,
            horizonte_periodos=horizonte_dias,
            nivel_confianza=NIVEL_CONFIANZA,
        )
        return self._dto(
            embalse_id, horizonte_dias, puntos_forecast,
            metodo=self._forecasting.nombre_metodo(),
            nivel_confianza=NIVEL_CONFIANZA, origen=ORIGEN_HOLT_WINTERS,
        )

    @staticmethod
    def _dto(embalse_id, horizonte_dias, puntos, metodo, nivel_confianza, origen) -> PrediccionDTO:
        return PrediccionDTO(
            embalse_id=embalse_id,
            horizonte_dias=horizonte_dias,
            nivel_confianza=nivel_confianza,
            generado_en=datetime.now(timezone.utc),
            metodo=metodo,
            origen=origen,
            puntos=[
                PrediccionPuntoDTO(
                    fecha=p.fecha,
                    valor_esperado=round(p.valor_esperado, 2),
                    limite_inferior=round(p.limite_inferior, 2),
                    limite_superior=round(p.limite_superior, 2),
                )
                for p in puntos
            ],
        )
