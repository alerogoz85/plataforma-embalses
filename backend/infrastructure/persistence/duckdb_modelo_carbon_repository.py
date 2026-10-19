from __future__ import annotations

from typing import Optional

from domain.entities.modelo_carbon import (
    ComparacionXM,
    CriterioValidez,
    EpisodioValidacion,
    ErrorPorHorizonte,
    HistoricoCarbonMensual,
    InventarioCarbon,
    PaqueteModeloCarbon,
    ProyeccionCarbonMensual,
    SupuestoCarbon,
    TrimestreCarbon,
)
from domain.repositories.modelo_carbon_repository import ModeloCarbonRepository
from domain.value_objects.banda import Banda
from infrastructure.persistence.duckdb_connection import DuckDBConnection

_ID_UNICO = 1
_TABLAS = (
    "carbon_meta", "carbon_historico", "carbon_proyeccion", "carbon_trimestres", "carbon_inventario",
    "carbon_comparacion_xm", "carbon_error_horizonte", "carbon_episodios", "carbon_veredicto",
    "carbon_supuestos",
)


class DuckDBModeloCarbonRepository(ModeloCarbonRepository):
    """Guarda la corrida vigente del modelo de carbon en tablas `carbon_*` de DuckDB.

    Las consultas usan parametros (`?`), nunca texto armado a mano. La corrida se
    reemplaza dentro de una transaccion: o queda completa o queda la anterior."""

    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    # ---------------------------------------------------------------- lectura
    def obtener(self) -> Optional[PaqueteModeloCarbon]:
        meta = self._db.obtener_una_fila(
            "SELECT origen, poder_calorifico_mbtu_t FROM carbon_meta WHERE id = ?", [_ID_UNICO]
        )
        if meta is None:
            return None
        filas = self._db.obtener_filas
        return PaqueteModeloCarbon(
            origen=meta[0],
            poder_calorifico_mbtu_t=meta[1],
            historico=[
                HistoricoCarbonMensual(*f)
                for f in filas(
                    "SELECT fecha, carbon_gbtu_dia, techo_gbtu_dia, uso_techo_pct, aportes_pct_media, "
                    "roni, fuente, mes_completo, dias_con_dato FROM carbon_historico ORDER BY fecha"
                )
            ],
            proyeccion=[
                ProyeccionCarbonMensual(
                    fecha=f[0], dias=f[1], techo_gbtu_dia=f[2],
                    roni=Banda(f[3], f[4], f[5]), aportes_pct_media=Banda(f[6], f[7], f[8]),
                    uso_techo_pct=Banda(f[9], f[10], f[11]), carbon_gbtu_dia=Banda(f[12], f[13], f[14]),
                    carbon_kt_mes=Banda(f[15], f[16], f[17]), prob_supera_maximo_pct=f[18],
                    observado_parcial_gbtu_dia=f[19],
                )
                for f in filas("SELECT * FROM carbon_proyeccion ORDER BY fecha")
            ],
            trimestres=[
                TrimestreCarbon(f[0], f[1], Banda(f[2], f[3], f[4]))
                for f in filas("SELECT * FROM carbon_trimestres ORDER BY trimestre")
            ],
            inventario=[
                InventarioCarbon(*f)
                for f in filas("SELECT * FROM carbon_inventario ORDER BY fecha, dias_inventario")
            ],
            comparacion_xm=[
                ComparacionXM(f[0], Banda(f[2], f[3], f[4]), f[1], f[5], f[6], f[7])
                for f in filas("SELECT * FROM carbon_comparacion_xm ORDER BY fecha")
            ],
            errores_horizonte=[
                ErrorPorHorizonte(*f)
                for f in filas("SELECT * FROM carbon_error_horizonte ORDER BY horizonte_meses")
            ],
            episodios=[
                EpisodioValidacion(*f) for f in filas("SELECT * FROM carbon_episodios ORDER BY inicio")
            ],
            veredicto=[
                CriterioValidez(*f)
                for f in filas("SELECT criterio, resultado, cumple, interpretacion FROM carbon_veredicto ORDER BY orden")
            ],
            supuestos=[
                SupuestoCarbon(*f) for f in filas("SELECT nombre, valor FROM carbon_supuestos ORDER BY orden")
            ],
        )

    # -------------------------------------------------------------- escritura
    def reemplazar(self, paquete: PaqueteModeloCarbon) -> None:
        self._db.ejecutar("BEGIN TRANSACTION")
        try:
            for tabla in _TABLAS:
                self._db.ejecutar(f"DELETE FROM {tabla}")  # nombres fijos de arriba, no de usuario
            self._guardar(paquete)
        except Exception:
            self._db.ejecutar("ROLLBACK")
            raise
        self._db.ejecutar("COMMIT")

    def _guardar(self, p: PaqueteModeloCarbon) -> None:
        def lote(consulta: str, filas: list) -> None:
            if filas:  # DuckDB no admite un lote vacio
                self._db.ejecutar_lote(consulta, filas)

        self._db.ejecutar(
            "INSERT INTO carbon_meta VALUES (?, ?, ?)", [_ID_UNICO, p.origen, p.poder_calorifico_mbtu_t]
        )
        lote(
            "INSERT INTO carbon_historico VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(h.fecha, h.carbon_gbtu_dia, h.techo_gbtu_dia, h.uso_techo_pct, h.aportes_pct_media, h.roni,
              h.fuente, h.mes_completo, h.dias_con_dato) for h in p.historico],
        )
        lote(
            "INSERT INTO carbon_proyeccion VALUES (" + ", ".join(["?"] * 20) + ")",
            [(m.fecha, m.dias, m.techo_gbtu_dia,
              m.roni.p10, m.roni.p50, m.roni.p90,
              m.aportes_pct_media.p10, m.aportes_pct_media.p50, m.aportes_pct_media.p90,
              m.uso_techo_pct.p10, m.uso_techo_pct.p50, m.uso_techo_pct.p90,
              m.carbon_gbtu_dia.p10, m.carbon_gbtu_dia.p50, m.carbon_gbtu_dia.p90,
              m.carbon_kt_mes.p10, m.carbon_kt_mes.p50, m.carbon_kt_mes.p90,
              m.prob_supera_maximo_pct, m.observado_parcial_gbtu_dia) for m in p.proyeccion],
        )
        lote(
            "INSERT INTO carbon_trimestres VALUES (?, ?, ?, ?, ?)",
            [(t.trimestre, t.meses, t.carbon_mt.p10, t.carbon_mt.p50, t.carbon_mt.p90) for t in p.trimestres],
        )
        lote(
            "INSERT INTO carbon_inventario VALUES (?, ?, ?, ?)",
            [(i.fecha, i.dias_inventario, i.kt_p50, i.kt_p90) for i in p.inventario],
        )
        lote(
            "INSERT INTO carbon_comparacion_xm VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [(c.fecha, c.techo_gbtu_dia, c.modelo.p10, c.modelo.p50, c.modelo.p90, c.xm_estocastico_gbtu_dia,
              c.xm_historicas_min_gbtu_dia, c.xm_historicas_max_gbtu_dia) for c in p.comparacion_xm],
        )
        lote(
            "INSERT INTO carbon_error_horizonte VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(e.horizonte_meses, e.pronosticos, e.mae_modelo, e.mae_persistencia, e.mae_estacional,
              e.mae_climatologia, e.sesgo_modelo) for e in p.errores_horizonte],
        )
        lote(
            "INSERT INTO carbon_episodios VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [(e.episodio, e.inicio, e.fin, e.meses, e.real_gbtu_dia, e.p50_gbtu_dia, e.error_total_pct,
              e.mae_modelo, e.mae_ingenuo, e.cobertura_p10_p90_pct) for e in p.episodios],
        )
        lote(
            "INSERT INTO carbon_veredicto VALUES (?, ?, ?, ?, ?)",
            [(i, c.criterio, c.resultado, c.cumple, c.interpretacion) for i, c in enumerate(p.veredicto)],
        )
        lote(
            "INSERT INTO carbon_supuestos VALUES (?, ?, ?)",
            [(i, s.nombre, s.valor) for i, s in enumerate(p.supuestos)],
        )
