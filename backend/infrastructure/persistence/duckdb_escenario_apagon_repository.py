from __future__ import annotations

import json
from typing import Optional

from domain.entities.escenario_apagon import EscenarioApagon, FuenteEscenarios, MesEscenario, clave_escenario
from domain.repositories.modelo_analitico_repository import EscenarioApagonRepository
from infrastructure.persistence.duckdb_connection import DuckDBConnection

MODELO = "apagon"
CLAVE_FUENTE = "fuente"


def _meses_a_json(meses: tuple[MesEscenario, ...]) -> list[list]:
    """Una fila por mes con los valores en el orden de los campos (mas compacto que un objeto por mes)."""
    return [[getattr(m, c) if c != "deficit_por_franja_mwh" else list(m.deficit_por_franja_mwh) for c in _CAMPOS] for m in meses]


_CAMPOS = tuple(MesEscenario.__dataclass_fields__)


def escenario_a_json(e: EscenarioApagon) -> str:
    return json.dumps({"campos": list(_CAMPOS), "meses": _meses_a_json(e.meses)}, ensure_ascii=False, separators=(",", ":"))


def escenario_desde_json(modo: str, oni: Optional[float], simulaciones: int, horizonte: int, contenido: str) -> EscenarioApagon:
    d = json.loads(contenido)
    meses = []
    for fila in d["meses"]:
        valores = dict(zip(d["campos"], fila))
        valores["deficit_por_franja_mwh"] = tuple(valores["deficit_por_franja_mwh"])
        meses.append(MesEscenario(**valores))
    return EscenarioApagon(modo=modo, oni=oni, simulaciones=simulaciones, horizonte=horizonte, meses=tuple(meses))


class DuckDBEscenarioApagonRepository(EscenarioApagonRepository):
    """Escenarios del modelo de apagon. Consultas con parametros (`?`); el reemplazo de la tanda es transaccional."""

    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    def obtener(self, modo: str, oni: Optional[float], simulaciones: int, horizonte: int) -> Optional[EscenarioApagon]:
        fila = self._db.obtener_una_fila(
            "SELECT contenido FROM modelo_escenarios WHERE modelo_id = ? AND clave = ?",
            [MODELO, clave_escenario(modo, oni, simulaciones, horizonte)],
        )
        return None if fila is None else escenario_desde_json(modo, oni, simulaciones, horizonte, fila[0])

    def fuente(self) -> Optional[FuenteEscenarios]:
        fila = self._db.obtener_una_fila(
            "SELECT generado_en, contenido FROM modelo_escenarios WHERE modelo_id = ? AND clave = ?", [MODELO, CLAVE_FUENTE]
        )
        if fila is None:
            return None
        d = json.loads(fila[1])
        return FuenteEscenarios(
            generado_en=fila[0], origen=d["origen"], ultimo_oni_observado=d["ultimo_oni_observado"],
            ultimo_mes_demanda=d["ultimo_mes_demanda"], semilla=d["semilla"],
        )

    def reemplazar(self, escenarios: list[EscenarioApagon], fuente: FuenteEscenarios) -> None:
        self._db.ejecutar("BEGIN TRANSACTION")
        try:
            self._db.ejecutar("DELETE FROM modelo_escenarios WHERE modelo_id = ?", [MODELO])
            for e in escenarios:
                self._db.ejecutar(
                    "INSERT INTO modelo_escenarios VALUES (?, ?, ?, ?)", [MODELO, e.clave, fuente.generado_en, escenario_a_json(e)]
                )
            contenido = json.dumps(
                {"origen": fuente.origen, "ultimo_oni_observado": fuente.ultimo_oni_observado,
                 "ultimo_mes_demanda": fuente.ultimo_mes_demanda, "semilla": fuente.semilla},
                ensure_ascii=False,
            )
            self._db.ejecutar("INSERT INTO modelo_escenarios VALUES (?, ?, ?, ?)", [MODELO, CLAVE_FUENTE, fuente.generado_en, contenido])
        except Exception:
            self._db.ejecutar("ROLLBACK")
            raise
        self._db.ejecutar("COMMIT")
