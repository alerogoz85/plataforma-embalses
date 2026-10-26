"""Lee las salidas del modelo de gas (scripts 8 y 4) y arma un ResultadoModelo.

Libros de Excel (carpeta `Output/` bajo la carpeta del proyecto):
* pronostico_dca/Pronostico_DCA_Declaraciones.xlsx (script 8, curvas de Arps por cohorte de declaracion)
* pronostico/Pronostico_Produccion_Gas.xlsx (script 4, Prophet por campo; opcional)
Hace falta al menos uno. No se recalcula nada: se muestran las tablas y series tal como las dejo el modelo."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Optional

from openpyxl import load_workbook

from domain.entities.modelo_analitico import Indicador, PuntoSerie, ResultadoModelo, SerieResultado, TablaResultado
from infrastructure.ingesta.resultados_modelos.comun import (
    TOPE_FILAS_TABLA,
    SalidaModeloInvalidaError,
    celda,
    mes_iso,
    momento_de,
    numero,
)

RUTA_DCA = Path("Output") / "pronostico_dca" / "Pronostico_DCA_Declaraciones.xlsx"
RUTA_PROPHET = Path("Output") / "pronostico" / "Pronostico_Produccion_Gas.xlsx"
ETQ_MME = "Oferta gas declarado (MME)"
ETQ_ANH = "Oferta gas comercializado (ANH)"
CURVAS = ("Proyeccion Exponencial", "Proyeccion Hiperbolica", "Proyeccion Armonica")
HOJAS_DCA = {"Parametros", "Proyeccion mensual", "Resumen", "Metricas vs MME", "Metricas vs ANH real"}


def _hoja(libro, nombre: str, archivo: str) -> list[dict[str, Any]]:
    """Filas de una hoja como diccionarios por encabezado; ignora filas vacias y las notas de pie (una sola celda)."""
    if nombre not in libro.sheetnames:
        raise SalidaModeloInvalidaError(f"{archivo}: falta la hoja '{nombre}'")
    filas = list(libro[nombre].iter_rows(values_only=True))
    if not filas:
        raise SalidaModeloInvalidaError(f"{archivo}: la hoja '{nombre}' esta vacia")
    encabezado = [str(c).strip() if c is not None else "" for c in filas[0]]
    salida = []
    for fila in filas[1:]:
        if sum(1 for c in fila if c is not None) <= 1:  # fila vacia o nota al pie
            continue
        salida.append({h: v for h, v in zip(encabezado, fila) if h})
    return salida


def _tabla(id_: str, titulo: str, filas: list[dict[str, Any]], nota: Optional[str] = None) -> TablaResultado:
    columnas = tuple(filas[0].keys()) if filas else ("Sin filas",)
    recortada = len(filas) > TOPE_FILAS_TABLA
    cuerpo = tuple(tuple(celda(f.get(c)) for c in columnas) for f in filas[:TOPE_FILAS_TABLA]) if filas else ()
    if recortada:
        nota = (nota + " " if nota else "") + f"Se muestran las primeras {TOPE_FILAS_TABLA} de {len(filas)} filas."
    return TablaResultado(id_, titulo, columnas, cuerpo, nota)


def leer_gas(carpeta: Path) -> ResultadoModelo:
    carpeta = Path(carpeta)
    dca, prophet = carpeta / RUTA_DCA, carpeta / RUTA_PROPHET
    if not dca.is_file() and not prophet.is_file():
        raise SalidaModeloInvalidaError(f"no hay ningun libro de resultados: se buscaron {dca} y {prophet}")

    series: list[SerieResultado] = []
    tablas: list[TablaResultado] = []
    indicadores: list[Indicador] = []
    advertencias: list[str] = []
    configuracion: list[tuple[str, str]] = []
    momentos = []
    fuentes = []

    if dca.is_file():
        _leer_dca(dca, series, tablas, indicadores, advertencias, configuracion)
        momentos.append(momento_de(dca))
        fuentes.append("curvas de declinación (Arps)")
    if prophet.is_file():
        _leer_prophet(prophet, series, tablas, indicadores)
        momentos.append(momento_de(prophet))
        fuentes.append("pronóstico por campo (Prophet)")
        advertencias.append("El pronóstico por campo cubre solo los campos de mayor producción que el script seleccionó.")

    return ResultadoModelo(
        modelo_id="gas", generado_en=max(momentos), origen="Modelo de gas fiscalizado y declarado · " + " + ".join(fuentes),
        configuracion=tuple(configuracion), indicadores=tuple(indicadores), series=tuple(series), tablas=tuple(tablas),
        advertencias=tuple(advertencias),
    )


def _leer_dca(ruta: Path, series, tablas, indicadores, advertencias, configuracion) -> None:
    archivo = ruta.name
    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        faltan = HOJAS_DCA - set(libro.sheetnames)
        if faltan:
            raise SalidaModeloInvalidaError(f"{archivo}: faltan hojas {sorted(faltan)}")
        resumen = _hoja(libro, "Resumen", archivo)
        mensual = _hoja(libro, "Proyeccion mensual", archivo)
        parametros = _hoja(libro, "Parametros", archivo)
        met_anh = _hoja(libro, "Metricas vs ANH real", archivo)
        met_mme = _hoja(libro, "Metricas vs MME", archivo)
        info = [(str(f[0] or ""), str(f[1] or "")) for f in libro["Info"].iter_rows(values_only=True) if len(f) > 1] if "Info" in libro.sheetnames else []
    finally:
        libro.close()
    if not mensual:
        raise SalidaModeloInvalidaError(f"{archivo}: la hoja 'Proyeccion mensual' no tiene filas")

    # Serie: la cohorte de declaracion mas reciente, con lo observado, lo declarado y las tres curvas.
    for columna in ("Cohorte", "Periodo", ETQ_ANH, ETQ_MME, *CURVAS):
        if columna not in mensual[0]:
            raise SalidaModeloInvalidaError(f"{archivo}: 'Proyeccion mensual' no tiene la columna '{columna}'")
    cohorte = max(int(numero(f["Cohorte"], archivo, "Cohorte")) for f in mensual)
    de_la_cohorte = sorted((f for f in mensual if int(numero(f["Cohorte"], archivo, "Cohorte")) == cohorte), key=lambda f: str(f["Periodo"]))
    for columna, titulo in [(ETQ_ANH, "Gas comercializado observado (ANH)"), (ETQ_MME, "Oferta declarada (MME)"),
                            ("Proyeccion Exponencial", "Curva exponencial"), ("Proyeccion Hiperbolica", "Curva hiperbólica"),
                            ("Proyeccion Armonica", "Curva armónica")]:
        puntos = tuple(
            PuntoSerie(x=mes_iso(str(f["Periodo"]), archivo), y=y)
            for f in de_la_cohorte
            if (y := numero(f[columna], archivo, columna, opcional=True)) is not None
        )
        if puntos:
            series.append(SerieResultado(f"dca_{columna.lower().replace(' ', '_')}", f"{titulo} · cohorte {cohorte}", "MPCD", "linea", puntos))

    validables = [f for f in resumen if str(f.get("Validacion_ANH_real", "")).startswith(("DCA", "MME"))]
    dca_gana = sum(1 for f in validables if str(f["Validacion_ANH_real"]).startswith("DCA"))
    mapes = sorted(v for f in resumen if (v := numero(f.get("MAPE_%"), archivo, "MAPE_%", opcional=True)) is not None)
    indicadores.append(Indicador("Cohortes de declaración procesadas", str(len(resumen)), f"cohorte más reciente: {cohorte}", None))
    if validables:
        indicadores.append(Indicador(
            "Cohortes donde la curva supera a la declaración", f"{dca_gana} de {len(validables)}",
            "frente al gas comercializado real fuera de la ventana de ajuste", None,
        ))
    if mapes:
        indicadores.append(Indicador("MAPE mediano del mejor modelo frente al MME", f"{mapes[len(mapes) // 2]:.1f} %", "por cohorte, sobre el segmento evaluado", None))

    tablas.append(_tabla("dca_resumen", "Resumen por cohorte de declaración", resumen))
    tablas.append(_tabla("dca_metricas_anh", "Error de cada curva y de la declaración frente al gas comercializado real", met_anh))
    tablas.append(_tabla("dca_metricas_mme", "Error de cada curva frente a la declaración", met_mme))
    tablas.append(_tabla("dca_parametros", "Parámetros ajustados de las curvas", parametros,
                         "Di_mensual en 1/mes; en el agregado nacional b y Di no tienen interpretación física."))

    for clave, valor in info:
        if clave.startswith("Nota") and valor:
            advertencias.append(valor)
        elif clave in ("Ventana de ajuste", "Cohortes procesadas", "Modelos", "Insumo"):
            configuracion.append((clave, valor))


def _leer_prophet(ruta: Path, series, tablas, indicadores) -> None:
    archivo = ruta.name
    libro = load_workbook(ruta, read_only=True, data_only=True)
    try:
        pronostico = _hoja(libro, "Pronóstico", archivo)
        historico = _hoja(libro, "Histórico", archivo)
        metricas = _hoja(libro, "Métricas Modelo", archivo)
    finally:
        libro.close()

    def total_por_mes(filas, columna_valor):
        acumulado: dict[str, float] = defaultdict(float)
        for f in filas:
            acumulado[mes_iso(str(f["FECHA"]), archivo)] += numero(f[columna_valor], archivo, columna_valor)
        return tuple(PuntoSerie(x=x, y=y) for x, y in sorted(acumulado.items()))

    if pronostico:
        series.append(SerieResultado("prophet_pronostico", "Pronóstico mensual de los campos modelados (suma)", "MPCD", "linea",
                                     total_por_mes(pronostico, "PRONÓSTICO (Mpcpd)")))
    if historico:
        series.append(SerieResultado("prophet_historico", "Producción observada de los campos modelados (suma)", "MPCD", "linea",
                                     total_por_mes(historico, "PRODUCCIÓN REAL (Mpcpd)")))
    if metricas:
        tablas.append(_tabla("prophet_metricas", "Calidad del pronóstico por campo (12 meses de validación)", metricas,
                             "MAE y MAPE sobre los últimos 12 meses reservados para validar."))
        indicadores.append(Indicador("Campos con pronóstico propio", str(len(metricas)), "modelo Prophet por campo", None))
