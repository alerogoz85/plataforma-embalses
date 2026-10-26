"""Modelos analiticos con ficha (gas, optimizacion, apagon): entidades, fichas, casos de uso, lectores de salidas y repositorio."""
import csv
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from openpyxl import Workbook

from application.use_cases.modelo_analitico import ObtenerFichaModeloUseCase, ObtenerResultadosModeloUseCase
from domain.entities.modelo_analitico import (
    ESTADO_CON_RESULTADOS,
    MODELOS_CON_FICHA,
    Indicador,
    PuntoSerie,
    SerieResultado,
    TablaResultado,
)
from domain.exceptions import ModeloNoEncontradoError
from infrastructure.fichas.catalogo import FICHAS, FichasEnCodigo
from infrastructure.ingesta import importar_resultado_modelo
from infrastructure.ingesta.resultados_modelos import LECTORES, SalidaModeloInvalidaError
from infrastructure.ingesta.resultados_modelos.apagon import leer_apagon
from infrastructure.ingesta.resultados_modelos.gas import leer_gas
from infrastructure.ingesta.resultados_modelos.optimizacion import leer_optimizacion
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_modelo_resultado_repository import DuckDBModeloResultadoRepository
from tests.fakes import ResultadoModeloRepositoryEnMemoria, crear_resultado_modelo


# ------------------------------------------------------------------ entidades
class TestEntidades:
    def test_punto_con_banda_exige_orden_p10_y_p90(self):
        PuntoSerie("2026-10", 5.0, 4.0, 6.0)
        with pytest.raises(ValueError, match="p10 <= y <= p90"):
            PuntoSerie("2026-10", 5.0, 6.0, 7.0)
        with pytest.raises(ValueError, match="necesita p10 y p90"):
            PuntoSerie("2026-10", 5.0, 4.0, None)

    def test_serie_sin_puntos_o_con_puntos_repetidos(self):
        with pytest.raises(ValueError, match="no tiene puntos"):
            SerieResultado("s", "S", "u", "linea", ())
        with pytest.raises(ValueError, match="repetidos"):
            SerieResultado("s", "S", "u", "linea", (PuntoSerie("a", 1), PuntoSerie("a", 2)))
        with pytest.raises(ValueError, match="tipo de serie"):
            SerieResultado("s", "S", "u", "pastel", (PuntoSerie("a", 1),))

    def test_tabla_con_filas_de_largo_distinto(self):
        with pytest.raises(ValueError, match="distinto largo"):
            TablaResultado("t", "T", ("a", "b"), (("x",),))
        with pytest.raises(ValueError, match="no tiene columnas"):
            TablaResultado("t", "T", (), ())

    def test_indicador_con_nivel_desconocido(self):
        with pytest.raises(ValueError, match="nivel"):
            Indicador("x", "1", None, "morado")

    def test_resultado_exige_modelo_conocido_contenido_e_ids_unicos(self):
        r = crear_resultado_modelo()
        with pytest.raises(ValueError, match="modelo desconocido"):
            replace(r, modelo_id="otro")
        with pytest.raises(ValueError, match="al menos un indicador"):
            replace(r, indicadores=(), series=(), tablas=())
        with pytest.raises(ValueError, match="series con id repetido"):
            replace(r, series=(r.series[0], r.series[0]))
        with pytest.raises(ValueError, match="tablas con id repetido"):
            replace(r, tablas=(r.tablas[0], r.tablas[0]))


# ------------------------------------------------------------------ fichas
class TestFichas:
    def test_hay_una_ficha_por_modelo_y_su_id_coincide(self):
        assert set(FICHAS) == set(MODELOS_CON_FICHA)
        assert all(FichasEnCodigo().obtener(m).id == m for m in MODELOS_CON_FICHA)
        assert FichasEnCodigo().obtener("otro") is None

    @pytest.mark.parametrize("modelo", MODELOS_CON_FICHA)
    def test_cada_ficha_dice_su_estado_sus_limitaciones_y_que_archivos_importar(self, modelo):
        f = FICHAS[modelo]
        assert f.estado in ("sin_resultados", "prueba_tecnica")  # ninguna declara resultados que no existen
        titulos = [s.titulo for s in f.secciones]
        assert "Limitaciones documentadas" in titulos and "Método" in titulos
        assert f.datos_documentados and f.archivos_esperados and f.pregunta.endswith("?")
        assert f"--modelo {modelo}" in f.comando_importacion
        assert all(s.items for s in f.secciones)

    def test_la_optimizacion_es_prueba_tecnica_no_publicable(self):
        f = FICHAS["optimizacion"]
        assert f.estado == "prueba_tecnica"
        assert "publishable = false" in f.estado_detalle and "INSUFFICIENT_RISK_SAMPLE" in f.estado_detalle

    def test_gas_y_apagon_avisan_que_no_hay_resultados(self):
        assert "no incluyen el libro de resultados" in FICHAS["gas"].estado_detalle
        assert "no se dispone de una corrida" in FICHAS["apagon"].estado_detalle


# ------------------------------------------------------------------ casos de uso
class TestCasosDeUso:
    def test_ficha_sin_resultado_conserva_el_estado_documentado(self):
        caso = ObtenerFichaModeloUseCase(FichasEnCodigo(), ResultadoModeloRepositoryEnMemoria())
        assert caso.ejecutar("gas").estado == "sin_resultados"
        assert caso.ejecutar("optimizacion").estado == "prueba_tecnica"

    def test_ficha_con_resultado_importado_pasa_a_con_resultados(self):
        caso = ObtenerFichaModeloUseCase(FichasEnCodigo(), ResultadoModeloRepositoryEnMemoria(crear_resultado_modelo("apagon")))
        assert caso.ejecutar("apagon").estado == ESTADO_CON_RESULTADOS
        assert caso.ejecutar("gas").estado == "sin_resultados"  # el de otro modelo no cambia

    def test_resultados_no_disponibles_no_es_un_error(self):
        r = ObtenerResultadosModeloUseCase(ResultadoModeloRepositoryEnMemoria()).ejecutar("apagon")
        assert r.disponible is False and r.resultado is None and r.modelo_id == "apagon"

    def test_resultados_disponibles_se_traducen_al_dto(self):
        r = ObtenerResultadosModeloUseCase(ResultadoModeloRepositoryEnMemoria(crear_resultado_modelo())).ejecutar("apagon")
        assert r.disponible and r.resultado.origen == "Corrida de prueba"
        assert r.resultado.configuracion[0].nombre == "Simulaciones"
        assert r.resultado.series[1].puntos[0].p10 == 50.0
        assert r.resultado.tablas[0].filas[1] == ["2026-11", "Amarillo", None]

    @pytest.mark.parametrize("caso", [
        lambda: ObtenerFichaModeloUseCase(FichasEnCodigo(), ResultadoModeloRepositoryEnMemoria()).ejecutar("dns"),
        lambda: ObtenerResultadosModeloUseCase(ResultadoModeloRepositoryEnMemoria()).ejecutar("../etc"),
    ])
    def test_modelo_inexistente(self, caso):
        with pytest.raises(ModeloNoEncontradoError):
            caso()


# ------------------------------------------------------------------ repositorio DuckDB
@pytest.fixture
def repo(tmp_path):
    return DuckDBModeloResultadoRepository(DuckDBConnection(str(tmp_path / "m.duckdb")))


class TestRepositorio:
    def test_sin_resultado_devuelve_none(self, repo):
        assert repo.obtener("apagon") is None

    def test_ida_y_vuelta_conserva_todo(self, repo):
        original = crear_resultado_modelo()
        repo.reemplazar(original)
        assert repo.obtener("apagon") == original

    def test_reemplazar_solo_toca_ese_modelo(self, repo):
        repo.reemplazar(crear_resultado_modelo("apagon"))
        repo.reemplazar(crear_resultado_modelo("gas"))
        nuevo = replace(crear_resultado_modelo("apagon"), origen="Otra corrida")
        repo.reemplazar(nuevo)
        assert repo.obtener("apagon").origen == "Otra corrida"
        assert repo.obtener("gas").origen == "Corrida de prueba"

    def test_si_falla_queda_el_resultado_anterior(self, repo, monkeypatch):
        repo.reemplazar(crear_resultado_modelo())
        mala = replace(crear_resultado_modelo(), generado_en=None)  # NOT NULL violado despues del DELETE
        with pytest.raises(Exception):
            repo.reemplazar(mala)
        assert repo.obtener("apagon").origen == "Corrida de prueba"

    def test_reiniciar_la_base_no_borra_los_resultados(self, tmp_path):
        ruta = str(tmp_path / "r.duckdb")
        conexion = DuckDBConnection(ruta)
        DuckDBModeloResultadoRepository(conexion).reemplazar(crear_resultado_modelo())
        conexion.cerrar()
        assert DuckDBModeloResultadoRepository(DuckDBConnection(ruta, reiniciar=True)).obtener("apagon") is not None


# ------------------------------------------------------------------ lector del apagon
COLUMNAS_APAGON = [
    "mes", "oni_p10", "oni_p50", "oni_p90", "embalse_pct_p10", "embalse_pct_p50", "embalse_pct_p90", "demanda_mwh_p10",
    "demanda_mwh_p50", "demanda_mwh_p90", "generacion_hidro_mwh_p50", "oferta_total_mwh_p10", "oferta_total_mwh_p50",
    "oferta_total_mwh_p90", "deficit_mwh_p50", "deficit_mwh_p90", "probabilidad_deficit", "probabilidad_apagon_severo",
    "margen_reserva_pct_p50", "indice_riesgo_0_100", "semaforo",
]


def _fila_apagon(mes, semaforo="VERDE", indice=10.0, prob=0.02, severo=0.0, margen=0.20, d50=0.0, d90=5000.0):
    return {
        "mes": mes, "oni_p10": -0.5, "oni_p50": 0.5, "oni_p90": 1.5, "embalse_pct_p10": 40.0, "embalse_pct_p50": 55.0,
        "embalse_pct_p90": 70.0, "demanda_mwh_p10": 6_000_000, "demanda_mwh_p50": 6_500_000, "demanda_mwh_p90": 7_000_000,
        "generacion_hidro_mwh_p50": 4_000_000, "oferta_total_mwh_p10": 6_100_000, "oferta_total_mwh_p50": 6_600_000,
        "oferta_total_mwh_p90": 7_100_000, "deficit_mwh_p50": d50, "deficit_mwh_p90": d90, "probabilidad_deficit": prob,
        "probabilidad_apagon_severo": severo, "margen_reserva_pct_p50": margen, "indice_riesgo_0_100": indice, "semaforo": semaforo,
    }


def escribir_apagon(carpeta: Path, filas=None, franjas=True, json_extra=True) -> Path:
    base = carpeta / "resultados_modelo_riesgo_apagon"
    base.mkdir(parents=True)
    filas = filas or [
        _fila_apagon("2026-10-01", "VERDE", 10.0, 0.02, 0.0, 0.20),
        _fila_apagon("2026-11-01", "AMARILLO", 40.0, 0.12, 0.01, 0.08, 1000.0, 9000.0),
        _fila_apagon("2026-12-01 00:00:00", "ROJO", 85.0, 0.60, 0.20, -0.05, 90_000.0, 200_000.0),
    ]
    with (base / "resumen_mensual.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS_APAGON)
        w.writeheader()
        w.writerows(filas)
    if franjas:
        with (base / "detalle_franjas_horarias.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["mes", "franja", "probabilidad_deficit_horas", "deficit_medio_mwh_condicional", "deficit_esperado_mwh"])
            for mes in ("2026-11-01", "2026-12-01"):
                w.writerow([mes, "pico_noche_18_21", 0.5, 200.0, 4000.0])
                w.writerow([mes, "madrugada_00_05", 0.3, 100.0, 1000.0])
    if json_extra:
        (base / "configuracion_corrida.json").write_text(json.dumps({"modo_oni": "probabilistico", "n_simulaciones": 3000, "horizonte_meses": 18, "semilla": 20260729}), encoding="utf-8")
        (base / "metadatos_corrida.json").write_text(json.dumps({"ultimo_oni_observado": 0.3, "capacidad_vigente_mw": 21000.5, "modo_oni": "probabilistico"}), encoding="utf-8")
    return carpeta


class TestLectorApagon:
    def test_lee_indicadores_y_semaforo(self, tmp_path):
        r = leer_apagon(escribir_apagon(tmp_path))
        assert r.modelo_id == "apagon" and "3 meses, 2026-10 a 2026-12" in r.origen
        rojo = r.indicadores[0]
        assert (rojo.valor, rojo.nivel) == ("1", "critico") and "amarillo: 1 · verde: 1" in rojo.detalle
        assert r.indicadores[1].valor == "85.0" and r.indicadores[1].nivel == "critico"
        assert r.indicadores[2].valor == "60.0 %" and r.indicadores[3].valor == "-5.0 %"

    def test_convierte_unidades_fracciones_a_porcentaje_y_mwh_a_gwh(self, tmp_path):
        r = leer_apagon(escribir_apagon(tmp_path))
        series = {s.id: s for s in r.series}
        assert [p.y for p in series["probabilidad_deficit"].puntos] == [2.0, 12.0, 60.0]
        assert [p.y for p in series["margen_reserva"].puntos] == [20.0, 8.0, -5.0]
        d = series["demanda"].puntos[0]
        assert (d.p10, d.y, d.p90) == (6000.0, 6500.0, 7000.0)  # GWh
        assert series["deficit_p50"].tipo == "barras" and series["deficit_p50"].puntos[2].y == 90.0
        assert series["embalse"].puntos[0].p10 == 40.0 and series["oni"].puntos[0].p90 == 1.5

    def test_el_mes_con_hora_se_normaliza_y_se_ordena(self, tmp_path):
        filas = [_fila_apagon("2026-12-01 00:00:00"), _fila_apagon("2026-10-01")]
        r = leer_apagon(escribir_apagon(tmp_path, filas=filas))
        assert [p.x for p in r.series[0].puntos] == ["2026-10", "2026-12"]

    def test_tabla_de_meses_y_de_franjas(self, tmp_path):
        r = leer_apagon(escribir_apagon(tmp_path))
        meses = r.tablas[0]
        assert meses.filas[1][:3] == ("2026-11", "Amarillo", 40.0)
        franjas = r.tablas[1]
        assert franjas.filas[0][0] == "Pico de la noche (18-21 h)" and franjas.filas[0][2] == 8.0  # 2 x 4000 MWh = 8 GWh
        assert franjas.filas[0][1] == 50.0

    def test_las_franjas_y_los_json_son_opcionales(self, tmp_path):
        r = leer_apagon(escribir_apagon(tmp_path, franjas=False, json_extra=False))
        assert len(r.tablas) == 1 and r.configuracion == ()

    def test_configuracion_sin_duplicados(self, tmp_path):
        r = leer_apagon(escribir_apagon(tmp_path))
        etiquetas = [n for n, _ in r.configuracion]
        assert etiquetas.count("Modo ONI") == 1 and ("Simulaciones", "3000") in r.configuracion
        assert ("Capacidad vigente (MW)", "21000.5") in r.configuracion

    def test_siempre_advierte_que_es_adecuacion_nacional(self, tmp_path):
        r = leer_apagon(escribir_apagon(tmp_path))
        assert any("restricciones de red" in a for a in r.advertencias)

    @pytest.mark.parametrize("cambio,mensaje", [
        ({"semaforo": "MORADO"}, "semaforo desconocido"),
        ({"indice_riesgo_0_100": 120.0}, "entre 0 y 100"),
        ({"probabilidad_deficit": 1.5}, "fracciones entre 0 y 1"),
        ({"probabilidad_deficit": "abc"}, "no es un numero"),
        ({"mes": "ayer"}, "fecha invalida"),
        ({"embalse_pct_p50": ""}, "valor vacio"),
    ])
    def test_valores_invalidos(self, tmp_path, cambio, mensaje):
        with pytest.raises(SalidaModeloInvalidaError, match=mensaje):
            leer_apagon(escribir_apagon(tmp_path, filas=[{**_fila_apagon("2026-10-01"), **cambio}]))

    def test_meses_repetidos(self, tmp_path):
        with pytest.raises(SalidaModeloInvalidaError, match="repetidos"):
            leer_apagon(escribir_apagon(tmp_path, filas=[_fila_apagon("2026-10-01"), _fila_apagon("2026-10-15")]))

    def test_banda_desordenada_invalida_el_resultado(self, tmp_path):
        with pytest.raises(ValueError, match="p10 <= y <= p90"):
            leer_apagon(escribir_apagon(tmp_path, filas=[{**_fila_apagon("2026-10-01"), "embalse_pct_p10": 90.0}]))

    def test_falta_el_archivo_o_una_columna(self, tmp_path):
        with pytest.raises(SalidaModeloInvalidaError, match="falta el archivo"):
            leer_apagon(tmp_path)
        base = tmp_path / "resultados_modelo_riesgo_apagon"
        base.mkdir()
        (base / "resumen_mensual.csv").write_text("mes,semaforo\n2026-10-01,VERDE\n", encoding="utf-8")
        with pytest.raises(SalidaModeloInvalidaError, match="faltan columnas"):
            leer_apagon(tmp_path)


# ------------------------------------------------------------------ lector del gas
def _libro(ruta: Path, hojas: dict[str, list[list]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    libro = Workbook()
    libro.remove(libro.active)
    for nombre, filas in hojas.items():
        ws = libro.create_sheet(nombre)
        for fila in filas:
            ws.append(fila)
    libro.save(ruta)


ETQ_ANH, ETQ_MME = "Oferta gas comercializado (ANH)", "Oferta gas declarado (MME)"


def escribir_dca(carpeta: Path, validacion="DCA mejor que MME", sin_hoja=None) -> Path:
    mensual = [["Cohorte", "Periodo", "Anio", "Mes", "Segmento", ETQ_ANH, ETQ_MME, "Proyeccion Exponencial", "Proyeccion Hiperbolica", "Proyeccion Armonica"]]
    for cohorte in (2025, 2026):
        for mes in (1, 2, 3):
            mensual.append([cohorte, f"{cohorte}-{mes:02d}-01", cohorte, mes, "ajuste", 900.0 + mes, 950.0 + mes, 890.0, 895.0, None])
    hojas = {
        "Info": [["Pronostico de oferta de gas", ""], ["Ventana de ajuste", "todo"], ["Nota 3", "Ejercicio a nivel NACIONAL agregado, solo ilustrativo."], ["Nota 1", "Se permiten Di <= 0."]],
        "Parametros": [["Cohorte", "Modelo", "qi", "Di_mensual", "b", "R2_ajuste", "Bandera"], [2026, "Exponencial", 950.1, 0.01, 0.0, 0.98, ""]],
        "Proyeccion mensual": mensual,
        "Comparacion anual": [["Cohorte", "Anio"], [2026, 2026]],
        "Metricas vs MME": [["Cohorte", "Modelo", "Segmento", "MAE", "MAPE"], [2026, "Exponencial", "ajuste", 10.0, 1.1]],
        "Metricas vs ANH real": [["Cohorte", "Modelo", "Segmento", "MAE", "MAPE"], [2026, "Declaracion MME", "proyeccion", 20.0, 2.0], ["Nota al pie"]],
        "Resumen": [["Cohorte", "Meses_proyectados", "Mejor_modelo_vs_MME", "MAPE_%", "Validacion_ANH_real"],
                    [2025, 12, "Exponencial", 1.5, validacion], [2026, 8, "Armonica", 3.5, "MME mejor que DCA"], [2024, 0, "Exponencial", 5.5, "N/D"]],
    }
    if sin_hoja:
        hojas.pop(sin_hoja)
    _libro(carpeta / "Output" / "pronostico_dca" / "Pronostico_DCA_Declaraciones.xlsx", hojas)
    return carpeta


def escribir_prophet(carpeta: Path) -> Path:
    _libro(carpeta / "Output" / "pronostico" / "Pronostico_Produccion_Gas.xlsx", {
        "Pronóstico": [["CAMPO", "FECHA", "AÑO", "MES", "PRONÓSTICO (Mpcpd)", "IC INFERIOR (95%)", "IC SUPERIOR (95%)"],
                       ["A", "2026-08-01", 2026, 8, 10.0, 8.0, 12.0], ["B", "2026-08-01", 2026, 8, 5.0, 4.0, 6.0], ["A", "2026-09-01", 2026, 9, 11.0, 9.0, 13.0]],
        "Resumen Campos": [["CAMPO"], ["A"]],
        "Métricas Modelo": [["CAMPO", "MESES HISTÓRICOS", "PRODUCCIÓN TOTAL HIST.", "MAE VALIDACIÓN", "MAPE VALIDACIÓN (%)"], ["A", 100, 5000.0, 1.2, 8.5]],
        "Histórico": [["CAMPO", "FECHA", "PRODUCCIÓN REAL (Mpcpd)"], ["A", "2026-07-01", 9.0], ["B", "2026-07-01", 4.0]],
    })
    return carpeta


class TestLectorGas:
    def test_lee_la_cohorte_mas_reciente_con_sus_curvas(self, tmp_path):
        r = leer_gas(escribir_dca(tmp_path))
        ids = {s.id: s for s in r.series}
        assert all("cohorte 2026" in s.titulo for s in r.series)
        anh = ids["dca_oferta_gas_comercializado_(anh)"]
        assert [p.x for p in anh.puntos] == ["2026-01", "2026-02", "2026-03"] and anh.unidad == "MPCD"
        assert "dca_proyeccion_armonica" not in ids  # toda la curva armonica vacia: no se dibuja una serie sin puntos
        assert len(ids["dca_proyeccion_exponencial"].puntos) == 3

    def test_indicadores_cuentan_cohortes_y_quien_gana(self, tmp_path):
        r = leer_gas(escribir_dca(tmp_path))
        ind = {i.etiqueta: i for i in r.indicadores}
        assert ind["Cohortes de declaración procesadas"].valor == "3"
        assert ind["Cohortes donde la curva supera a la declaración"].valor == "1 de 2"  # la «N/D» no es validable
        assert ind["MAPE mediano del mejor modelo frente al MME"].valor == "3.5 %"

    def test_tablas_ignoran_la_nota_al_pie(self, tmp_path):
        r = leer_gas(escribir_dca(tmp_path))
        t = {t.id: t for t in r.tablas}
        assert set(t) == {"dca_resumen", "dca_metricas_anh", "dca_metricas_mme", "dca_parametros"}
        assert len(t["dca_metricas_anh"].filas) == 1 and t["dca_resumen"].columnas[0] == "Cohorte"

    def test_las_notas_del_libro_se_vuelven_advertencias_y_la_ventana_configuracion(self, tmp_path):
        r = leer_gas(escribir_dca(tmp_path))
        assert any("solo ilustrativo" in a for a in r.advertencias) and ("Ventana de ajuste", "todo") in r.configuracion

    def test_el_libro_de_prophet_suma_los_campos_por_mes(self, tmp_path):
        r = leer_gas(escribir_prophet(tmp_path))
        s = {s.id: s for s in r.series}
        assert [(p.x, p.y) for p in s["prophet_pronostico"].puntos] == [("2026-08", 15.0), ("2026-09", 11.0)]
        assert [(p.x, p.y) for p in s["prophet_historico"].puntos] == [("2026-07", 13.0)]
        assert r.indicadores[0].valor == "1" and any("15 campos" in a or "mayor producción" in a for a in r.advertencias)

    def test_los_dos_libros_juntos(self, tmp_path):
        escribir_dca(tmp_path)
        r = leer_gas(escribir_prophet(tmp_path))
        assert "curvas de declinación" in r.origen and "Prophet" in r.origen
        assert {"dca_resumen", "prophet_metricas"} <= {t.id for t in r.tablas}

    def test_sin_ningun_libro(self, tmp_path):
        with pytest.raises(SalidaModeloInvalidaError, match="ningun libro"):
            leer_gas(tmp_path)

    def test_falta_una_hoja(self, tmp_path):
        with pytest.raises(SalidaModeloInvalidaError, match="faltan hojas"):
            leer_gas(escribir_dca(tmp_path, sin_hoja="Resumen"))


# ------------------------------------------------------------------ lector de la optimizacion
def escribir_optimizacion(carpeta: Path, resumen=None, validacion=None, manifest=None) -> Path:
    base = carpeta / "05_resultados"
    base.mkdir(parents=True)
    resumen = {"classification": "INSUFFICIENT_RISK_SAMPLE", "publishable": False, "etapas": 82, "costo": {"esperado": 12.5}, "lista": [1, 2]} if resumen is None else resumen
    (base / "resumen.json").write_text(json.dumps(resumen), encoding="utf-8")
    if validacion is not None:
        (base / "validacion_tecnica.json").write_text(json.dumps(validacion), encoding="utf-8")
    if manifest is not None:
        (base / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return carpeta


class TestLectorOptimizacion:
    def test_muestra_el_resumen_y_advierte_si_no_es_publicable(self, tmp_path):
        r = leer_optimizacion(escribir_optimizacion(tmp_path))
        filas = dict(r.tablas[0].filas)
        assert filas["etapas"] == 82.0 and filas["costo.esperado"] == 12.5 and "lista" not in filas  # las listas no se expanden
        assert filas["publishable"] == "No"
        ind = r.indicadores[0]
        assert (ind.etiqueta, ind.valor, ind.nivel) == ("Corrida publicable", "No", "critico")
        assert any("no publicable" in a for a in r.advertencias) and any("INSUFFICIENT_RISK_SAMPLE" in a for a in r.advertencias)

    def test_si_es_publicable_no_advierte(self, tmp_path):
        r = leer_optimizacion(escribir_optimizacion(tmp_path, resumen={"publishable": True, "etapas": 82}))
        assert r.indicadores[0].valor == "Sí" and r.indicadores[0].nivel == "ok" and r.advertencias == ()

    def test_sin_senales_conocidas_solo_muestra_la_tabla(self, tmp_path):
        r = leer_optimizacion(escribir_optimizacion(tmp_path, resumen={"etapas": 82}))
        assert r.indicadores == () and r.advertencias == () and len(r.tablas) == 1

    def test_validacion_como_objeto_o_como_lista(self, tmp_path):
        r = leer_optimizacion(escribir_optimizacion(tmp_path, validacion={"balance_energia": {"ok": True, "error": 0.0001}}))
        assert dict(r.tablas[1].filas) == {"balance_energia.ok": "Sí", "balance_energia.error": 0.0001}
        lista = [{"control": "balance hidrico", "ok": True, "detalle": {"x": 1}}, {"control": "volumen", "ok": False}]
        r2 = leer_optimizacion(escribir_optimizacion(tmp_path / "otra", validacion=lista))
        assert r2.tablas[1].columnas == ("control", "ok", "detalle")
        assert r2.tablas[1].filas[0] == ("balance hidrico", "Sí", "…") and r2.tablas[1].filas[1][2] is None

    def test_el_manifiesto_aporta_la_procedencia(self, tmp_path):
        r = leer_optimizacion(escribir_optimizacion(tmp_path, manifest={"run_id": "abc", "version": "v002", "hashes": {"a": "b"}}))
        assert r.configuracion == (("run_id", "abc"), ("version", "v002"))

    @pytest.mark.parametrize("resumen", [[], {}, {"solo": {"lista": [1]}}, "texto"])
    def test_resumen_invalido(self, tmp_path, resumen):
        with pytest.raises(SalidaModeloInvalidaError):
            leer_optimizacion(escribir_optimizacion(tmp_path, resumen=resumen))

    def test_json_roto_o_ausente(self, tmp_path):
        with pytest.raises(SalidaModeloInvalidaError, match="falta el archivo"):
            leer_optimizacion(tmp_path)
        base = tmp_path / "05_resultados"
        base.mkdir()
        (base / "resumen.json").write_text("{no es json", encoding="utf-8")
        with pytest.raises(SalidaModeloInvalidaError, match="no es un JSON valido"):
            leer_optimizacion(tmp_path)

    def test_un_valor_infinito_o_texto_largo_no_rompe(self, tmp_path):
        r = leer_optimizacion(escribir_optimizacion(tmp_path, resumen={"x": float("inf"), "y": "ok"}))
        assert dict(r.tablas[0].filas)["x"] is None and dict(r.tablas[0].filas)["y"] == "ok"


# ------------------------------------------------------------------ importador (linea de comandos)
class TestImportador:
    def _correr(self, monkeypatch, *args):
        monkeypatch.setattr(sys, "argv", ["importar_resultado_modelo", *args])
        importar_resultado_modelo.main()

    def test_importa_y_deja_el_resultado_en_la_base(self, tmp_path, monkeypatch, capsys):
        carpeta = escribir_apagon(tmp_path / "proyecto")
        db = str(tmp_path / "base.duckdb")
        self._correr(monkeypatch, "--modelo", "apagon", "--carpeta", str(carpeta), "--db-path", db)
        assert "Importado 'apagon': 4 indicadores, 10 series, 2 tablas" in capsys.readouterr().out
        DuckDBConnection._instancia = None  # el importador usa la instancia unica; la soltamos para abrirla de nuevo
        leido = DuckDBModeloResultadoRepository(DuckDBConnection(db)).obtener("apagon")
        assert leido is not None and len(leido.series) == 10

    def test_si_los_archivos_son_invalidos_no_importa_nada(self, tmp_path, monkeypatch):
        with pytest.raises(SystemExit, match="No se importo nada: falta el archivo"):
            self._correr(monkeypatch, "--modelo", "apagon", "--carpeta", str(tmp_path), "--db-path", str(tmp_path / "x.duckdb"))
        assert not (tmp_path / "x.duckdb").exists()

    def test_solo_acepta_modelos_conocidos(self, tmp_path, monkeypatch):
        with pytest.raises(SystemExit):
            self._correr(monkeypatch, "--modelo", "dns", "--carpeta", str(tmp_path))

    def test_hay_un_lector_por_modelo(self):
        assert set(LECTORES) == set(MODELOS_CON_FICHA)
