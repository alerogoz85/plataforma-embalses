from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from domain.entities.modelo_analitico import (
    DimensionFiltro,
    GraficoResultado,
    Indicador,
    LineaGrafico,
    PuntoSerie,
    ResultadoModelo,
    SerieResultado,
    TablaResultado,
)
from domain.repositories.modelo_analitico_repository import ResultadoModeloRepository
from infrastructure.persistence.duckdb_connection import DuckDBConnection


def a_json(r: ResultadoModelo) -> str:
    """Serializa el contenido (sin modelo_id ni fecha, que van en columnas)."""
    return json.dumps(
        {
            "origen": r.origen,
            "configuracion": [list(p) for p in r.configuracion],
            "indicadores": [
                {"etiqueta": i.etiqueta, "valor": i.valor, "detalle": i.detalle, "nivel": i.nivel} for i in r.indicadores
            ],
            "series": [
                {"id": s.id, "titulo": s.titulo, "unidad": s.unidad, "tipo": s.tipo,
                 "puntos": [{"x": p.x, "y": p.y, "p10": p.p10, "p90": p.p90} for p in s.puntos]}
                for s in r.series
            ],
            "tablas": [
                {"id": t.id, "titulo": t.titulo, "columnas": list(t.columnas), "filas": [list(f) for f in t.filas], "nota": t.nota,
                 "filtros_columna": [list(f) for f in t.filtros_columna]}
                for t in r.tablas
            ],
            "advertencias": list(r.advertencias),
            "dimensiones": [
                {"id": d.id, "etiqueta": d.etiqueta, "opciones": list(d.opciones), "por_defecto": d.por_defecto} for d in r.dimensiones
            ],
            "graficos": [
                {"id": g.id, "titulo": g.titulo, "unidad": g.unidad, "etiquetas": [list(e) for e in g.etiquetas],
                 "lineas": [
                     {"nombre": l.nombre, "estilo": l.estilo, "puntos": [{"x": p.x, "y": p.y, "p10": p.p10, "p90": p.p90} for p in l.puntos]}
                     for l in g.lineas
                 ]}
                for g in r.graficos
            ],
        },
        ensure_ascii=False,
    )


def desde_json(modelo_id: str, generado_en: datetime, contenido: str) -> ResultadoModelo:
    d = json.loads(contenido)
    return ResultadoModelo(
        modelo_id=modelo_id,
        generado_en=generado_en,
        origen=d["origen"],
        configuracion=tuple((n, v) for n, v in d["configuracion"]),
        indicadores=tuple(Indicador(**i) for i in d["indicadores"]),
        series=tuple(
            SerieResultado(id=s["id"], titulo=s["titulo"], unidad=s["unidad"], tipo=s["tipo"],
                           puntos=tuple(PuntoSerie(**p) for p in s["puntos"]))
            for s in d["series"]
        ),
        tablas=tuple(
            TablaResultado(id=t["id"], titulo=t["titulo"], columnas=tuple(t["columnas"]),
                           filas=tuple(tuple(f) for f in t["filas"]), nota=t["nota"],
                           filtros_columna=tuple((a, b) for a, b in t.get("filtros_columna", [])))
            for t in d["tablas"]
        ),
        advertencias=tuple(d["advertencias"]),
        # Los resultados guardados antes de existir estos campos se leen igual (sin dimensiones ni graficos).
        dimensiones=tuple(
            DimensionFiltro(id=x["id"], etiqueta=x["etiqueta"], opciones=tuple(x["opciones"]), por_defecto=x["por_defecto"])
            for x in d.get("dimensiones", [])
        ),
        graficos=tuple(
            GraficoResultado(
                id=g["id"], titulo=g["titulo"], unidad=g["unidad"], etiquetas=tuple((a, b) for a, b in g["etiquetas"]),
                lineas=tuple(LineaGrafico(nombre=l["nombre"], estilo=l["estilo"], puntos=tuple(PuntoSerie(**p) for p in l["puntos"])) for l in g["lineas"]),
            )
            for g in d.get("graficos", [])
        ),
    )


class DuckDBModeloResultadoRepository(ResultadoModeloRepository):
    """Guarda el ultimo resultado de cada modelo analitico. Consultas con parametros (`?`); el reemplazo es transaccional."""

    def __init__(self, conexion: DuckDBConnection) -> None:
        self._db = conexion

    def obtener(self, modelo_id: str) -> Optional[ResultadoModelo]:
        fila = self._db.obtener_una_fila(
            "SELECT generado_en, contenido FROM modelo_resultados WHERE modelo_id = ?", [modelo_id]
        )
        return None if fila is None else desde_json(modelo_id, fila[0], fila[1])

    def reemplazar(self, resultado: ResultadoModelo) -> None:
        self._db.ejecutar("BEGIN TRANSACTION")
        try:
            self._db.ejecutar("DELETE FROM modelo_resultados WHERE modelo_id = ?", [resultado.modelo_id])
            self._db.ejecutar(
                "INSERT INTO modelo_resultados VALUES (?, ?, ?)",
                [resultado.modelo_id, resultado.generado_en, a_json(resultado)],
            )
        except Exception:
            self._db.ejecutar("ROLLBACK")
            raise
        self._db.ejecutar("COMMIT")
