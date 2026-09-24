from __future__ import annotations

from datetime import date
from typing import Optional

from domain.entities.medicion_hidrologica import MedicionHidrologica
from domain.repositories.medicion_repository import MedicionRepository
from domain.value_objects.caudal import Caudal
from domain.value_objects.volumen import Volumen
from infrastructure.persistence.duckdb_connection import DuckDBConnection

_COLUMNAS = (
    "embalse_id, fecha, volumen_util_mm3, capacidad_util_mm3, energia_util_gwh, "
    "capacidad_util_energia_gwh, aportes_m3s, aportes_media_historica_m3s, "
    "vertimientos_m3s, turbinado_m3s"
)


def _caudal(valor: Optional[float]) -> Optional[Caudal]:
    return Caudal(valor) if valor is not None else None


def _valor(caudal: Optional[Caudal]) -> Optional[float]:
    return caudal.valor_m3s if caudal is not None else None


class DuckDBMedicionRepository(MedicionRepository):
    """Adaptador de persistencia para series de MedicionHidrologica sobre DuckDB."""

    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    def obtener_serie(
        self,
        embalse_id: str,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
    ) -> list[MedicionHidrologica]:
        condiciones = ["embalse_id = ?"]
        parametros: list = [embalse_id]
        if fecha_inicio is not None:
            condiciones.append("fecha >= ?")
            parametros.append(fecha_inicio)
        if fecha_fin is not None:
            condiciones.append("fecha <= ?")
            parametros.append(fecha_fin)

        consulta = (
            f"SELECT {_COLUMNAS} FROM mediciones WHERE "
            f"{' AND '.join(condiciones)} ORDER BY fecha"
        )
        return [self._fila_a_medicion(f) for f in self._db.obtener_filas(consulta, parametros)]

    def obtener_ultima_medicion(self, embalse_id: str) -> Optional[MedicionHidrologica]:
        fila = self._db.obtener_una_fila(
            f"SELECT {_COLUMNAS} FROM mediciones WHERE embalse_id = ? "
            "ORDER BY fecha DESC LIMIT 1",
            [embalse_id],
        )
        return self._fila_a_medicion(fila) if fila else None

    def obtener_medicion_en_fecha(
        self, embalse_id: str, fecha: date
    ) -> Optional[MedicionHidrologica]:
        fila = self._db.obtener_una_fila(
            f"SELECT {_COLUMNAS} FROM mediciones WHERE embalse_id = ? AND fecha = ?",
            [embalse_id, fecha],
        )
        return self._fila_a_medicion(fila) if fila else None

    def obtener_ultima_fecha(self) -> Optional[date]:
        fila = self._db.obtener_una_fila("SELECT max(fecha) FROM mediciones")
        return fila[0] if fila else None

    def guardar_lote(self, mediciones: list[MedicionHidrologica]) -> None:
        if not mediciones:
            return
        filas = [
            (
                m.embalse_id,
                m.fecha,
                m.volumen_util.valor_mm3,
                m.capacidad_util.valor_mm3,
                m.energia_util_gwh,
                m.capacidad_util_energia_gwh,
                _valor(m.aportes),
                m.aportes_media_historica_m3s,
                _valor(m.vertimientos),
                _valor(m.turbinado),
            )
            for m in mediciones
        ]
        self._db.ejecutar_lote(
            f"""
            INSERT INTO mediciones ({_COLUMNAS})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (embalse_id, fecha) DO UPDATE SET
                volumen_util_mm3 = excluded.volumen_util_mm3,
                capacidad_util_mm3 = excluded.capacidad_util_mm3,
                energia_util_gwh = excluded.energia_util_gwh,
                capacidad_util_energia_gwh = excluded.capacidad_util_energia_gwh,
                aportes_m3s = excluded.aportes_m3s,
                aportes_media_historica_m3s = excluded.aportes_media_historica_m3s,
                vertimientos_m3s = excluded.vertimientos_m3s,
                turbinado_m3s = excluded.turbinado_m3s
            """,
            filas,
        )

    @staticmethod
    def _fila_a_medicion(fila: tuple) -> MedicionHidrologica:
        (
            embalse_id,
            fecha,
            volumen_util,
            capacidad_util,
            energia_util,
            capacidad_energia,
            aportes,
            media_historica,
            vertimientos,
            turbinado,
        ) = fila
        return MedicionHidrologica(
            embalse_id=embalse_id,
            fecha=fecha,
            volumen_util=Volumen(volumen_util),
            capacidad_util=Volumen(capacidad_util),
            energia_util_gwh=energia_util,
            capacidad_util_energia_gwh=capacidad_energia,
            aportes=_caudal(aportes),
            aportes_media_historica_m3s=media_historica,
            vertimientos=_caudal(vertimientos),
            turbinado=_caudal(turbinado),
        )
