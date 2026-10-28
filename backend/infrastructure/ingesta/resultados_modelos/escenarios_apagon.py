"""Genera la tanda de escenarios del visor de apagon ejecutando el modelo Monte Carlo (script 6) una vez por combinacion
de controles (modo de ONI, ONI, simulaciones, horizonte).

Requiere las dependencias del modelo (pandas, pyarrow, scipy, statsmodels, scikit-learn, matplotlib), que NO forman parte
de la API: esta tarea corre en el equipo del analista, igual que el modelo. La API solo lee lo que aqui se guarda.
El script del modelo se carga por ruta (su nombre empieza por «6. » y no es importable como modulo normal)."""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from domain.entities.escenario_apagon import (
    FRANJAS,
    HORIZONTES,
    MODO_MANUAL,
    MODO_PROBABILISTICO,
    SIMULACIONES,
    EscenarioApagon,
    FuenteEscenarios,
    MesEscenario,
    valores_oni,
)
from infrastructure.ingesta.resultados_modelos.comun import SalidaModeloInvalidaError

SCRIPT = Path("Scripts") / "6. modelo_riesgo_apagon_montecarlo.py"
BASE = Path("Datos") / "base_modelo_riesgo_apagon_nacional.parquet"
ORIGEN = "Modelo de riesgo de apagón (Monte Carlo) · base_modelo_riesgo_apagon_nacional.parquet"

_COLUMNAS_MES = {
    "mes": "mes", "indice_riesgo": "indice_riesgo_0_100", "probabilidad_deficit": "probabilidad_deficit",
    "probabilidad_apagon_severo": "probabilidad_apagon_severo", "semaforo": "semaforo",
    "oni_p10": "oni_p10", "oni_p50": "oni_p50", "oni_p90": "oni_p90",
    "embalse_pct_p10": "embalse_pct_p10", "embalse_pct_p50": "embalse_pct_p50", "embalse_pct_p90": "embalse_pct_p90",
    "demanda_mwh_p10": "demanda_mwh_p10", "demanda_mwh_p50": "demanda_mwh_p50", "demanda_mwh_p90": "demanda_mwh_p90",
    "oferta_mwh_p10": "oferta_total_mwh_p10", "oferta_mwh_p50": "oferta_total_mwh_p50", "oferta_mwh_p90": "oferta_total_mwh_p90",
    "deficit_mwh_p50": "deficit_mwh_p50", "deficit_mwh_p90": "deficit_mwh_p90", "margen_reserva_pct_p50": "margen_reserva_pct_p50",
}


def escenario_desde_resultado(resultado: dict, modo: str, oni: Optional[float], simulaciones: int, horizonte: int) -> EscenarioApagon:
    """Convierte la salida del modelo (`resumen_mensual` y `detalle_franjas_horarias`) en un EscenarioApagon validado."""
    resumen = resultado["resumen_mensual"]
    faltan = {origen for origen in _COLUMNAS_MES.values() if origen not in resumen.columns}
    if faltan:
        raise SalidaModeloInvalidaError(f"El resumen mensual del modelo no trae las columnas: {', '.join(sorted(faltan))}")
    franjas = resultado["detalle_franjas_horarias"]
    por_mes: dict[str, dict[str, float]] = {}
    for fila in franjas.itertuples(index=False):
        por_mes.setdefault(str(fila.mes)[:7], {})[fila.franja] = float(fila.deficit_esperado_mwh)
    meses = []
    for _, fila in resumen.iterrows():
        mes = str(fila["mes"])[:7]
        franja_mes = por_mes.get(mes, {})
        if set(franja_mes) != set(FRANJAS):
            raise SalidaModeloInvalidaError(f"El mes {mes} no trae el deficit de las {len(FRANJAS)} franjas horarias")
        valores = {destino: fila[origen] for destino, origen in _COLUMNAS_MES.items()}
        meses.append(MesEscenario(
            **{**{k: (float(v) if k not in ("mes", "semaforo") else str(v)) for k, v in valores.items()}, "mes": mes,
               "semaforo": str(valores["semaforo"]).upper()},
            deficit_por_franja_mwh=tuple(round(franja_mes[f], 2) for f in FRANJAS),
        ))
    return EscenarioApagon(modo=modo, oni=oni, simulaciones=simulaciones, horizonte=horizonte, meses=tuple(meses))


def combinaciones() -> list[tuple[str, Optional[float], int, int]]:
    """Todas las combinaciones que ofrecen los controles: cada ONI y el modo probabilistico, por simulaciones y horizonte."""
    modos = [(MODO_MANUAL, o) for o in valores_oni()] + [(MODO_PROBABILISTICO, None)]
    return [(m, o, s, h) for m, o in modos for s in SIMULACIONES for h in HORIZONTES]


def _cargar_modelo(carpeta: Path):
    ruta = carpeta / SCRIPT
    if not ruta.is_file():
        raise SalidaModeloInvalidaError(f"No se encuentra el script del modelo: {ruta}")
    carpeta_script = str(ruta.parent)
    sys.path.insert(0, carpeta_script)
    try:
        especificacion = importlib.util.spec_from_file_location("modelo_apagon_montecarlo", ruta)
        modulo = importlib.util.module_from_spec(especificacion)
        sys.modules[especificacion.name] = modulo  # los dataclasses del script lo necesitan registrado
        especificacion.loader.exec_module(modulo)
    except ImportError as error:
        raise SalidaModeloInvalidaError(f"Faltan dependencias del modelo: {error}") from error
    finally:
        sys.path.remove(carpeta_script)
    return modulo


def generar_escenarios(
    carpeta: Path, progreso: Optional[Callable[[int, int], None]] = None
) -> tuple[list[EscenarioApagon], FuenteEscenarios]:
    """Ejecuta el modelo en cada combinacion (semilla fija del propio modelo) y devuelve la tanda completa validada."""
    modelo = _cargar_modelo(carpeta)
    base = carpeta / BASE
    if not base.is_file():
        raise SalidaModeloInvalidaError(f"No se encuentra la base del modelo: {base}")
    df = modelo.leer_parquet_seguro(base)
    errores = modelo.validar_dataset(df)
    errores = errores.loc[errores["tipo"] == "ERROR"]
    if not errores.empty:
        raise SalidaModeloInvalidaError("La base no cumple los requisitos del modelo: " + "; ".join(errores["detalle"].astype(str)))

    todas = combinaciones()
    escenarios: list[EscenarioApagon] = []
    metadatos: dict = {}
    for n, (modo, oni, simulaciones, horizonte) in enumerate(todas, start=1):
        config = modelo.ConfiguracionModelo(
            modo_oni=modo, oni_manual=oni, n_simulaciones=simulaciones, horizonte_meses=horizonte
        )
        resultado = modelo.simular_escenario_completo(df, config)
        escenarios.append(escenario_desde_resultado(resultado, modo, oni, simulaciones, horizonte))
        metadatos = resultado["metadatos"]
        if progreso:
            progreso(n, len(todas))
    fuente = FuenteEscenarios(
        generado_en=datetime.now().replace(microsecond=0), origen=ORIGEN,
        ultimo_oni_observado=metadatos.get("ultimo_oni_observado"),
        ultimo_mes_demanda=str(metadatos.get("ultimo_mes_historico_demanda", ""))[:10] or None,
        semilla=int(modelo.ConfiguracionModelo().semilla),
    )
    return escenarios, fuente
