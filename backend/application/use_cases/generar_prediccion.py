from __future__ import annotations

from datetime import datetime, timezone

from application.dtos.prediccion_dto import PrediccionDTO, PrediccionPuntoDTO
from application.ports.input.use_case_ports import GenerarPrediccionPort
from application.ports.output.forecasting_port import ForecastingPort
from domain.exceptions import DatosHistoricosInsuficientesError, EmbalseNoEncontradoError
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.services.calculo_hidrico_service import CalculoHidricoService

MINIMO_REGISTROS_HISTORICOS = 30
NIVEL_CONFIANZA = 0.95


class GenerarPrediccionUseCase(GenerarPrediccionPort):
    """Proyecta el %V_util futuro de un embalse delegando el pronostico
    estadistico en un ForecastingPort (Holt-Winters / Prophet / XGBoost)."""

    def __init__(
        self,
        embalse_repository: EmbalseRepository,
        medicion_repository: MedicionRepository,
        forecasting_service: ForecastingPort,
    ) -> None:
        self._embalses_repo = embalse_repository
        self._mediciones_repo = medicion_repository
        self._forecasting = forecasting_service
        self._calculo = CalculoHidricoService()

    def ejecutar(self, embalse_id: str, horizonte_dias: int) -> PrediccionDTO:
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

        puntos_forecast = self._forecasting.proyectar(
            serie_historica=valores_pct,
            fechas_historicas=fechas,
            horizonte_periodos=horizonte_dias,
            nivel_confianza=NIVEL_CONFIANZA,
        )

        return PrediccionDTO(
            embalse_id=embalse_id,
            horizonte_dias=horizonte_dias,
            nivel_confianza=NIVEL_CONFIANZA,
            generado_en=datetime.now(timezone.utc),
            metodo=self._forecasting.nombre_metodo(),
            puntos=[
                PrediccionPuntoDTO(
                    fecha=p.fecha,
                    valor_esperado=round(p.valor_esperado, 2),
                    limite_inferior=round(p.limite_inferior, 2),
                    limite_superior=round(p.limite_superior, 2),
                )
                for p in puntos_forecast
            ],
        )
