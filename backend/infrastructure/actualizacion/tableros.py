"""Catalogo de tableros que se actualizan con archivos y los adaptadores que los leen y guardan.

Cada tablero declara el paquete de archivos que pide (clave, formatos, obligatorio). Para leer, los archivos se escriben en una carpeta
temporal privada con la MISMA estructura que usan los importadores de linea de comandos y se invoca ese mismo lector: la validacion
de contenido es una sola (la del lector), no una copia. Nada se escribe en la base hasta `guardar`."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable

from domain.entities.actualizacion import ArchivoRequerido, TableroActualizable
from domain.repositories.modelo_analitico_repository import EscenarioApagonRepository, ResultadoModeloRepository
from domain.repositories.modelo_carbon_repository import ModeloCarbonRepository
from domain.repositories.modelo_dns_repository import ModeloDnsRepository
from infrastructure.ingesta import modelo_carbon_archivos as carbon_archivos
from infrastructure.ingesta import modelo_dns_archivos as dns_archivos
from infrastructure.ingesta.resultados_modelos import LECTORES
from infrastructure.ingesta.resultados_modelos.comun import SalidaModeloInvalidaError
from infrastructure.ingesta.resultados_modelos.escenarios_csv import leer_escenarios_csv

Resumen = tuple[tuple[str, str], ...]


class AdaptadorTablero(ABC):
    """Lee el paquete (lanza error con el motivo si no cumple), lo resume y lo guarda."""

    definicion: TableroActualizable
    errores_de_lectura: tuple[type[Exception], ...] = (ValueError,)

    @abstractmethod
    def leer(self, carpeta: Path) -> Any: ...

    @abstractmethod
    def resumir(self, objeto: Any) -> tuple[Resumen, tuple[str, ...]]:
        """(datos clave de la carga, advertencias)."""

    @abstractmethod
    def guardar(self, objeto: Any) -> None: ...


def _archivo(clave: str, etiqueta: str, ruta: str, formatos: tuple[str, ...], obligatorio: bool = True, descripcion: str = "", patron: str | None = None) -> ArchivoRequerido:
    return ArchivoRequerido(clave=clave, etiqueta=etiqueta, ruta=ruta, formatos=formatos, obligatorio=obligatorio, descripcion=descripcion, patron_nombre=patron)


def _n(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


# ---------------------------------------------------------------------------------------------------- carbon
class AdaptadorCarbon(AdaptadorTablero):
    definicion = TableroActualizable(
        id="carbon", titulo="Carbón térmico", descripcion="Proyección del consumo de carbón con escenarios ENOS, su validación y la comparación con XM.",
        archivos=(
            _archivo("proyeccion", "Proyección de carbón (Excel)", "resultados/proyeccion_carbon.xlsx", ("xlsx",), descripcion="Hojas proyeccion_mensual, trimestres, inventario, comparacion_xm, validacion y supuestos."),
            _archivo("evaluacion", "Evaluación del modelo (Excel)", "resultados/evaluacion/evaluacion_modelo.xlsx", ("xlsx",), descripcion="Hojas veredicto y error_por_horizonte."),
            _archivo("base", "Base mensual nacional (Parquet)", "datos/base/base_mensual_nacional.parquet", ("parquet",), descripcion="Histórico mensual del consumo de carbón."),
        ),
    )
    errores_de_lectura = (carbon_archivos.ArchivoModeloCarbonInvalidoError, ValueError)

    def __init__(self, repo: ModeloCarbonRepository) -> None:
        self._repo = repo

    def leer(self, carpeta: Path) -> Any:
        return carbon_archivos.leer_modelo_carbon(carpeta)

    def resumir(self, p: Any) -> tuple[Resumen, tuple[str, ...]]:
        return (
            (("Meses históricos", _n(len(p.historico))), ("Meses proyectados", _n(len(p.proyeccion))), ("Trimestres", _n(len(p.trimestres))),
             ("Episodios de validación", _n(len(p.episodios))), ("Origen", p.origen[:120])), (),
        )

    def guardar(self, p: Any) -> None:
        self._repo.reemplazar(p)


# -------------------------------------------------------------------------------------------------------- dns
class AdaptadorDns(AdaptadorTablero):
    definicion = TableroActualizable(
        id="dns", titulo="Demanda no atendida (DNS)", descripcion="Eventos por subárea, priorización de zonas, causas, cambios de reporte y modelo predictivo.",
        archivos=(
            _archivo("mapeo", "Mapeo de subáreas (CSV)", "Datos/outputs_datos/mapeo_subareas.csv", ("csv",)),
            _archivo("eventos", "Eventos enriquecidos (CSV)", "Datos/outputs/03_causas/eventos_enriquecidos.csv", ("csv",)),
            _archivo("zonas", "Índice de priorización de zonas (CSV)", "Datos/outputs/04_zonas/indice_priorizacion_zonas.csv", ("csv",)),
            _archivo("cambios", "Cambios en la forma de reportar (CSV)", "Datos/outputs/05_cambios_reporte/cambios_reporte_confirmados.csv", ("csv",)),
            _archivo("metricas", "Métricas del modelo (CSV)", "Datos/outputs/07_modelo/metricas_evaluacion.csv", ("csv",)),
            _archivo("importancia", "Importancia de variables (CSV)", "Datos/outputs/07_modelo/importancia_variables.csv", ("csv",)),
            _archivo("pronostico", "Pronóstico por subárea (CSV)", "Datos/outputs/07_modelo", ("csv",), descripcion="Debe llamarse pronostico_AAAA-MM.csv", patron=r"pronostico_\d{4}-(0[1-9]|1[0-2])\.csv"),
        ),
    )
    errores_de_lectura = (dns_archivos.ArchivoModeloDnsInvalidoError, ValueError)

    def __init__(self, repo: ModeloDnsRepository) -> None:
        self._repo = repo

    def leer(self, carpeta: Path) -> Any:
        return dns_archivos.leer_modelo_dns(carpeta)

    def resumir(self, p: Any) -> tuple[Resumen, tuple[str, ...]]:
        return (
            (("Eventos", _n(len(p.eventos))), ("Primer evento", f"{p.fecha_inicio:%Y-%m-%d}"), ("Último evento", f"{p.fecha_corte:%Y-%m-%d}"),
             ("Subáreas", _n(len(p.subareas))), ("Zonas priorizadas", _n(len(p.zonas))), ("Pronóstico", f"{p.periodo_pronostico} · {_n(len(p.pronostico))} subáreas")), (),
        )

    def guardar(self, p: Any) -> None:
        self._repo.reemplazar(p)


# ------------------------------------------------------------------------------- modelos con resultados genericos
class AdaptadorResultadoModelo(AdaptadorTablero):
    errores_de_lectura = (SalidaModeloInvalidaError, ValueError)

    def __init__(self, modelo_id: str, definicion: TableroActualizable, repo: ResultadoModeloRepository) -> None:
        self._modelo_id = modelo_id
        self.definicion = definicion
        self._repo = repo

    def leer(self, carpeta: Path) -> Any:
        return LECTORES[self._modelo_id](carpeta)

    def resumir(self, r: Any) -> tuple[Resumen, tuple[str, ...]]:
        resumen = (("Origen", r.origen[:140]), ("Indicadores", _n(len(r.indicadores))), ("Series", _n(len(r.series))), ("Gráficos", _n(len(r.graficos))), ("Tablas", _n(len(r.tablas))))
        return resumen, tuple(r.advertencias[:5])

    def guardar(self, r: Any) -> None:
        self._repo.reemplazar(r)


def _definicion_gas() -> TableroActualizable:
    return TableroActualizable(
        id="gas", titulo="Gas natural", descripcion="Oferta declarada frente a gas fiscalizado: pronóstico por campo, curvas de Arps, backtesting y comparación.",
        archivos=(
            _archivo("v2", "Pronóstico v2 (Excel)", "Resultados/pronostico_v2/Pronostico_Gas_v2.xlsx", ("xlsx",), descripcion="Libro con las hojas Info, Resumen, Pronostico, Proporciones, Backtest y Arps."),
            _archivo("dca", "Curvas de declinación por cohorte (Excel)", "Resultados/pronostico_dca/Pronostico_DCA_Declaraciones.xlsx", ("xlsx",), obligatorio=False),
            _archivo("bt_global", "Backtesting global (CSV)", "Resultados/backtesting/backtest_resumen_global.csv", ("csv",), obligatorio=False),
            _archivo("bt_anio", "Backtesting por año de declaración (CSV)", "Resultados/backtesting/backtest_por_anio_declaracion.csv", ("csv",), obligatorio=False),
            _archivo("bt_skill", "Habilidad frente al ingenuo (CSV)", "Resultados/backtesting/backtest_skill_vs_naive_horizonte.csv", ("csv",), obligatorio=False),
            _archivo("comparacion", "Comparación por año (CSV)", "Resultados/comparacion/resumen_comparacion_por_anio.csv", ("csv",), obligatorio=False),
        ),
    )


def _definicion_optimizacion() -> TableroActualizable:
    return TableroActualizable(
        id="optimizacion", titulo="Optimización hidrotérmica", descripcion="Resumen de la corrida de planeación SDDP y su validación técnica.",
        archivos=(
            _archivo("resumen", "Resumen de la corrida (JSON)", "05_resultados/resumen.json", ("json",)),
            _archivo("validacion", "Validación técnica (JSON)", "05_resultados/validacion_tecnica.json", ("json",), obligatorio=False),
            _archivo("manifest", "Manifiesto de la corrida (JSON)", "05_resultados/manifest.json", ("json",), obligatorio=False),
        ),
    )


def _definicion_apagon() -> TableroActualizable:
    return TableroActualizable(
        id="apagon", titulo="Riesgo de apagón · resumen del modelo", descripcion="Resumen mensual de la corrida del modelo (semáforo, probabilidades, franjas). Es la vista de respaldo del tablero.",
        archivos=(
            _archivo("resumen", "Resumen mensual (CSV)", "resultados_modelo_riesgo_apagon/resumen_mensual.csv", ("csv",)),
            _archivo("franjas", "Detalle por franja horaria (CSV)", "resultados_modelo_riesgo_apagon/detalle_franjas_horarias.csv", ("csv",), obligatorio=False),
            _archivo("metadatos", "Metadatos de la corrida (JSON)", "resultados_modelo_riesgo_apagon/metadatos_corrida.json", ("json",), obligatorio=False),
            _archivo("configuracion", "Configuración de la corrida (JSON)", "resultados_modelo_riesgo_apagon/configuracion_corrida.json", ("json",), obligatorio=False),
        ),
    )


# ---------------------------------------------------------------------------- apagon: visor interactivo (escenarios)
class AdaptadorEscenariosApagon(AdaptadorTablero):
    definicion = TableroActualizable(
        id="apagon_visor", titulo="Riesgo de apagón · visor interactivo", descripcion="Las 468 corridas del modelo (ONI, simulaciones, horizonte) que usa el visor. Se generan con el comando local y se exportan a CSV.",
        archivos=(_archivo("escenarios", "Tanda de escenarios (CSV)", "escenarios_apagon.csv", ("csv",), descripcion="Se genera con: importar_escenarios_apagon --exportar-csv escenarios_apagon.csv"),),
    )
    errores_de_lectura = (SalidaModeloInvalidaError, ValueError)

    def __init__(self, repo: EscenarioApagonRepository) -> None:
        self._repo = repo

    def leer(self, carpeta: Path) -> Any:
        return leer_escenarios_csv(carpeta)

    def resumir(self, par: Any) -> tuple[Resumen, tuple[str, ...]]:
        escenarios, fuente = par
        return (("Escenarios", _n(len(escenarios))), ("Último mes de demanda", fuente.ultimo_mes_demanda or "—"), ("Último ONI observado", str(fuente.ultimo_oni_observado)), ("Semilla", str(fuente.semilla))), ()

    def guardar(self, par: Any) -> None:
        escenarios, fuente = par
        self._repo.reemplazar(escenarios, fuente)


def construir_adaptadores(
    carbon: ModeloCarbonRepository, dns: ModeloDnsRepository, resultados: ResultadoModeloRepository, escenarios: EscenarioApagonRepository
) -> dict[str, AdaptadorTablero]:
    """Un adaptador por tablero actualizable, en el orden en que se ofrecen en la pantalla."""
    adaptadores: list[AdaptadorTablero] = [
        AdaptadorCarbon(carbon), AdaptadorDns(dns),
        AdaptadorResultadoModelo("gas", _definicion_gas(), resultados),
        AdaptadorResultadoModelo("optimizacion", _definicion_optimizacion(), resultados),
        AdaptadorEscenariosApagon(escenarios),
        AdaptadorResultadoModelo("apagon", _definicion_apagon(), resultados),
    ]
    return {a.definicion.id: a for a in adaptadores}


Fabrica = Callable[[], dict[str, AdaptadorTablero]]
