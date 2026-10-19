"""Modelo de carbon termico: dominio, lectura de archivos, repositorio y casos de uso."""
from dataclasses import replace
from datetime import date
from pathlib import Path

import duckdb
import openpyxl
import pytest

from application.use_cases.modelo_carbon import (
    ObtenerComparacionXmUseCase,
    ObtenerInventarioCarbonUseCase,
    ObtenerResumenCarbonUseCase,
    ObtenerSerieCarbonUseCase,
    ObtenerValidacionCarbonUseCase,
)
from domain.entities.modelo_carbon import PaqueteModeloCarbon
from domain.exceptions import ModeloCarbonNoCargadoError
from domain.value_objects.banda import Banda
from infrastructure.ingesta.modelo_carbon_archivos import ArchivoModeloCarbonInvalidoError, leer_modelo_carbon
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_modelo_carbon_repository import DuckDBModeloCarbonRepository
from tests.fakes import ModeloCarbonRepositoryEnMemoria, crear_paquete_carbon


# ------------------------------------------------------------------ dominio
class TestBanda:
    def test_acepta_p10_menor_o_igual_p50_menor_o_igual_p90(self):
        Banda(1.0, 2.0, 3.0)
        Banda(5.0, 5.0, 5.0)

    @pytest.mark.parametrize("p", [(3, 2, 1), (1, 3, 2), (2, 1, 3)])
    def test_rechaza_valores_fuera_de_orden(self, p):
        with pytest.raises(ValueError, match="P10 <= P50 <= P90"):
            Banda(*p)


class TestPaquete:
    def test_el_maximo_mensual_ignora_el_mes_en_curso(self):
        paquete = crear_paquete_carbon()
        assert paquete.maximo_mensual_historico.carbon_gbtu_dia == 310.0
        assert paquete.maximo_mensual_historico.mes_completo

    def test_exige_historico_y_proyeccion(self):
        base = crear_paquete_carbon()
        with pytest.raises(ValueError, match="historico y proyeccion"):
            PaqueteModeloCarbon("x", 26.27, [], base.proyeccion)
        with pytest.raises(ValueError, match="historico y proyeccion"):
            PaqueteModeloCarbon("x", 26.27, base.historico, [])

    def test_rechaza_fechas_o_claves_repetidas(self):
        base = crear_paquete_carbon()
        with pytest.raises(ValueError, match="repetidas en 'historico'"):
            PaqueteModeloCarbon("x", 26.27, base.historico + [base.historico[0]], base.proyeccion)
        with pytest.raises(ValueError, match="repetidas en 'inventario'"):
            PaqueteModeloCarbon("x", 26.27, base.historico, base.proyeccion, inventario=base.inventario + [base.inventario[0]])

    def test_el_poder_calorifico_debe_ser_positivo(self):
        base = crear_paquete_carbon()
        with pytest.raises(ValueError, match="poder calorifico"):
            PaqueteModeloCarbon("x", 0, base.historico, base.proyeccion)


# ------------------------------------------------------------------ lectura de archivos
COLUMNAS_PROYECCION = [
    "fecha", "dias", "techo_gbtu_dia", "roni_p10", "roni_p50", "roni_p90",
    "aportes_pct_media_p10", "aportes_pct_media_p50", "aportes_pct_media_p90",
    "uso_techo_p10", "uso_techo_p50", "uso_techo_p90", "carbon_gbtu_dia_p10", "carbon_gbtu_dia_p50",
    "carbon_gbtu_dia_p90", "carbon_kt_mes_p10", "carbon_kt_mes_p50", "carbon_kt_mes_p90",
    "prob_supera_maximo_historico", "carbon_observado_parcial",
]


def _fila_proyeccion(fecha=date(2026, 10, 1), **cambios):
    fila = dict(
        fecha=fecha, dias=31, techo_gbtu_dia=403.3, roni_p10=2.0, roni_p50=2.4, roni_p90=2.8,
        aportes_pct_media_p10=0.4, aportes_pct_media_p50=0.57, aportes_pct_media_p90=0.74,
        uso_techo_p10=0.52, uso_techo_p50=0.74, uso_techo_p90=0.88, carbon_gbtu_dia_p10=208.0,
        carbon_gbtu_dia_p50=297.0, carbon_gbtu_dia_p90=355.0, carbon_kt_mes_p10=246.0, carbon_kt_mes_p50=351.0,
        carbon_kt_mes_p90=419.0, prob_supera_maximo_historico=0.235, carbon_observado_parcial=213.0,
    )
    fila.update(cambios)
    return fila


def _escribir_hoja(libro, nombre, columnas, filas):
    hoja = libro.create_sheet(nombre)
    hoja.append(columnas)
    for fila in filas:
        hoja.append([fila.get(c) for c in columnas])


def escribir_modelo(carpeta: Path, proyeccion=None, sin_hoja=None, sin_columna=None, poder="26.27"):
    """Crea en `carpeta` los tres archivos minimos que entrega el modelo."""
    (carpeta / "resultados" / "evaluacion").mkdir(parents=True)
    (carpeta / "datos" / "base").mkdir(parents=True)
    hojas = {
        "proyeccion_mensual": (COLUMNAS_PROYECCION, proyeccion if proyeccion is not None else [_fila_proyeccion()]),
        "trimestres": (["trimestre", "meses_incluidos", "carbon_mt_p10", "carbon_mt_p50", "carbon_mt_p90"],
                       [dict(trimestre="2026Q4", meses_incluidos=3, carbon_mt_p10=0.8, carbon_mt_p50=1.1, carbon_mt_p90=1.3)]),
        "inventario": (["fecha", "dias_inventario", "inventario_kt_p50", "inventario_kt_p90"],
                       [dict(fecha=date(2026, 10, 1), dias_inventario=45, inventario_kt_p50=510.0, inventario_kt_p90=607.0)]),
        "comparacion_xm": (["fecha", "carbon_gbtu_dia_p10", "carbon_gbtu_dia_p50", "carbon_gbtu_dia_p90", "techo_gbtu_dia",
                            "xm_promedio", "xm_h15_17_oefatraso", "xm_h23_25_oefatraso", "xm_h91_93_oefatraso"],
                           [dict(fecha=date(2026, 10, 1), carbon_gbtu_dia_p10=208.0, carbon_gbtu_dia_p50=297.0,
                                 carbon_gbtu_dia_p90=355.0, techo_gbtu_dia=403.3, xm_promedio=465.0,
                                 xm_h15_17_oefatraso=233.0, xm_h23_25_oefatraso=232.0, xm_h91_93_oefatraso=None)]),
        "validacion_metricas": (["episodio", "inicio", "fin", "meses", "carbon_real_promedio", "carbon_p50_promedio",
                                 "error_total_episodio_pct", "mae_modelo", "mae_ingenuo", "cobertura_p10_p90"],
                                [dict(episodio="El Niño 2023-2024", inicio=date(2023, 7, 1), fin=date(2024, 2, 1), meses=8,
                                      carbon_real_promedio=270.0, carbon_p50_promedio=258.0, error_total_episodio_pct=-0.047,
                                      mae_modelo=58.0, mae_ingenuo=95.0, cobertura_p10_p90=0.875)]),
        "supuestos": (["supuesto", "valor"], [dict(supuesto="Poder calorífico [MBTU/t]", valor=poder),
                                              dict(supuesto="Simulaciones", valor=20000)]),
    }
    libro = openpyxl.Workbook()
    libro.remove(libro.active)
    for nombre, (columnas, filas) in hojas.items():
        if nombre == sin_hoja:
            continue
        if sin_columna and sin_columna[0] == nombre:
            columnas = [c for c in columnas if c != sin_columna[1]]
        _escribir_hoja(libro, nombre, columnas, filas)
    libro.save(carpeta / "resultados" / "proyeccion_carbon.xlsx")

    evaluacion = openpyxl.Workbook()
    evaluacion.remove(evaluacion.active)
    _escribir_hoja(evaluacion, "veredicto", ["criterio", "resultado", "cumple", "interpretacion"],
                   [dict(criterio="RESET", resultado="p=0.59", cumple="Sí", interpretacion="Forma adecuada"),
                    dict(criterio="Breusch-Pagan", resultado="p=0.001", cumple="No", interpretacion="Varianza cambiante")])
    _escribir_hoja(evaluacion, "error_por_horizonte",
                   ["horizonte", "n", "mae_modelo", "mae_persistencia", "mae_estacional", "mae_climatologia", "sesgo_modelo"],
                   [dict(horizonte=1, n=65, mae_modelo=45.8, mae_persistencia=47.3, mae_estacional=112.3, mae_climatologia=87.2, sesgo_modelo=-3.9)])
    evaluacion.save(carpeta / "resultados" / "evaluacion" / "evaluacion_modelo.xlsx")

    conexion = duckdb.connect()
    conexion.execute(
        "CREATE TABLE t(fecha DATE, carbon_gbtu_dia DOUBLE, techo_carbon_gbtu_dia DOUBLE, uso_techo_carbon DOUBLE, "
        "aportes_pct_media DOUBLE, roni DOUBLE, fuente_carbon VARCHAR, mes_completo BOOLEAN, dias_con_dato INTEGER)"
    )
    conexion.execute(
        "INSERT INTO t VALUES "
        "(DATE '2026-09-01', 299.7, 403.3, 0.743, 0.655, 1.7, 'Estimado', true, 30), "
        "(DATE '2026-10-01', 213.3, 403.3, 0.529, NULL, NULL, 'Estimado', false, 15), "
        "(DATE '2005-01-01', 53.6, NULL, NULL, NULL, 0.62, 'Sinergox', true, 31), "
        "(DATE '2005-02-01', NULL, NULL, NULL, NULL, 0.5, 'Sinergox', true, 28)"
    )
    conexion.execute("COPY t TO '" + str(carpeta / "datos" / "base" / "base_mensual_nacional.parquet") + "' (FORMAT PARQUET)")
    conexion.close()
    return carpeta


class TestLecturaDeArchivos:
    def test_lee_una_corrida_completa_y_convierte_fracciones_a_porcentaje(self, tmp_path):
        paquete = leer_modelo_carbon(escribir_modelo(tmp_path))
        m = paquete.proyeccion[0]
        assert m.fecha == date(2026, 10, 1) and m.carbon_gbtu_dia == Banda(208.0, 297.0, 355.0)
        assert m.aportes_pct_media == Banda(40.0, 57.0, 74.0)  # fraccion -> %
        assert m.uso_techo_pct.p50 == 74.0 and m.prob_supera_maximo_pct == 23.5
        assert m.observado_parcial_gbtu_dia == 213.0
        assert paquete.poder_calorifico_mbtu_t == 26.27
        assert "20000 simulaciones" in paquete.origen

    def test_el_historico_ordena_por_fecha_y_omite_meses_sin_consumo(self, tmp_path):
        historico = leer_modelo_carbon(escribir_modelo(tmp_path)).historico
        assert [h.fecha for h in historico] == [date(2005, 1, 1), date(2026, 9, 1), date(2026, 10, 1)]
        assert historico[0].techo_gbtu_dia is None and historico[0].uso_techo_pct is None
        assert historico[1].uso_techo_pct == 74.3 and historico[1].aportes_pct_media == 65.5
        assert historico[2].mes_completo is False and historico[2].aportes_pct_media is None

    def test_resume_los_casos_historicos_de_xm_en_un_minimo_y_un_maximo(self, tmp_path):
        c = leer_modelo_carbon(escribir_modelo(tmp_path)).comparacion_xm[0]
        assert (c.xm_historicas_min_gbtu_dia, c.xm_historicas_max_gbtu_dia) == (232.0, 233.0)
        assert c.xm_estocastico_gbtu_dia == 465.0

    def test_lee_validacion_y_veredicto(self, tmp_path):
        paquete = leer_modelo_carbon(escribir_modelo(tmp_path))
        assert paquete.episodios[0].error_total_pct == -4.7 and paquete.episodios[0].cobertura_p10_p90_pct == 87.5
        assert [c.cumple for c in paquete.veredicto] == [True, False]
        assert paquete.errores_horizonte[0].mae_modelo == 45.8

    def test_los_porcentajes_de_proyeccion_no_pasan_de_100_por_error_de_unidades(self, tmp_path):
        # una banda desordenada delata un archivo mal armado y detiene la importacion
        malo = [_fila_proyeccion(carbon_gbtu_dia_p10=400.0)]
        with pytest.raises(ArchivoModeloCarbonInvalidoError, match="P10 <= P50 <= P90"):
            leer_modelo_carbon(escribir_modelo(tmp_path, proyeccion=malo))

    def test_falta_una_hoja(self, tmp_path):
        with pytest.raises(ArchivoModeloCarbonInvalidoError, match="falta la hoja 'inventario'"):
            leer_modelo_carbon(escribir_modelo(tmp_path, sin_hoja="inventario"))

    def test_falta_una_columna(self, tmp_path):
        with pytest.raises(ArchivoModeloCarbonInvalidoError, match="faltan columnas xm_promedio"):
            leer_modelo_carbon(escribir_modelo(tmp_path, sin_columna=("comparacion_xm", "xm_promedio")))

    def test_valor_no_numerico(self, tmp_path):
        with pytest.raises(ArchivoModeloCarbonInvalidoError, match="no es numerico"):
            leer_modelo_carbon(escribir_modelo(tmp_path, proyeccion=[_fila_proyeccion(techo_gbtu_dia="alto")]))

    def test_fecha_invalida(self, tmp_path):
        with pytest.raises(ArchivoModeloCarbonInvalidoError, match="fecha no valida"):
            leer_modelo_carbon(escribir_modelo(tmp_path, proyeccion=[_fila_proyeccion(fecha="octubre")]))

    def test_poder_calorifico_no_numerico(self, tmp_path):
        with pytest.raises(ArchivoModeloCarbonInvalidoError, match="poder calorifico"):
            leer_modelo_carbon(escribir_modelo(tmp_path, poder="alto"))

    def test_carpeta_sin_archivos(self, tmp_path):
        with pytest.raises(ArchivoModeloCarbonInvalidoError, match="No existe"):
            leer_modelo_carbon(tmp_path)


# ------------------------------------------------------------------ repositorio DuckDB
@pytest.fixture
def repo(tmp_path):
    return DuckDBModeloCarbonRepository(DuckDBConnection(str(tmp_path / "carbon.duckdb")))


class TestRepositorioDuckDB:
    def test_sin_corrida_devuelve_none(self, repo):
        assert repo.obtener() is None

    def test_guarda_y_devuelve_la_misma_corrida(self, repo):
        original = crear_paquete_carbon()
        repo.reemplazar(original)
        leido = repo.obtener()
        assert leido.origen == original.origen and leido.poder_calorifico_mbtu_t == original.poder_calorifico_mbtu_t
        assert leido.historico == original.historico
        assert leido.proyeccion == original.proyeccion
        assert leido.inventario == sorted(original.inventario, key=lambda i: (i.fecha, i.dias_inventario))
        assert leido.trimestres == original.trimestres and leido.comparacion_xm == original.comparacion_xm
        assert leido.errores_horizonte == original.errores_horizonte and leido.veredicto == original.veredicto
        assert [s.nombre for s in leido.supuestos] == [s.nombre for s in original.supuestos]

    def test_una_corrida_nueva_reemplaza_a_la_anterior(self, repo):
        repo.reemplazar(crear_paquete_carbon())
        nueva = crear_paquete_carbon()
        repo.reemplazar(PaqueteModeloCarbon("Otra corrida", 25.0, nueva.historico[:5], nueva.proyeccion[:2]))
        leido = repo.obtener()
        assert leido.origen == "Otra corrida" and len(leido.historico) == 5 and len(leido.proyeccion) == 2
        assert leido.trimestres == [] and leido.veredicto == []

    def test_si_falla_a_mitad_queda_la_corrida_anterior(self, repo):
        repo.reemplazar(crear_paquete_carbon())
        mala = crear_paquete_carbon()
        mal_historico = [replace(h, carbon_gbtu_dia=None) if i == 10 else h for i, h in enumerate(mala.historico)]
        with pytest.raises(Exception):  # NOT NULL violado despues de haber borrado y escrito otras tablas
            repo.reemplazar(PaqueteModeloCarbon("Mala", 26.27, mal_historico, mala.proyeccion))
        leido = repo.obtener()
        assert leido.origen == "Modelo de prueba" and len(leido.historico) == 24 and len(leido.trimestres) == 3

    def test_reiniciar_la_base_no_borra_el_modelo_de_carbon(self, tmp_path):
        ruta = str(tmp_path / "c.duckdb")
        conexion = DuckDBConnection(ruta)
        DuckDBModeloCarbonRepository(conexion).reemplazar(crear_paquete_carbon())
        conexion.cerrar()
        reiniciada = DuckDBConnection(ruta, reiniciar=True)
        assert DuckDBModeloCarbonRepository(reiniciada).obtener() is not None


# ------------------------------------------------------------------ casos de uso
@pytest.fixture
def paquete_en_memoria():
    return ModeloCarbonRepositoryEnMemoria(crear_paquete_carbon())


class TestResumen:
    def test_el_pico_es_el_mes_de_mayor_consumo_central(self, paquete_en_memoria):
        r = ObtenerResumenCarbonUseCase(paquete_en_memoria).ejecutar()
        assert r.pico.fecha == date(2027, 2, 1) and r.pico.carbon_gbtu_dia.p50 == 389.0
        assert r.pico.carbon_gbtu_dia.p10 == 329.0 and r.pico.carbon_gbtu_dia.p90 == 419.0
        assert r.pico.uso_techo_p50_pct == pytest.approx(389 / 400 * 100, abs=0.01)

    def test_el_horizonte_recorta_el_pico(self, paquete_en_memoria):
        r = ObtenerResumenCarbonUseCase(paquete_en_memoria).ejecutar(horizonte_meses=3)
        assert r.horizonte_meses == 3 and r.pico.fecha == date(2026, 12, 1)  # dic-2026: 370

    def test_el_horizonte_no_pasa_de_lo_que_proyecta_el_modelo(self, paquete_en_memoria):
        assert ObtenerResumenCarbonUseCase(paquete_en_memoria).ejecutar(horizonte_meses=9).horizonte_meses == 9

    def test_inventario_del_mes_pico_segun_los_dias(self, paquete_en_memoria):
        caso = ObtenerResumenCarbonUseCase(paquete_en_memoria)
        i15 = caso.ejecutar(dias_inventario=15).inventario_pico
        i60 = caso.ejecutar(dias_inventario=60).inventario_pico
        assert (i15.dias_inventario, i60.dias_inventario) == (15, 60)
        assert i60.kt_p50 == pytest.approx(i15.kt_p50 * 4, rel=1e-3) and i15.fecha == date(2027, 2, 1)

    def test_los_trimestres_incompletos_en_el_horizonte_se_marcan(self, paquete_en_memoria):
        t = {x.trimestre: x.dentro_del_horizonte for x in ObtenerResumenCarbonUseCase(paquete_en_memoria).ejecutar(horizonte_meses=6).trimestres}
        assert t == {"2026Q4": True, "2027Q1": True, "2027Q2": False}
        t = {x.trimestre: x.dentro_del_horizonte for x in ObtenerResumenCarbonUseCase(paquete_en_memoria).ejecutar(horizonte_meses=1).trimestres}
        assert t == {"2026Q4": False, "2027Q1": False, "2027Q2": False}

    def test_techo_record_y_ultimo_observado(self, paquete_en_memoria):
        r = ObtenerResumenCarbonUseCase(paquete_en_memoria).ejecutar()
        assert r.techo_gbtu_dia == 400.0 and r.maximo_historico.carbon_gbtu_dia == 310.0
        assert r.ultimo_observado.fecha == date(2026, 10, 1) and r.ultimo_observado.mes_completo is False

    def test_cuenta_los_criterios_de_validez(self, paquete_en_memoria):
        r = ObtenerResumenCarbonUseCase(paquete_en_memoria).ejecutar()
        assert (r.criterios_cumplidos, r.criterios_total) == (3, 4)


class TestSerie:
    def test_historia_por_ventana(self, paquete_en_memoria):
        caso = ObtenerSerieCarbonUseCase(paquete_en_memoria)
        assert len(caso.ejecutar(historia_meses=12).historico) == 12
        assert len(caso.ejecutar(historia_meses=0).historico) == 24  # todo lo que hay
        assert caso.ejecutar(historia_meses=12).historico[-1].fecha == date(2026, 10, 1)

    def test_proyeccion_limitada_al_horizonte_y_en_orden(self, paquete_en_memoria):
        serie = ObtenerSerieCarbonUseCase(paquete_en_memoria).ejecutar(horizonte_meses=3)
        assert [p.fecha for p in serie.proyeccion] == [date(2026, 10, 1), date(2026, 11, 1), date(2026, 12, 1)]
        assert serie.horizonte_meses == 3

    def test_incluye_referencias_del_grafico(self, paquete_en_memoria):
        serie = ObtenerSerieCarbonUseCase(paquete_en_memoria).ejecutar()
        assert serie.techo_gbtu_dia == 400.0 and serie.maximo_historico_gbtu_dia == 310.0
        assert serie.poder_calorifico_mbtu_t == 26.27


class TestInventarioYComparacion:
    def test_inventario_filtra_por_dias_y_horizonte(self, paquete_en_memoria):
        filas = ObtenerInventarioCarbonUseCase(paquete_en_memoria).ejecutar(dias_inventario=30, horizonte_meses=4)
        assert len(filas) == 4 and {f.dias_inventario for f in filas} == {30}
        assert [f.fecha.month for f in filas] == [10, 11, 12, 1]

    def test_comparacion_con_xm_respeta_el_horizonte(self, paquete_en_memoria):
        filas = ObtenerComparacionXmUseCase(paquete_en_memoria).ejecutar(horizonte_meses=2)
        assert len(filas) == 2 and filas[0].xm_estocastico_gbtu_dia == 465.0
        assert filas[0].xm_historicas_min_gbtu_dia == 231.0


class TestValidacion:
    def test_devuelve_errores_episodios_veredicto_y_supuestos(self, paquete_en_memoria):
        v = ObtenerValidacionCarbonUseCase(paquete_en_memoria).ejecutar()
        assert [e.horizonte_meses for e in v.errores_horizonte] == [1, 3, 6, 9]
        assert len(v.episodios) == 2 and (v.criterios_cumplidos, v.criterios_total) == (3, 4)
        assert v.veredicto[-1].cumple is False and len(v.supuestos) == 3


@pytest.mark.parametrize("caso", [
    ObtenerResumenCarbonUseCase, ObtenerSerieCarbonUseCase, ObtenerInventarioCarbonUseCase,
    ObtenerComparacionXmUseCase, ObtenerValidacionCarbonUseCase,
])
def test_sin_corrida_cargada_falla_con_un_error_de_dominio(caso):
    with pytest.raises(ModeloCarbonNoCargadoError, match="importar_modelo_carbon"):
        caso(ModeloCarbonRepositoryEnMemoria(None)).ejecutar()
