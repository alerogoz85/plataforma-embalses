from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from application.ports.output.forecasting_port import ForecastingPort, PuntoForecast
from domain.entities.embalse import Embalse
from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.entities.metadatos_datos import MetadatosDatos
from domain.entities.modelo_carbon import (
    ComparacionXM, CriterioValidez, EpisodioValidacion, ErrorPorHorizonte, HistoricoCarbonMensual,
    InventarioCarbon, PaqueteModeloCarbon, ProyeccionCarbonMensual, SupuestoCarbon, TrimestreCarbon,
)
from domain.entities.modelo_analitico import (
    DimensionFiltro, GraficoResultado, Indicador, LineaGrafico, PuntoSerie, ResultadoModelo, SerieResultado, TablaResultado,
)
from domain.entities.modelo_dns import (
    CambioReporte, EventoDns, ImportanciaVariable, MetricaModelo, PaqueteModeloDns, PronosticoSubarea, SubareaDns,
    ZonaPriorizada,
)
from domain.entities.proyeccion_senda import ProyeccionSendaMensual
from domain.entities.region import NombreRegion, Region
from domain.repositories.embalse_repository import EmbalseRepository
from domain.repositories.medicion_repository import MedicionRepository
from domain.repositories.metadatos_repository import MetadatosRepository
from domain.repositories.modelo_carbon_repository import ModeloCarbonRepository
from domain.repositories.modelo_analitico_repository import ResultadoModeloRepository
from domain.repositories.modelo_dns_repository import ModeloDnsRepository
from domain.value_objects.banda import Banda
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


# --- Modelo de carbon termico --------------------------------------------------
class ModeloCarbonRepositoryEnMemoria(ModeloCarbonRepository):
    def __init__(self, paquete: Optional[PaqueteModeloCarbon] = None) -> None:
        self.paquete = paquete

    def obtener(self) -> Optional[PaqueteModeloCarbon]:
        return self.paquete

    def reemplazar(self, paquete: PaqueteModeloCarbon) -> None:
        self.paquete = paquete


P50_CARBON = [298.0, 295.0, 370.0, 380.0, 389.0, 377.0, 356.0, 351.0, 313.0]  # oct-2026 a jun-2027
TECHO_CARBON = 400.0
PODER_CALORIFICO = 26.27


def _mes(anio: int, mes: int) -> date:
    return date(anio + (mes - 1) // 12, (mes - 1) % 12 + 1, 1)


def crear_paquete_carbon() -> PaqueteModeloCarbon:
    """Una corrida del modelo pequena pero completa: 24 meses de historia (el ultimo
    parcial), 9 de proyeccion con pico en febrero de 2027 y los extras de validacion."""
    historico = [
        HistoricoCarbonMensual(
            _mes(2024, 11 + i), 200.0 + 5 * i, TECHO_CARBON, 50.0 + i, 60.0 + i, 1.0 if i % 2 else None,
            "Sinergox" if i < 20 else "Estimado", i < 23, 30 if i < 23 else 15,
        )
        for i in range(24)
    ]
    # el record mensual es el mes 22 (ago-2026): 310 GBTU/dia
    historico[22] = HistoricoCarbonMensual(_mes(2026, 9), 310.0, TECHO_CARBON, 77.5, 55.0, 1.5, "Estimado", True, 30)
    proyeccion = [
        ProyeccionCarbonMensual(
            fecha=_mes(2026, 10 + i), dias=30, techo_gbtu_dia=TECHO_CARBON,
            roni=Banda(2.0, 2.4, 2.8), aportes_pct_media=Banda(30.0 + i, 50.0 + i, 70.0 + i),
            uso_techo_pct=Banda(p50 - 60, p50, p50 + 30), carbon_gbtu_dia=Banda(p50 - 60, p50, p50 + 30),
            carbon_kt_mes=Banda((p50 - 60) * 1.14, p50 * 1.14, (p50 + 30) * 1.14),
            prob_supera_maximo_pct=min(95.0, p50 / 4), observado_parcial_gbtu_dia=213.0 if i == 0 else None,
        )
        for i, p50 in enumerate(P50_CARBON)
    ]
    # los porcentajes de uso del ejemplo se escalan al techo para que sean verosimiles
    proyeccion = [
        ProyeccionCarbonMensual(
            m.fecha, m.dias, m.techo_gbtu_dia, m.roni, m.aportes_pct_media,
            Banda(*(round(v / TECHO_CARBON * 100, 2) for v in (m.uso_techo_pct.p10, m.uso_techo_pct.p50, m.uso_techo_pct.p90))),
            m.carbon_gbtu_dia, m.carbon_kt_mes, m.prob_supera_maximo_pct, m.observado_parcial_gbtu_dia,
        )
        for m in proyeccion
    ]
    return PaqueteModeloCarbon(
        origen="Modelo de prueba", poder_calorifico_mbtu_t=PODER_CALORIFICO,
        historico=historico, proyeccion=proyeccion,
        trimestres=[
            TrimestreCarbon("2026Q4", 3, Banda(0.8, 1.1, 1.3)),
            TrimestreCarbon("2027Q1", 3, Banda(1.1, 1.3, 1.4)),
            TrimestreCarbon("2027Q2", 3, Banda(0.8, 1.2, 1.3)),
        ],
        inventario=[
            InventarioCarbon(m.fecha, dias, round(m.carbon_gbtu_dia.p50 * dias * 0.038, 3), round(m.carbon_gbtu_dia.p90 * dias * 0.038, 3))
            for m in proyeccion for dias in (15, 30, 45, 60)
        ],
        comparacion_xm=[
            ComparacionXM(m.fecha, m.carbon_gbtu_dia, TECHO_CARBON, 465.0, 231.0, 233.0) for m in proyeccion
        ],
        errores_horizonte=[
            ErrorPorHorizonte(h, 60, 45.0 + h, 50.0 + 5 * h, 110.0, 88.0, -4.0) for h in (1, 3, 6, 9)
        ],
        episodios=[
            EpisodioValidacion("El Nino 2023-2024", date(2023, 7, 1), date(2024, 2, 1), 8, 271.0, 258.0, -4.7, 58.0, 95.0, 87.5),
            EpisodioValidacion("El Nino 2018-2019", date(2018, 10, 1), date(2019, 4, 1), 7, 188.0, 261.0, 39.0, 73.0, 115.0, 85.7),
        ],
        veredicto=[
            CriterioValidez("Coeficientes significativos", "p=0.000", True, "Relaciones no casuales"),
            CriterioValidez("RESET de Ramsey", "p=0.59", True, "Forma funcional adecuada"),
            CriterioValidez("CUSUM", "p=0.96", True, "Coeficientes estables"),
            CriterioValidez("Breusch-Pagan", "p=0.001", False, "Varianza cambiante"),
        ],
        supuestos=[
            SupuestoCarbon("Poder calorífico [MBTU/t]", "26.27"), SupuestoCarbon("Simulaciones", "20000"),
            SupuestoCarbon("Factor de ampliación de residuos (calibrado)", "1.5"),
        ],
    )


# ------------------------------------------------------------------ modelo DNS
class ModeloDnsRepositoryEnMemoria(ModeloDnsRepository):
    def __init__(self, paquete: Optional[PaqueteModeloDns] = None) -> None:
        self.paquete = paquete

    def obtener(self) -> Optional[PaqueteModeloDns]:
        return self.paquete

    def reemplazar(self, paquete: PaqueteModeloDns) -> None:
        self.paquete = paquete


def _ev(fecha: str, subarea: str, kwh: float, origen: Optional[str], causa: str = "mantenimiento",
        origen_causa: str = "reportada", tipo: str = "DNS", tipo_evento: str = "Trabajos de mantenimiento (consignación)",
        nivel: str = "Transmisión regional / distribución (STR, <220 kV)") -> EventoDns:
    return EventoDns(datetime.fromisoformat(fecha), subarea, tipo, kwh, origen, causa, origen_causa, tipo_evento, nivel)


def crear_paquete_dns() -> PaqueteModeloDns:
    """Corrida pequena con numeros faciles de comprobar a mano. El corte es 2026-08-11 12:00 (mes parcial).

    Ventana de 12 meses = 2025-09..2026-08 (5 eventos DNS, 420.000 kWh); la anterior = 2024-09..2025-08
    (2 eventos, 50.000 kWh). Are0001/Are0002 son de la region Norte, Are0003 del Sur y Are0004 (sin
    asignar) solo tiene EDAC."""
    eventos = [
        _ev("2026-08-02 10:30", "Are0001", 50_000, "no_programada", "fallas", "reportada", tipo_evento="Disparo de activo/protección"),
        _ev("2026-08-05 00:00", "Are0001", 120_000, "programada"),  # hora desconocida (00:00:00 exacto) y critico
        _ev("2026-08-11 12:00", "Are0003", 30_000, "no_programada", "desconocido", "sin clasificar", tipo_evento="Otro / no clasificado"),
        _ev("2026-07-10 07:15", "Are0001", 20_000, "no_programada", "atmosferica", "inferida (regex)", tipo_evento="Disparo de activo/protección",
            nivel="Transmisión nacional (STN, ≥220 kV)"),
        _ev("2026-07-20 19:00", "Are0002", 200_000, "programada"),  # critico
        _ev("2025-08-15 09:00", "Are0001", 10_000, "no_programada", "fallas", "inferida (TF-IDF)"),
        _ev("2025-03-03 22:00", "Are0002", 40_000, "no_programada", "desconocido", "sin clasificar"),
        _ev("2013-01-02 06:00", "Are0003", 5_000, "programada"),
        _ev("2026-07-30 03:00", "Are0004", 150.0, None, "desconocido", "sin clasificar", tipo="EDAC"),
        _ev("2020-01-01 05:00", "Are0001", 90.0, None, "desconocido", "sin clasificar", tipo="EDAC"),
    ]
    return PaqueteModeloDns(
        origen="Modelo DNS de prueba", periodo_pronostico="2026-08",
        subareas=[
            SubareaDns("Are0001", "SubArea Uno", "Norte", "Antioquia"),
            SubareaDns("Are0002", "SubArea Dos", "Norte"),
            SubareaDns("Are0003", "SubArea Tres", "Sur"),
            SubareaDns("Are0004", "Are0004", "Sin asignar"),
        ],
        eventos=eventos,
        zonas=[
            ZonaPriorizada(1, "Are0001", 80.0, 5.0e7, 400, 0.2, 10.0),
            ZonaPriorizada(2, "Are0002", 60.0, 2.0e7, 200, 0.1, -5.0),
            ZonaPriorizada(3, "Are0003", 30.0, 1.0e7, 100, 0.0, 0.0),
        ],
        cambios_reporte=[CambioReporte("Are0002", "2025-01", "SUBIDA", 0.0, 80.0, 50.0, 5.0)],
        metricas=[
            MetricaModelo("n_eventos - persistencia", 6.0, 12.0),
            MetricaModelo("n_eventos - GradientBoosting", 4.5, 10.0),
            MetricaModelo("energia_kwh - persistencia", 200_000.0, 400_000.0),
            MetricaModelo("energia_kwh - RandomForest (log)", 150_000.0, 300_000.0),
        ],
        importancia=[ImportanciaVariable(f"variable_{i:02d}", 1.0 - i * 0.05, i * 0.01) for i in range(12)],
        pronostico=[
            PronosticoSubarea("Are0001", 10.0, 500_000.0),
            PronosticoSubarea("Are0002", 5.0, 250_000.0),
            PronosticoSubarea("Are0003", 2.0, 100_000.0),
        ],
    )


# ------------------------------------------------------------------ modelos analiticos (gas, optimizacion, apagon)
class ResultadoModeloRepositoryEnMemoria(ResultadoModeloRepository):
    def __init__(self, *resultados: ResultadoModelo) -> None:
        self.resultados = {r.modelo_id: r for r in resultados}

    def obtener(self, modelo_id: str) -> Optional[ResultadoModelo]:
        return self.resultados.get(modelo_id)

    def reemplazar(self, resultado: ResultadoModelo) -> None:
        self.resultados[resultado.modelo_id] = resultado


def crear_resultado_modelo(modelo_id: str = "apagon") -> ResultadoModelo:
    """Resultado pequeno pero completo: un indicador con nivel, dos series (una con banda), un grafico con dos lineas filtrado por
    una dimension, dos tablas (una filtrable por esa dimension) y una advertencia."""
    return ResultadoModelo(
        modelo_id=modelo_id, generado_en=datetime(2026, 10, 1, 12, 30), origen="Corrida de prueba",
        configuracion=(("Simulaciones", "3000"),),
        indicadores=(Indicador("Meses en rojo", "2", "de 3 meses", "critico"),),
        series=(
            SerieResultado("indice", "Índice de riesgo", "puntos", "linea",
                           (PuntoSerie("2026-10", 20.0), PuntoSerie("2026-11", 45.5), PuntoSerie("2026-12", 80.0))),
            SerieResultado("embalse", "Embalse", "%", "linea",
                           (PuntoSerie("2026-10", 60.0, 50.0, 70.0), PuntoSerie("2026-11", 55.0, 40.0, 65.0))),
        ),
        tablas=(
            TablaResultado("semaforo", "Semáforo", ("Mes", "Semáforo", "Índice"),
                           (("2026-10", "Verde", 20.0), ("2026-11", "Amarillo", None)), "Nota de prueba"),
            TablaResultado("por_campo", "Por campo", ("Campo", "Valor"), (("NACIONAL", 1.0), ("CAMPO A", 2.0)), None, (("serie", "Campo"),)),
        ),
        advertencias=("Solo adecuación de generación nacional.",),
        dimensiones=(DimensionFiltro("serie", "Campo", ("NACIONAL", "CAMPO A"), "NACIONAL"),),
        graficos=(
            GraficoResultado(
                "g_nacional", "NACIONAL: observado y pronóstico", "MPCD",
                (LineaGrafico("Observado", (PuntoSerie("2026-06", 10.0), PuntoSerie("2026-07", 11.0))),
                 LineaGrafico("Pronóstico", (PuntoSerie("2026-08", 12.0, 10.0, 14.0),), "punteada")),
                (("serie", "NACIONAL"),),
            ),
        ),
    )
