"""Lee la corrida del modelo DNS desde la carpeta del proyecto y la valida.

Archivos (relativos a la carpeta del proyecto `2. Modelo DNS`):
* Datos/outputs_datos/mapeo_subareas.csv: codigo, nombre, region y departamentos de cada subarea
* Datos/outputs/03_causas/eventos_enriquecidos.csv: eventos DNS y EDAC con su causa
* Datos/outputs/04_zonas/indice_priorizacion_zonas.csv: indice de priorizacion de zonas
* Datos/outputs/05_cambios_reporte/cambios_reporte_confirmados.csv: cambios en la forma de reportar
* Datos/outputs/07_modelo/metricas_evaluacion.csv, importancia_variables.csv y pronostico_AAAA-MM.csv

Se usa solo la biblioteca estandar. Nada se escribe si algun archivo es invalido."""
from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from domain.entities.modelo_dns import (
    REGION_SIN_ASIGNAR,
    CambioReporte,
    EventoDns,
    ImportanciaVariable,
    MetricaModelo,
    PaqueteModeloDns,
    PronosticoSubarea,
    SubareaDns,
    ZonaPriorizada,
)

RUTA_MAPEO = Path("Datos") / "outputs_datos" / "mapeo_subareas.csv"
RUTA_EVENTOS = Path("Datos") / "outputs" / "03_causas" / "eventos_enriquecidos.csv"
RUTA_ZONAS = Path("Datos") / "outputs" / "04_zonas" / "indice_priorizacion_zonas.csv"
RUTA_CAMBIOS = Path("Datos") / "outputs" / "05_cambios_reporte" / "cambios_reporte_confirmados.csv"
RUTA_METRICAS = Path("Datos") / "outputs" / "07_modelo" / "metricas_evaluacion.csv"
RUTA_IMPORTANCIA = Path("Datos") / "outputs" / "07_modelo" / "importancia_variables.csv"
CARPETA_MODELO = Path("Datos") / "outputs" / "07_modelo"
PATRON_PRONOSTICO = re.compile(r"^pronostico_(\d{4}-\d{2})\.csv$")

FUENTE = "SIMEM (DNS 3C77AF, EDAC 81FD6B, subáreas operativas 10F2C9)"


class ArchivoModeloDnsInvalidoError(Exception):
    """Un archivo del modelo DNS falta o no cumple el formato esperado."""


def _leer(ruta: Path, columnas: set[str]) -> list[dict[str, str]]:
    if not ruta.is_file():
        raise ArchivoModeloDnsInvalidoError(f"falta el archivo {ruta}")
    with ruta.open(encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        faltan = columnas - set(lector.fieldnames or [])
        if faltan:
            raise ArchivoModeloDnsInvalidoError(f"{ruta.name}: faltan columnas {sorted(faltan)}")
        return list(lector)


def _num(valor: str, archivo: str, columna: str, *, opcional: bool = False) -> Optional[float]:
    if valor is None or valor.strip() == "":
        if opcional:
            return None
        raise ArchivoModeloDnsInvalidoError(f"{archivo}: valor vacio en '{columna}'")
    try:
        return float(valor)
    except ValueError as error:
        raise ArchivoModeloDnsInvalidoError(f"{archivo}: '{columna}' no es un numero: {valor!r}") from error


def _texto(valor: Optional[str]) -> Optional[str]:
    valor = (valor or "").strip()
    return valor or None


def leer_modelo_dns(carpeta: Path) -> PaqueteModeloDns:
    carpeta = Path(carpeta)

    subareas = {}
    for f in _leer(carpeta / RUTA_MAPEO, {"codigo_subarea", "nombre_subarea", "region", "departamentos"}):
        subareas[f["codigo_subarea"]] = SubareaDns(
            codigo=f["codigo_subarea"], nombre=f["nombre_subarea"],
            region=_texto(f["region"]) or REGION_SIN_ASIGNAR, departamentos=_texto(f["departamentos"]),
        )

    eventos = []
    for f in _leer(
        carpeta / RUTA_EVENTOS,
        {"codigo_subarea", "fecha_hora", "tipo", "energia_no_atendida_kwh", "origen_evento", "causa_definitiva",
         "origen_causa_definitiva", "tipo_evento", "nivel_red"},
    ):
        try:
            fecha = datetime.fromisoformat(f["fecha_hora"])
        except ValueError as error:
            raise ArchivoModeloDnsInvalidoError(f"eventos: fecha invalida {f['fecha_hora']!r}") from error
        eventos.append(EventoDns(
            fecha_hora=fecha, codigo_subarea=f["codigo_subarea"], tipo=f["tipo"],
            energia_no_atendida_kwh=_num(f["energia_no_atendida_kwh"], "eventos", "energia_no_atendida_kwh"),
            origen_evento=_texto(f["origen_evento"]), causa_definitiva=f["causa_definitiva"],
            origen_causa_definitiva=f["origen_causa_definitiva"], tipo_evento=f["tipo_evento"], nivel_red=f["nivel_red"],
        ))
    # Subareas con eventos pero sin fila en el mapeo (hoy, un codigo con solo EDAC): se muestran por su codigo.
    for codigo in sorted({e.codigo_subarea for e in eventos} - set(subareas)):
        subareas[codigo] = SubareaDns(codigo=codigo, nombre=codigo, region=REGION_SIN_ASIGNAR)

    zonas = [
        ZonaPriorizada(
            ranking=int(_num(f["ranking"], "zonas", "ranking")), codigo_subarea=f["codigo_subarea"],
            indice_priorizacion=_num(f["indice_priorizacion"], "zonas", "indice_priorizacion"),
            energia_total_kwh=_num(f["energia_total_kwh"], "zonas", "energia_total_kwh"),
            n_eventos=int(_num(f["n_eventos"], "zonas", "n_eventos")),
            pct_criticos=_num(f["pct_criticos"], "zonas", "pct_criticos"),
            variacion_pct=_num(f["variacion_pct"], "zonas", "variacion_pct"),
        )
        for f in _leer(carpeta / RUTA_ZONAS, {"ranking", "codigo_subarea", "indice_priorizacion", "energia_total_kwh",
                                              "n_eventos", "pct_criticos", "variacion_pct"})
    ]
    cambios = [
        CambioReporte(
            codigo_subarea=f["codigo_subarea"], periodo_quiebre=f["periodo_quiebre"], direccion=f["direccion"],
            pct_generica_antes=_num(f["pct_descripcion_generica_antes"], "cambios", "pct_descripcion_generica_antes"),
            pct_generica_despues=_num(f["pct_descripcion_generica_despues"], "cambios", "pct_descripcion_generica_despues"),
            pct_causa_conocida_antes=_num(f["pct_causa_conocida_antes"], "cambios", "pct_causa_conocida_antes"),
            pct_causa_conocida_despues=_num(f["pct_causa_conocida_despues"], "cambios", "pct_causa_conocida_despues"),
        )
        for f in _leer(carpeta / RUTA_CAMBIOS, {"codigo_subarea", "periodo_quiebre", "direccion",
                                                "pct_descripcion_generica_antes", "pct_descripcion_generica_despues",
                                                "pct_causa_conocida_antes", "pct_causa_conocida_despues"})
    ]
    metricas = [
        MetricaModelo(modelo=f["modelo"], mae=_num(f["MAE"], "metricas", "MAE"), rmse=_num(f["RMSE"], "metricas", "RMSE"))
        for f in _leer(carpeta / RUTA_METRICAS, {"modelo", "MAE", "RMSE"})
    ]
    importancia = [
        ImportanciaVariable(
            variable=f["variable"],
            importancia_n_eventos=_num(f["importancia_n_eventos"], "importancia", "importancia_n_eventos"),
            importancia_energia_kwh=_num(f["importancia_energia_kwh"], "importancia", "importancia_energia_kwh"),
        )
        for f in _leer(carpeta / RUTA_IMPORTANCIA, {"variable", "importancia_n_eventos", "importancia_energia_kwh"})
    ]

    candidatos = sorted(
        (m.group(1), a) for a in (carpeta / CARPETA_MODELO).glob("pronostico_*.csv") if (m := PATRON_PRONOSTICO.match(a.name))
    )
    if not candidatos:
        raise ArchivoModeloDnsInvalidoError(f"no hay pronostico_AAAA-MM.csv en {carpeta / CARPETA_MODELO}")
    periodo, archivo = candidatos[-1]  # el mas reciente
    pronostico = [
        PronosticoSubarea(
            codigo_subarea=f["codigo_subarea"],
            n_eventos=_num(f["pronostico_n_eventos"], "pronostico", "pronostico_n_eventos"),
            energia_kwh=_num(f["pronostico_energia_kwh"], "pronostico", "pronostico_energia_kwh"),
        )
        for f in _leer(archivo, {"codigo_subarea", "pronostico_n_eventos", "pronostico_energia_kwh"})
    ]

    try:
        paquete = PaqueteModeloDns(
            origen="", periodo_pronostico=periodo, subareas=list(subareas.values()), eventos=eventos, zonas=zonas,
            cambios_reporte=cambios, metricas=metricas, importancia=importancia, pronostico=pronostico,
        )
    except ValueError as error:
        raise ArchivoModeloDnsInvalidoError(str(error)) from error
    origen = (
        f"Modelo DNS · {FUENTE} · eventos {paquete.fecha_inicio:%Y-%m-%d} a {paquete.fecha_corte:%Y-%m-%d} · "
        f"pronóstico {periodo}"
    )
    return PaqueteModeloDns(**{**paquete.__dict__, "origen": origen})
