from __future__ import annotations

from typing import Optional

from domain.entities.modelo_dns import (
    CambioReporte,
    EventoDns,
    ImportanciaVariable,
    MetricaModelo,
    PaqueteModeloDns,
    PronosticoSubarea,
    SubareaDns,
    ZonaPriorizada,
)
from domain.repositories.modelo_dns_repository import ModeloDnsRepository
from infrastructure.persistence.duckdb_connection import DuckDBConnection

_ID_UNICO = 1
_TABLAS = (
    "dns_meta", "dns_subareas", "dns_eventos", "dns_zonas", "dns_cambios_reporte",
    "dns_metricas", "dns_importancia", "dns_pronostico",
)


class DuckDBModeloDnsRepository(ModeloDnsRepository):
    """Guarda la corrida vigente del modelo DNS en tablas `dns_*` de DuckDB.

    Las consultas usan parametros (`?`); la corrida se reemplaza en una transaccion."""

    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    def obtener(self) -> Optional[PaqueteModeloDns]:
        meta = self._db.obtener_una_fila("SELECT origen, periodo_pronostico FROM dns_meta WHERE id = ?", [_ID_UNICO])
        if meta is None:
            return None
        filas = self._db.obtener_filas
        return PaqueteModeloDns(
            origen=meta[0],
            periodo_pronostico=meta[1],
            subareas=[SubareaDns(*f) for f in filas("SELECT codigo, nombre, region, departamentos FROM dns_subareas ORDER BY codigo")],
            eventos=[
                EventoDns(*f)
                for f in filas(
                    "SELECT fecha_hora, codigo_subarea, tipo, energia_no_atendida_kwh, origen_evento, "
                    "causa_definitiva, origen_causa_definitiva, tipo_evento, nivel_red FROM dns_eventos ORDER BY fecha_hora"
                )
            ],
            zonas=[ZonaPriorizada(*f) for f in filas("SELECT * FROM dns_zonas ORDER BY ranking")],
            cambios_reporte=[
                CambioReporte(*f) for f in filas("SELECT * FROM dns_cambios_reporte ORDER BY periodo_quiebre, codigo_subarea")
            ],
            metricas=[MetricaModelo(*f) for f in filas("SELECT modelo, mae, rmse FROM dns_metricas ORDER BY orden")],
            importancia=[
                ImportanciaVariable(*f)
                for f in filas("SELECT variable, importancia_n_eventos, importancia_energia_kwh FROM dns_importancia ORDER BY orden")
            ],
            pronostico=[PronosticoSubarea(*f) for f in filas("SELECT * FROM dns_pronostico ORDER BY codigo_subarea")],
        )

    def reemplazar(self, paquete: PaqueteModeloDns) -> None:
        self._db.ejecutar("BEGIN TRANSACTION")
        try:
            for tabla in _TABLAS:
                self._db.ejecutar(f"DELETE FROM {tabla}")  # nombres fijos de arriba, no de usuario
            self._guardar(paquete)
        except Exception:
            self._db.ejecutar("ROLLBACK")
            raise
        self._db.ejecutar("COMMIT")

    def _guardar(self, p: PaqueteModeloDns) -> None:
        def lote(consulta: str, filas: list) -> None:
            if filas:  # DuckDB no admite un lote vacio
                self._db.ejecutar_lote(consulta, filas)

        self._db.ejecutar("INSERT INTO dns_meta VALUES (?, ?, ?)", [_ID_UNICO, p.origen, p.periodo_pronostico])
        lote("INSERT INTO dns_subareas VALUES (?, ?, ?, ?)", [(s.codigo, s.nombre, s.region, s.departamentos) for s in p.subareas])
        lote(
            "INSERT INTO dns_eventos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(e.fecha_hora, e.codigo_subarea, e.tipo, e.energia_no_atendida_kwh, e.origen_evento, e.causa_definitiva,
              e.origen_causa_definitiva, e.tipo_evento, e.nivel_red) for e in p.eventos],
        )
        lote(
            "INSERT INTO dns_zonas VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(z.ranking, z.codigo_subarea, z.indice_priorizacion, z.energia_total_kwh, z.n_eventos, z.pct_criticos,
              z.variacion_pct) for z in p.zonas],
        )
        lote(
            "INSERT INTO dns_cambios_reporte VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(c.codigo_subarea, c.periodo_quiebre, c.direccion, c.pct_generica_antes, c.pct_generica_despues,
              c.pct_causa_conocida_antes, c.pct_causa_conocida_despues) for c in p.cambios_reporte],
        )
        lote("INSERT INTO dns_metricas VALUES (?, ?, ?, ?)", [(i, m.modelo, m.mae, m.rmse) for i, m in enumerate(p.metricas)])
        lote(
            "INSERT INTO dns_importancia VALUES (?, ?, ?, ?)",
            [(i, v.variable, v.importancia_n_eventos, v.importancia_energia_kwh) for i, v in enumerate(p.importancia)],
        )
        lote("INSERT INTO dns_pronostico VALUES (?, ?, ?)", [(f.codigo_subarea, f.n_eventos, f.energia_kwh) for f in p.pronostico])
