"""Lee las salidas del modelo de riesgo de apagon (script 6) y arma un ResultadoModelo.

Archivos (carpeta `resultados_modelo_riesgo_apagon/` bajo la carpeta del proyecto):
* resumen_mensual.csv (obligatorio): una fila por mes con percentiles, probabilidades, margen, indice y semaforo
* detalle_franjas_horarias.csv, metadatos_corrida.json, configuracion_corrida.json (opcionales)

Unidades de origen: probabilidades y margen de reserva como fraccion 0-1; energia en MWh. Aqui se
muestran como porcentaje (x100) y GWh (/1000). No se recalcula nada: solo se transforman unidades."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from domain.entities.modelo_analitico import Indicador, PuntoSerie, ResultadoModelo, SerieResultado, TablaResultado
from infrastructure.ingesta.resultados_modelos.comun import (
    SalidaModeloInvalidaError,
    celda,
    leer_csv,
    leer_json,
    mes_iso,
    momento_de,
    numero,
)

CARPETA = Path("resultados_modelo_riesgo_apagon")
SEMAFOROS = {"VERDE": "ok", "AMARILLO": "alerta", "ROJO": "critico"}
COLUMNAS = {
    "mes", "oni_p10", "oni_p50", "oni_p90", "embalse_pct_p10", "embalse_pct_p50", "embalse_pct_p90",
    "demanda_mwh_p10", "demanda_mwh_p50", "demanda_mwh_p90", "oferta_total_mwh_p10", "oferta_total_mwh_p50",
    "oferta_total_mwh_p90", "deficit_mwh_p50", "deficit_mwh_p90", "probabilidad_deficit",
    "probabilidad_apagon_severo", "margen_reserva_pct_p50", "indice_riesgo_0_100", "semaforo",
}
NOMBRES_PARAMETROS = {
    "modo_oni": "Modo ONI", "oni_manual": "ONI manual", "n_simulaciones": "Simulaciones", "horizonte_meses": "Horizonte (meses)",
    "semilla": "Semilla", "ultimo_oni_observado": "Último ONI observado", "ultimo_mes_historico_demanda": "Último mes de demanda observada",
    "capacidad_vigente_mw": "Capacidad vigente (MW)",
}
NOMBRES_FRANJA = {
    "madrugada_00_05": "Madrugada (0-5 h)", "manana_06_11": "Mañana (6-11 h)", "tarde_12_17": "Tarde (12-17 h)",
    "pico_noche_18_21": "Pico de la noche (18-21 h)", "noche_22_23": "Noche (22-23 h)",
}


def leer_apagon(carpeta: Path) -> ResultadoModelo:
    base = Path(carpeta) / CARPETA
    archivo = "resumen_mensual.csv"
    filas = leer_csv(base / archivo, COLUMNAS)
    meses = []
    for f in filas:
        semaforo = f["semaforo"].strip().upper()
        if semaforo not in SEMAFOROS:
            raise SalidaModeloInvalidaError(f"{archivo}: semaforo desconocido {f['semaforo']!r}")
        indice = numero(f["indice_riesgo_0_100"], archivo, "indice_riesgo_0_100")
        prob = numero(f["probabilidad_deficit"], archivo, "probabilidad_deficit")
        severo = numero(f["probabilidad_apagon_severo"], archivo, "probabilidad_apagon_severo")
        if not 0 <= indice <= 100:
            raise SalidaModeloInvalidaError(f"{archivo}: el indice de riesgo debe estar entre 0 y 100 ({indice})")
        if not (0 <= prob <= 1 and 0 <= severo <= 1):
            raise SalidaModeloInvalidaError(f"{archivo}: las probabilidades deben ser fracciones entre 0 y 1")
        meses.append({"f": f, "mes": mes_iso(f["mes"], archivo), "semaforo": semaforo, "indice": indice, "prob": prob, "severo": severo})
    meses.sort(key=lambda m: m["mes"])
    if len({m["mes"] for m in meses}) != len(meses):
        raise SalidaModeloInvalidaError(f"{archivo}: hay meses repetidos")

    def num(m, columna, factor=1.0):
        return numero(m["f"][columna], archivo, columna) * factor

    def banda(titulo, id_, unidad, base_col, factor=1.0):
        puntos = tuple(
            PuntoSerie(x=m["mes"], y=num(m, f"{base_col}_p50", factor), p10=num(m, f"{base_col}_p10", factor), p90=num(m, f"{base_col}_p90", factor))
            for m in meses
        )
        return SerieResultado(id_, titulo, unidad, "linea", puntos)

    def simple(titulo, id_, unidad, valor, tipo="linea"):
        return SerieResultado(id_, titulo, unidad, tipo, tuple(PuntoSerie(x=m["mes"], y=valor(m)) for m in meses))

    series = (
        simple("Índice de riesgo (0-100)", "indice_riesgo", "puntos", lambda m: m["indice"]),
        simple("Probabilidad de déficit", "probabilidad_deficit", "%", lambda m: m["prob"] * 100),
        simple("Probabilidad de déficit severo", "probabilidad_deficit_severo", "%", lambda m: m["severo"] * 100),
        simple("Margen de reserva (P50)", "margen_reserva", "%", lambda m: num(m, "margen_reserva_pct_p50", 100)),
        banda("Nivel útil de los embalses (P10-P50-P90)", "embalse", "%", "embalse_pct"),
        banda("ONI simulado (P10-P50-P90)", "oni", "puntos", "oni"),
        banda("Demanda mensual (P10-P50-P90)", "demanda", "GWh", "demanda_mwh", 1 / 1000),
        banda("Oferta total mensual (P10-P50-P90)", "oferta", "GWh", "oferta_total_mwh", 1 / 1000),
        simple("Déficit esperado (P50)", "deficit_p50", "GWh", lambda m: num(m, "deficit_mwh_p50", 1 / 1000), "barras"),
        simple("Déficit en el escenario adverso (P90)", "deficit_p90", "GWh", lambda m: num(m, "deficit_mwh_p90", 1 / 1000), "barras"),
    )

    cuenta = {s: sum(1 for m in meses if m["semaforo"] == s) for s in SEMAFOROS}
    pico = max(meses, key=lambda m: m["indice"])
    max_prob = max(meses, key=lambda m: m["prob"])
    min_margen = min(meses, key=lambda m: num(m, "margen_reserva_pct_p50"))
    peor = "critico" if cuenta["ROJO"] else "alerta" if cuenta["AMARILLO"] else "ok"
    indicadores = (
        Indicador("Meses en rojo", str(cuenta["ROJO"]), f"de {len(meses)} meses · amarillo: {cuenta['AMARILLO']} · verde: {cuenta['VERDE']}", peor),
        Indicador("Mayor índice de riesgo", f"{pico['indice']:.1f}", f"{pico['mes']} · semáforo {pico['semaforo'].lower()}", SEMAFOROS[pico["semaforo"]]),
        Indicador("Mayor probabilidad de déficit", f"{max_prob['prob'] * 100:.1f} %", f"{max_prob['mes']} (déficit relativo sobre el umbral del modelo)", None),
        Indicador("Menor margen de reserva (P50)", f"{num(min_margen, 'margen_reserva_pct_p50', 100):.1f} %", min_margen["mes"], None),
    )

    tabla_meses = TablaResultado(
        "semaforo_mensual", "Semáforo y probabilidades por mes",
        ("Mes", "Semáforo", "Índice", "Prob. déficit (%)", "Prob. déficit severo (%)", "Margen de reserva P50 (%)", "Déficit P50 (GWh)", "Déficit P90 (GWh)"),
        tuple(
            (m["mes"], m["semaforo"].capitalize(), celda(m["indice"]), celda(m["prob"] * 100), celda(m["severo"] * 100),
             celda(num(m, "margen_reserva_pct_p50", 100)), celda(num(m, "deficit_mwh_p50", 1 / 1000)), celda(num(m, "deficit_mwh_p90", 1 / 1000)))
            for m in meses
        ),
        nota="El déficit es de adecuación de generación nacional; no incluye restricciones de red.",
    )
    tablas = [tabla_meses]

    franjas = base / "detalle_franjas_horarias.csv"
    if franjas.is_file():
        tablas.append(_tabla_franjas(franjas))

    configuracion = []
    for nombre in ("configuracion_corrida.json", "metadatos_corrida.json"):
        datos = leer_json(base / nombre, obligatorio=False)
        if isinstance(datos, dict):
            for clave, etiqueta in NOMBRES_PARAMETROS.items():
                if clave in datos and datos[clave] is not None and not isinstance(datos[clave], (dict, list)):
                    configuracion.append((etiqueta, str(datos[clave])))
    vistos, config_unica = set(), []
    for n, v in configuracion:
        if n not in vistos:
            vistos.add(n)
            config_unica.append((n, v))

    advertencias = (
        "Mide adecuación de generación nacional agregada: un déficit en cero no descarta racionamientos localizados por restricciones de red.",
        "La desagregación por franjas reparte un balance mensual ya cerrado; no predice un evento puntual.",
    )
    return ResultadoModelo(
        modelo_id="apagon", generado_en=momento_de(base / archivo),
        origen=f"Modelo de riesgo de apagón (Monte Carlo) · {len(meses)} meses, {meses[0]['mes']} a {meses[-1]['mes']}",
        configuracion=tuple(config_unica), indicadores=indicadores, series=series, tablas=tuple(tablas), advertencias=advertencias,
    )


def _tabla_franjas(ruta: Path) -> TablaResultado:
    archivo = ruta.name
    filas = leer_csv(ruta, {"mes", "franja", "probabilidad_deficit_horas", "deficit_esperado_mwh"})
    acumulado: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
    for f in filas:
        a = acumulado[f["franja"]]
        a[0] += numero(f["probabilidad_deficit_horas"], archivo, "probabilidad_deficit_horas")
        a[1] += numero(f["deficit_esperado_mwh"], archivo, "deficit_esperado_mwh")
        a[2] += 1
    ordenadas = sorted(acumulado.items(), key=lambda kv: -kv[1][1])
    return TablaResultado(
        "franjas", "Franja del día con más déficit esperado (suma del horizonte)",
        ("Franja", "Probabilidad media de déficit (%)", "Déficit esperado acumulado (GWh)"),
        tuple((NOMBRES_FRANJA.get(n, n), celda(a[0] / a[2] * 100), celda(a[1] / 1000)) for n, a in ordenadas),
        nota="La magnitud (no la probabilidad) es lo que distingue una franja de otra.",
    )
