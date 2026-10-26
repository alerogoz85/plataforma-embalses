"""Lee las salidas del modelo de optimizacion hidrotermica (SDDP) y arma un ResultadoModelo.

Archivos (carpeta `05_resultados/` bajo la carpeta de la entrega):
* resumen.json (obligatorio), validacion_tecnica.json y manifest.json (opcionales)

El documento del modelo describe estos archivos pero no su esquema exacto, asi que el lector es tolerante:
muestra los valores simples del resumen tal cual vienen y reconoce solo las senales que el propio
documento nombra (`publishable` y la clasificacion INSUFFICIENT_RISK_SAMPLE) para advertir al lector.
No se interpreta ni se recalcula ningun valor economico."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from domain.entities.modelo_analitico import Indicador, ResultadoModelo, TablaResultado
from infrastructure.ingesta.resultados_modelos.comun import (
    TOPE_FILAS_TABLA,
    SalidaModeloInvalidaError,
    celda,
    leer_json,
    momento_de,
)

CARPETA = Path("05_resultados")
PROFUNDIDAD_MAXIMA = 3
CLAVES_PUBLICABLE = ("publishable", "publicable")
MARCA_MUESTRA_INSUFICIENTE = "INSUFFICIENT_RISK_SAMPLE"
CLAVES_PROCEDENCIA = ("run_id", "version", "wrapper_version", "created_at", "generated_at", "git_commit")


def _aplanar(valor: Any, prefijo: str = "", nivel: int = 0) -> list[tuple[str, Any]]:
    """Pares (clave.ruta, valor simple) de un JSON anidado, hasta una profundidad acotada. Las listas no se expanden."""
    if isinstance(valor, dict):
        if nivel >= PROFUNDIDAD_MAXIMA:
            return []
        salida: list[tuple[str, Any]] = []
        for clave, v in valor.items():
            salida.extend(_aplanar(v, f"{prefijo}.{clave}" if prefijo else str(clave), nivel + 1))
        return salida
    if isinstance(valor, list):
        return []
    return [(prefijo, valor)]


def _tabla_clave_valor(id_: str, titulo: str, pares: list[tuple[str, Any]], nota: str | None = None) -> TablaResultado:
    filas = tuple((clave, celda(valor)) for clave, valor in pares[:TOPE_FILAS_TABLA])
    if len(pares) > TOPE_FILAS_TABLA:
        nota = (nota + " " if nota else "") + f"Se muestran los primeros {TOPE_FILAS_TABLA} de {len(pares)} valores."
    return TablaResultado(id_, titulo, ("Campo", "Valor"), filas, nota)


def leer_optimizacion(carpeta: Path) -> ResultadoModelo:
    base = Path(carpeta) / CARPETA
    resumen = leer_json(base / "resumen.json", obligatorio=True)
    if not isinstance(resumen, dict) or not resumen:
        raise SalidaModeloInvalidaError("resumen.json debe ser un objeto JSON con al menos un campo")
    pares = _aplanar(resumen)
    if not pares:
        raise SalidaModeloInvalidaError("resumen.json no tiene valores simples que mostrar")

    advertencias: list[str] = []
    indicadores: list[Indicador] = []
    tablas = [_tabla_clave_valor("resumen", "Resumen de la corrida", pares)]

    publicable = next((v for k, v in pares if k.split(".")[-1].lower() in CLAVES_PUBLICABLE), None)
    if isinstance(publicable, bool):
        indicadores.append(Indicador(
            "Corrida publicable", "Sí" if publicable else "No",
            "marca de la propia corrida" , "ok" if publicable else "critico",
        ))
        if not publicable:
            advertencias.append(
                "La corrida está marcada como no publicable: sus cifras de costo y riesgo no son evidencia económica ni soporte de una recomendación de despacho."
            )
    if any(isinstance(v, str) and MARCA_MUESTRA_INSUFICIENTE in v for _, v in pares):
        advertencias.append(
            "Clasificación INSUFFICIENT_RISK_SAMPLE: la muestra de riesgo es demasiado pequeña (cola efectiva menor al mínimo provisional); E[costo], VaR y CVaR no son concluyentes."
        )

    validacion = leer_json(base / "validacion_tecnica.json", obligatorio=False)
    if isinstance(validacion, dict) and validacion:
        tablas.append(_tabla_clave_valor("validacion", "Validación técnica (balances y controles)", _aplanar(validacion)))
    elif isinstance(validacion, list) and validacion and all(isinstance(f, dict) for f in validacion):
        columnas = tuple(dict.fromkeys(k for f in validacion for k in f.keys()))
        tablas.append(TablaResultado(
            "validacion", "Validación técnica (balances y controles)", columnas,
            tuple(tuple(celda(f.get(c)) if not isinstance(f.get(c), (dict, list)) else "…" for c in columnas) for f in validacion[:TOPE_FILAS_TABLA]),
        ))

    configuracion: list[tuple[str, str]] = []
    manifiesto = leer_json(base / "manifest.json", obligatorio=False)
    if isinstance(manifiesto, dict):
        for clave in CLAVES_PROCEDENCIA:
            if clave in manifiesto and not isinstance(manifiesto[clave], (dict, list)):
                configuracion.append((clave, str(manifiesto[clave])))

    return ResultadoModelo(
        modelo_id="optimizacion", generado_en=momento_de(base / "resumen.json"),
        origen="Modelo de optimización hidrotérmica (SDDP/CVaR) · resumen de la corrida",
        configuracion=tuple(configuracion), indicadores=tuple(indicadores), tablas=tuple(tablas), advertencias=tuple(advertencias),
    )
