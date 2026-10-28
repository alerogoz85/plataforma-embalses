"""Archivo CSV con la tanda completa de escenarios del visor de apagon (para exportarla desde el equipo del analista y cargarla en el modulo
de actualizacion). Una fila por escenario y mes. La tanda debe traer TODAS las combinaciones de controles: el visor no puede quedar con huecos."""
from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Optional

from domain.entities.escenario_apagon import (
    FRANJAS,
    EscenarioApagon,
    FuenteEscenarios,
    MesEscenario,
    clave_escenario,
)
from infrastructure.ingesta.resultados_modelos.comun import SalidaModeloInvalidaError
from infrastructure.ingesta.resultados_modelos.escenarios_apagon import ORIGEN, combinaciones

CAMPOS_MES = [c for c in MesEscenario.__dataclass_fields__ if c != "deficit_por_franja_mwh"]
CAMPOS_FRANJA = [f"deficit_{f}_mwh" for f in FRANJAS]
CAMPOS_CONTROL = ["modo", "oni", "simulaciones", "horizonte"]
CAMPOS_FUENTE = ["ultimo_oni_observado", "ultimo_mes_demanda", "semilla"]
ENCABEZADO = CAMPOS_CONTROL + CAMPOS_MES + CAMPOS_FRANJA + CAMPOS_FUENTE


def a_csv(escenarios: list[EscenarioApagon], fuente: FuenteEscenarios) -> str:
    salida = io.StringIO(newline="")
    w = csv.writer(salida, lineterminator="\n")
    w.writerow(ENCABEZADO)
    for e in escenarios:
        for m in e.meses:
            w.writerow(
                [e.modo, "" if e.oni is None else f"{e.oni:.1f}", e.simulaciones, e.horizonte]
                + [getattr(m, c) for c in CAMPOS_MES] + [round(v, 4) for v in m.deficit_por_franja_mwh]
                + ["" if fuente.ultimo_oni_observado is None else fuente.ultimo_oni_observado, fuente.ultimo_mes_demanda or "", fuente.semilla]
            )
    return salida.getvalue()


def _numero(valor: str, columna: str, fila: int) -> float:
    try:
        n = float(valor)
    except ValueError as error:
        raise SalidaModeloInvalidaError(f"Escenarios: fila {fila}, «{columna}» no es un número ({valor[:20]!r})") from error
    if n != n or n in (float("inf"), float("-inf")):
        raise SalidaModeloInvalidaError(f"Escenarios: fila {fila}, «{columna}» no es un número finito")
    return n


def desde_csv(texto: str, generado_en: Optional[datetime] = None) -> tuple[list[EscenarioApagon], FuenteEscenarios]:
    lector = csv.DictReader(io.StringIO(texto))
    faltan = [c for c in ENCABEZADO if c not in (lector.fieldnames or [])]
    if faltan:
        raise SalidaModeloInvalidaError(f"Escenarios: faltan columnas {faltan}")
    grupos: dict[tuple, list[MesEscenario]] = {}
    fuentes: set[tuple] = set()
    for n, f in enumerate(lector, start=2):
        try:
            oni = None if f["modo"] == "probabilistico" else _numero(f["oni"], "oni", n)
            clave = (f["modo"], oni, int(_numero(f["simulaciones"], "simulaciones", n)), int(_numero(f["horizonte"], "horizonte", n)))
            valores = {c: (f[c].strip() if c in ("mes", "semaforo") else _numero(f[c], c, n)) for c in CAMPOS_MES}
            mes = MesEscenario(**valores, deficit_por_franja_mwh=tuple(_numero(f[c], c, n) for c in CAMPOS_FRANJA))
        except ValueError as error:
            if isinstance(error, SalidaModeloInvalidaError):
                raise
            raise SalidaModeloInvalidaError(f"Escenarios: fila {n}: {error}") from error
        grupos.setdefault(clave, []).append(mes)
        fuentes.add((f["ultimo_oni_observado"], f["ultimo_mes_demanda"], f["semilla"]))
    if not grupos:
        raise SalidaModeloInvalidaError("Escenarios: el archivo no trae filas")
    if len(fuentes) != 1:
        raise SalidaModeloInvalidaError("Escenarios: la procedencia (último ONI, último mes de demanda, semilla) debe ser la misma en todas las filas")

    escenarios = []
    for (modo, oni, simulaciones, horizonte), meses in grupos.items():
        try:
            escenarios.append(EscenarioApagon(modo=modo, oni=oni, simulaciones=simulaciones, horizonte=horizonte, meses=tuple(meses)))
        except ValueError as error:
            raise SalidaModeloInvalidaError(f"Escenarios ({modo}, ONI {oni}, {simulaciones} sim., {horizonte} meses): {error}") from error
    esperadas = {clave_escenario(*c) for c in combinaciones()}
    presentes = {e.clave for e in escenarios}
    if presentes != esperadas:
        faltan_n, sobran_n = len(esperadas - presentes), len(presentes - esperadas)
        raise SalidaModeloInvalidaError(
            f"Escenarios: la tanda debe traer las {len(esperadas)} combinaciones de controles (faltan {faltan_n}, sobran {sobran_n}); filas duplicadas cuentan como sobrantes"
        )
    oni_obs, ultimo_mes, semilla = next(iter(fuentes))
    fuente = FuenteEscenarios(
        generado_en=generado_en or datetime.now().replace(microsecond=0), origen=ORIGEN,
        ultimo_oni_observado=float(oni_obs) if oni_obs else None, ultimo_mes_demanda=ultimo_mes or None, semilla=int(float(semilla)),
    )
    return escenarios, fuente


def leer_escenarios_csv(carpeta: Path) -> tuple[list[EscenarioApagon], FuenteEscenarios]:
    ruta = Path(carpeta) / "escenarios_apagon.csv"
    if not ruta.is_file():
        raise SalidaModeloInvalidaError("Falta el archivo de escenarios (escenarios_apagon.csv)")
    return desde_csv(ruta.read_text(encoding="utf-8-sig"))
