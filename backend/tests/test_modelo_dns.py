"""Modelo DNS: entidades, calculos, casos de uso, lectura de archivos y repositorio DuckDB."""
import csv
from dataclasses import replace
from datetime import datetime
from pathlib import Path

import pytest

from application.use_cases.modelo_dns import (
    ObtenerCambiosReporteDnsUseCase,
    ObtenerCatalogoDnsUseCase,
    ObtenerCausasDnsUseCase,
    ObtenerModeloDnsUseCase,
    ObtenerPatronesDnsUseCase,
    ObtenerResumenDnsUseCase,
    ObtenerSerieDnsUseCase,
    ObtenerZonasDnsUseCase,
)
from domain.entities.modelo_dns import CambioReporte, EventoDns, PronosticoSubarea
from domain.exceptions import FiltroInvalidoError, ModeloDnsNoCargadoError
from domain.services import analisis_dns as a
from domain.value_objects.filtro_dns import FiltroDns
from infrastructure.ingesta.modelo_dns_archivos import ArchivoModeloDnsInvalidoError, leer_modelo_dns
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_modelo_dns_repository import DuckDBModeloDnsRepository
from tests.fakes import ModeloDnsRepositoryEnMemoria, crear_paquete_dns


@pytest.fixture
def repo():
    return ModeloDnsRepositoryEnMemoria(crear_paquete_dns())


# ------------------------------------------------------------------ entidades
class TestEntidades:
    def test_critico_desde_100_mil_kwh(self):
        base = crear_paquete_dns().eventos[0]
        assert replace(base, energia_no_atendida_kwh=100_000).es_critico
        assert not replace(base, energia_no_atendida_kwh=99_999.9).es_critico

    def test_hora_desconocida_es_las_00_00_00_exactas(self):
        base = crear_paquete_dns().eventos[0]
        assert replace(base, fecha_hora=datetime(2026, 1, 1, 0, 0, 0)).hora_desconocida
        assert not replace(base, fecha_hora=datetime(2026, 1, 1, 0, 0, 1)).hora_desconocida
        assert not replace(base, fecha_hora=datetime(2026, 1, 1, 0, 1, 0)).hora_desconocida

    def test_corte_e_inicio_salen_de_los_eventos(self):
        p = crear_paquete_dns()
        assert p.fecha_corte == datetime(2026, 8, 11, 12) and p.fecha_inicio == datetime(2013, 1, 2, 6)

    def test_exige_eventos_y_subareas(self):
        p = crear_paquete_dns()
        with pytest.raises(ValueError, match="no trae eventos"):
            replace(p, eventos=[])
        with pytest.raises(ValueError, match="no trae subareas"):
            replace(p, subareas=[])

    def test_rechaza_subareas_repetidas_y_referencias_a_subareas_inexistentes(self):
        p = crear_paquete_dns()
        with pytest.raises(ValueError, match="repetido"):
            replace(p, subareas=p.subareas + [p.subareas[0]])
        with pytest.raises(ValueError, match="pronostico con subareas que no existen: Are9999"):
            replace(p, pronostico=p.pronostico + [PronosticoSubarea("Are9999", 1, 1)])
        evento_raro = EventoDns(datetime(2026, 1, 1, 1), "Are9999", "DNS", 1.0, "programada", "x", "x", "x", "x")
        with pytest.raises(ValueError, match="eventos con subareas que no existen"):
            replace(p, eventos=p.eventos + [evento_raro])

    def test_rechaza_energia_negativa_tipo_desconocido_y_duplicados(self):
        p = crear_paquete_dns()
        with pytest.raises(ValueError, match="negativa"):
            replace(p, eventos=[replace(p.eventos[0], energia_no_atendida_kwh=-1)])
        with pytest.raises(ValueError, match="tipo de evento"):
            replace(p, eventos=[replace(p.eventos[0], tipo="XYZ")])
        with pytest.raises(ValueError, match="ranking repetido"):
            replace(p, zonas=[p.zonas[0], p.zonas[0]])
        c = CambioReporte("Are0002", "2025-01", "SUBIDA", 0, 1, 2, 3)
        with pytest.raises(ValueError, match="cambios de reporte repetidos"):
            replace(p, cambios_reporte=[c, c])


class TestFiltro:
    def test_solo_acepta_las_listas_cerradas(self):
        for periodo in (12, 36, 60, 0):
            FiltroDns(periodo_meses=periodo)
        with pytest.raises(ValueError):
            FiltroDns(periodo_meses=7)
        with pytest.raises(ValueError):
            FiltroDns(origen="otro")


# ------------------------------------------------------------------ calculos
class TestVentanaYSeleccion:
    def test_la_ventana_termina_en_el_mes_del_corte(self):
        v = a.ventana_del_periodo(crear_paquete_dns(), 12)
        assert v.meses[0] == "2025-09" and v.meses[-1] == "2026-08" and len(v.meses) == 12

    def test_todo_el_historico_empieza_en_el_primer_evento(self):
        v = a.ventana_del_periodo(crear_paquete_dns(), 0)
        assert v.meses[0] == "2013-01" and len(v.meses) == 164

    def test_un_periodo_mayor_que_la_historia_no_pasa_del_primer_evento(self):
        p = crear_paquete_dns()
        p2 = replace(p, eventos=[e for e in p.eventos if e.fecha_hora.year >= 2026])
        assert a.ventana_del_periodo(p2, 60).meses[0] == "2026-07"

    def test_la_ventana_anterior_tiene_la_misma_duracion(self):
        v = a.ventana_del_periodo(crear_paquete_dns(), 12).anterior()
        assert v.meses[0] == "2024-09" and v.meses[-1] == "2025-08"

    def test_solo_eventos_dns_con_energia_no_negativa_y_dentro_de_la_ventana(self):
        sel = a.seleccionar(crear_paquete_dns(), FiltroDns(periodo_meses=12))
        assert len(sel) == 5 and all(e.tipo == "DNS" for e in sel)

    def test_la_region_se_traduce_a_sus_subareas_y_la_subarea_manda(self):
        p = crear_paquete_dns()
        assert len(a.seleccionar(p, FiltroDns(periodo_meses=12, region="Norte"))) == 4
        assert len(a.seleccionar(p, FiltroDns(periodo_meses=12, region="Norte", subarea="Are0003"))) == 1

    def test_el_origen_filtra_los_eventos(self):
        p = crear_paquete_dns()
        assert len(a.seleccionar(p, FiltroDns(periodo_meses=12, origen="programada"))) == 2
        assert len(a.seleccionar(p, FiltroDns(periodo_meses=12, origen="no_programada"))) == 3

    def test_edac_se_selecciona_aparte(self):
        sel = a.seleccionar(crear_paquete_dns(), FiltroDns(periodo_meses=0), tipo="EDAC", con_origen=False)
        assert len(sel) == 2

    def test_variacion_sin_base_es_none(self):
        assert a.variacion_pct(5, 0) is None and a.variacion_pct(5, 2) == 150.0


class TestSerieYPatrones:
    def test_serie_mensual_rellena_meses_sin_eventos_y_marca_el_mes_parcial(self):
        meses = a.serie_mensual(crear_paquete_dns(), FiltroDns(periodo_meses=12))
        assert [m.mes for m in meses][0] == "2025-09" and len(meses) == 12
        agosto, julio, junio = meses[-1], meses[-2], meses[-3]
        assert (agosto.eventos, agosto.energia_kwh, agosto.parcial) == (3, 200_000, True)
        assert (julio.eventos, julio.energia_kwh, julio.parcial) == (2, 220_000, False)
        assert (junio.eventos, junio.energia_kwh) == (0, 0)
        assert agosto.eventos_no_programados == 2

    def test_si_el_corte_es_fin_de_mes_no_es_parcial(self):
        p = crear_paquete_dns()
        p2 = replace(p, eventos=p.eventos + [EventoDns(datetime(2026, 8, 31, 5), "Are0001", "DNS", 1.0, "programada", "x", "x", "x", "x")])
        assert not a.serie_mensual(p2, FiltroDns(periodo_meses=12))[-1].parcial

    def test_patrones_excluyen_la_hora_desconocida(self):
        pat = a.patrones(crear_paquete_dns(), FiltroDns(periodo_meses=0))
        assert pat.eventos_usados == 7 and pat.eventos_hora_desconocida == 1
        esperado = [0] * 24
        for h in (6, 7, 9, 10, 12, 19, 22):
            esperado[h] = 1
        assert pat.por_hora == esperado
        assert pat.por_dia_semana == [2, 1, 1, 0, 2, 0, 1]
        assert pat.origen_por_franja["Mañana (6-11h)"] == (3, 1)
        assert pat.origen_por_franja["Madrugada (0-5h)"] == (0, 0)
        assert pat.origen_por_franja["Noche (18-23h)"] == (1, 1)

    @pytest.mark.parametrize("hora,franja", [(0, 0), (5, 0), (6, 1), (11, 1), (12, 2), (17, 2), (18, 3), (23, 3)])
    def test_limites_de_las_franjas(self, hora, franja):
        assert a.franja_horaria(hora) == a.FRANJAS[franja]

    def test_causas_ordenadas_por_energia(self):
        c = a.causas(crear_paquete_dns(), FiltroDns(periodo_meses=12))
        assert c.total == 5 and c.por_causa[0] == ("mantenimiento", 2, 320_000)
        assert dict((n, e) for n, e, _ in c.por_causa) == {"mantenimiento": 2, "fallas": 1, "atmosferica": 1, "desconocido": 1}
        assert dict(c.por_origen_de_la_causa)["sin clasificar"] == 1

    def test_causa_mas_frecuente_ignora_desconocido(self):
        eventos = a.seleccionar(crear_paquete_dns(), FiltroDns(periodo_meses=12))
        assert a.causa_mas_frecuente_conocida(eventos) == ("mantenimiento", 2)
        solo_desconocidas = [e for e in eventos if e.causa_definitiva == "desconocido"]
        assert a.causa_mas_frecuente_conocida(solo_desconocidas) is None


# ------------------------------------------------------------------ casos de uso
class TestCasosDeUso:
    def test_sin_corrida_cargada_se_pide_importarla(self):
        vacio = ModeloDnsRepositoryEnMemoria(None)
        for caso, args in (
            (ObtenerCatalogoDnsUseCase, ()), (ObtenerResumenDnsUseCase, (12, None, None, None)),
            (ObtenerSerieDnsUseCase, (12, None, None, None)), (ObtenerZonasDnsUseCase, (None, None)),
            (ObtenerPatronesDnsUseCase, (12, None, None, None)), (ObtenerCausasDnsUseCase, (12, None, None, None)),
            (ObtenerCambiosReporteDnsUseCase, (None, None)), (ObtenerModeloDnsUseCase, (None, None)),
        ):
            with pytest.raises(ModeloDnsNoCargadoError, match="importar_modelo_dns"):
                caso(vacio).ejecutar(*args)

    def test_catalogo(self, repo):
        c = ObtenerCatalogoDnsUseCase(repo).ejecutar()
        assert c.regiones == ["Norte", "Sur", "Sin asignar"]  # «Sin asignar» siempre al final
        assert [s.codigo for s in c.subareas] == ["Are0004", "Are0002", "Are0003", "Are0001"]  # por nombre
        assert str(c.fecha_inicio) == "2013-01-02" and str(c.fecha_corte) == "2026-08-11"
        assert c.mes_corte_parcial and c.periodo_pronostico == "2026-08"

    def test_resumen_de_12_meses(self, repo):
        r = ObtenerResumenDnsUseCase(repo).ejecutar(12, None, None, None)
        assert (r.desde, r.hasta) == ("2025-09", "2026-08")
        assert r.eventos == 5 and r.energia_gwh == pytest.approx(0.42)
        assert r.pct_criticos == pytest.approx(40.0) and r.pct_no_programados == pytest.approx(60.0)
        assert r.variacion_eventos_pct == pytest.approx(150.0) and r.variacion_energia_pct == pytest.approx(740.0)
        assert (r.causa_mas_frecuente, r.causa_mas_frecuente_eventos) == ("mantenimiento", 2)
        assert r.eventos_edac == 1

    def test_resumen_de_todo_el_historico_no_compara(self, repo):
        r = ObtenerResumenDnsUseCase(repo).ejecutar(0, None, None, None)
        assert r.eventos == 8 and r.variacion_eventos_pct is None and r.variacion_energia_pct is None
        assert r.eventos_edac == 2

    def test_sin_base_de_comparacion_no_hay_variacion(self, repo):
        # 60 meses: el periodo previo (2016-09..2021-08) no tiene eventos DNS -> no hay con que comparar
        r = ObtenerResumenDnsUseCase(repo).ejecutar(60, None, None, None)
        assert r.eventos == 7 and r.variacion_eventos_pct is None and r.variacion_energia_pct is None  # + 2 de 2025

    def test_si_el_periodo_previo_empieza_antes_de_los_datos_no_se_compara(self):
        p = crear_paquete_dns()
        reciente = ModeloDnsRepositoryEnMemoria(replace(p, eventos=[e for e in p.eventos if e.fecha_hora.year == 2026]))
        r = ObtenerResumenDnsUseCase(reciente).ejecutar(12, None, None, None)
        assert r.eventos == 5 and r.variacion_eventos_pct is None

    def test_resumen_por_region_subarea_y_origen(self, repo):
        caso = ObtenerResumenDnsUseCase(repo)
        assert caso.ejecutar(12, "Norte", None, None).eventos == 4
        assert caso.ejecutar(12, "Norte", "Are0003", None).eventos == 1
        r = caso.ejecutar(12, None, None, "programada")
        assert r.eventos == 2 and r.pct_no_programados == 0.0

    def test_resumen_sin_eventos_no_divide_por_cero(self, repo):
        r = ObtenerResumenDnsUseCase(repo).ejecutar(12, "Sin asignar", None, None)
        assert r.eventos == 0 and r.pct_criticos == 0.0 and r.pct_no_programados is None
        assert r.causa_mas_frecuente is None and r.eventos_edac == 1

    def test_region_o_subarea_inexistente(self, repo):
        with pytest.raises(FiltroInvalidoError, match="'Marte'"):
            ObtenerResumenDnsUseCase(repo).ejecutar(12, "Marte", None, None)
        with pytest.raises(FiltroInvalidoError, match="'Are9'"):
            ObtenerPatronesDnsUseCase(repo).ejecutar(12, None, "Are9", None)

    def test_serie_con_pronostico_del_ambito(self, repo):
        s = ObtenerSerieDnsUseCase(repo).ejecutar(12, "Norte", None, None)
        assert len(s.meses) == 12 and s.pronostico.mes == "2026-08"
        assert (s.pronostico.eventos, s.pronostico.energia_gwh, s.pronostico.subareas) == (15.0, pytest.approx(0.75), 2)
        assert s.nota_pronostico is None

    def test_serie_total_suma_el_pronostico_de_todas_las_subareas(self, repo):
        s = ObtenerSerieDnsUseCase(repo).ejecutar(12, None, None, None)
        assert s.pronostico.eventos == 17.0 and s.pronostico.subareas == 3

    def test_con_filtro_de_origen_no_hay_pronostico_y_se_explica(self, repo):
        s = ObtenerSerieDnsUseCase(repo).ejecutar(12, None, None, "programada")
        assert s.pronostico is None and "origen" in s.nota_pronostico

    def test_ambito_sin_pronostico_se_explica(self, repo):
        s = ObtenerSerieDnsUseCase(repo).ejecutar(12, "Sin asignar", None, None)
        assert s.pronostico is None and "no pronostica" in s.nota_pronostico

    def test_zonas_ordenadas_y_filtradas_por_ambito(self, repo):
        caso = ObtenerZonasDnsUseCase(repo)
        todas = caso.ejecutar(None, None).zonas
        assert [z.ranking for z in todas] == [1, 2, 3] and todas[0].nombre == "SubArea Uno"
        assert todas[0].energia_total_gwh == pytest.approx(50.0) and todas[0].pct_criticos == pytest.approx(20.0)
        assert [z.codigo for z in caso.ejecutar("Norte", None).zonas] == ["Are0001", "Are0002"]
        assert [z.codigo for z in caso.ejecutar(None, "Are0003").zonas] == ["Are0003"]

    def test_patrones_en_dto(self, repo):
        p = ObtenerPatronesDnsUseCase(repo).ejecutar(0, None, None, None)
        assert p.dias[0] == "Lunes" and len(p.por_hora) == 24 and p.eventos_hora_desconocida == 1
        manana = next(f for f in p.franjas if f.franja.startswith("Mañana"))
        assert manana.pct_no_programada == pytest.approx(75.0)
        madrugada = next(f for f in p.franjas if f.franja.startswith("Madrugada"))
        assert madrugada.pct_no_programada is None

    def test_causas_en_dto(self, repo):
        c = ObtenerCausasDnsUseCase(repo).ejecutar(12, None, None, None)
        assert c.causas[0].causa == "mantenimiento" and c.causas[0].energia_gwh == pytest.approx(0.32)
        assert c.causas[0].pct_eventos == pytest.approx(40.0)
        assert sum(x.eventos for x in c.origen_de_la_causa) == 5

    def test_causas_sin_eventos(self, repo):
        c = ObtenerCausasDnsUseCase(repo).ejecutar(12, "Sin asignar", None, None)
        assert c.total == 0 and c.causas == []

    def test_cambios_de_reporte_con_nombre_y_region(self, repo):
        caso = ObtenerCambiosReporteDnsUseCase(repo)
        c = caso.ejecutar(None, None).cambios[0]
        assert (c.nombre, c.region, c.periodo_quiebre) == ("SubArea Dos", "Norte", "2025-01")
        assert caso.ejecutar("Sur", None).cambios == []

    def test_modelo_mejora_frente_a_persistencia(self, repo):
        m = ObtenerModeloDnsUseCase(repo).ejecutar(None, None)
        gb = next(x for x in m.metricas if x.modelo == "GradientBoosting")
        assert gb.variable == "n_eventos" and gb.mejora_vs_persistencia_pct == pytest.approx(25.0)
        rf = next(x for x in m.metricas if x.variable == "energia_kwh" and x.modelo.startswith("RandomForest"))
        assert rf.mejora_vs_persistencia_pct == pytest.approx(25.0)
        base = next(x for x in m.metricas if x.modelo == "persistencia")
        assert base.mejora_vs_persistencia_pct is None

    def test_modelo_limita_la_importancia_a_10_y_ordena_el_pronostico_por_energia(self, repo):
        m = ObtenerModeloDnsUseCase(repo).ejecutar(None, None)
        assert len(m.importancia) == 10 and m.importancia[0].variable == "variable_00"
        assert [p.codigo for p in m.pronostico] == ["Are0001", "Are0002", "Are0003"]
        assert [p.codigo for p in ObtenerModeloDnsUseCase(repo).ejecutar("Sur", None).pronostico] == ["Are0003"]


# ------------------------------------------------------------------ archivos del modelo
def _csv(ruta: Path, columnas: list[str], filas: list[list]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        w.writerows(filas)


def escribir_modelo_dns(carpeta: Path, sin_archivo: str | None = None, pronostico: str = "2026-08", cambio=None) -> Path:
    d = carpeta / "Datos"
    archivos = {
        "mapeo": (d / "outputs_datos" / "mapeo_subareas.csv", ["codigo_subarea", "nombre_subarea", "region", "departamentos"],
                  [["Are0001", "SubArea Uno", "Norte", "Antioquia"], ["Are0002", "SubArea Dos", "", ""]]),
        "eventos": (d / "outputs" / "03_causas" / "eventos_enriquecidos.csv",
                    ["codigo_subarea", "fecha_hora", "tipo", "energia_no_atendida_kwh", "origen_evento", "causa_definitiva",
                     "origen_causa_definitiva", "tipo_evento", "nivel_red"],
                    [["Are0001", "2026-08-02 10:30:00", "DNS", "50000.0", "no_programada", "fallas", "reportada", "Disparo", "STR"],
                     ["Are0002", "2026-07-20 19:00:00", "DNS", "200000", "programada", "mantenimiento", "reportada", "Trabajos", "STR"],
                     ["Are0099", "2020-01-01 05:00:00", "EDAC", "150.02", "", "desconocido", "sin clasificar", "Disparo", "STN"]]),
        "zonas": (d / "outputs" / "04_zonas" / "indice_priorizacion_zonas.csv",
                  ["ranking", "codigo_subarea", "indice_priorizacion", "energia_total_kwh", "n_eventos", "pct_criticos", "variacion_pct"],
                  [[1, "Are0001", 80.5, 5.0e7, 400, 0.2, 10.0], [2, "Are0002", 60.0, 2.0e7, 200, 0.1, -5.0]]),
        "cambios": (d / "outputs" / "05_cambios_reporte" / "cambios_reporte_confirmados.csv",
                    ["codigo_subarea", "periodo_quiebre", "direccion", "pct_descripcion_generica_antes", "pct_descripcion_generica_despues",
                     "pct_causa_conocida_antes", "pct_causa_conocida_despues"],
                    [cambio or ["Are0002", "2025-01", "SUBIDA", 0.0, 80.0, 50.0, 5.0]]),
        "metricas": (d / "outputs" / "07_modelo" / "metricas_evaluacion.csv", ["modelo", "MAE", "RMSE"],
                     [["n_eventos - persistencia", 6.0, 12.0], ["n_eventos - GradientBoosting", 4.5, 10.0]]),
        "importancia": (d / "outputs" / "07_modelo" / "importancia_variables.csv",
                        ["variable", "importancia_n_eventos", "importancia_energia_kwh"], [["n_eventos", 0.5, 0.02]]),
        "pronostico": (d / "outputs" / "07_modelo" / f"pronostico_{pronostico}.csv",
                       ["codigo_subarea", "pronostico_n_eventos", "pronostico_energia_kwh"], [["Are0001", 10.0, 500000.0]]),
    }
    for nombre, (ruta, columnas, filas) in archivos.items():
        if nombre != sin_archivo:
            _csv(ruta, columnas, filas)
    return carpeta


class TestLecturaDeArchivos:
    def test_lee_una_corrida_completa(self, tmp_path):
        p = leer_modelo_dns(escribir_modelo_dns(tmp_path))
        assert len(p.eventos) == 3 and len(p.zonas) == 2 and p.periodo_pronostico == "2026-08"
        assert p.eventos[0].fecha_hora == datetime(2026, 8, 2, 10, 30) and p.eventos[2].origen_evento is None
        assert "2020-01-01 a 2026-08-02" in p.origen and "pronóstico 2026-08" in p.origen

    def test_region_vacia_pasa_a_sin_asignar_y_los_codigos_sin_mapeo_se_agregan(self, tmp_path):
        p = leer_modelo_dns(escribir_modelo_dns(tmp_path))
        assert p.subarea("Are0002").region == "Sin asignar" and p.subarea("Are0002").departamentos is None
        extra = p.subarea("Are0099")
        assert extra.nombre == "Are0099" and extra.region == "Sin asignar"

    def test_usa_el_pronostico_mas_reciente(self, tmp_path):
        escribir_modelo_dns(tmp_path, pronostico="2026-08")
        _csv(tmp_path / "Datos" / "outputs" / "07_modelo" / "pronostico_2026-09.csv",
             ["codigo_subarea", "pronostico_n_eventos", "pronostico_energia_kwh"], [["Are0002", 1.0, 2.0]])
        p = leer_modelo_dns(tmp_path)
        assert p.periodo_pronostico == "2026-09" and p.pronostico[0].codigo_subarea == "Are0002"

    @pytest.mark.parametrize("falta", ["mapeo", "eventos", "zonas", "cambios", "metricas", "importancia", "pronostico"])
    def test_falta_un_archivo(self, tmp_path, falta):
        escribir_modelo_dns(tmp_path, sin_archivo=falta)
        with pytest.raises(ArchivoModeloDnsInvalidoError):
            leer_modelo_dns(tmp_path)

    def test_falta_una_columna(self, tmp_path):
        escribir_modelo_dns(tmp_path)
        _csv(tmp_path / "Datos" / "outputs" / "07_modelo" / "metricas_evaluacion.csv", ["modelo", "MAE"], [["x", 1]])
        with pytest.raises(ArchivoModeloDnsInvalidoError, match="faltan columnas"):
            leer_modelo_dns(tmp_path)

    def test_valores_invalidos(self, tmp_path):
        escribir_modelo_dns(tmp_path, cambio=["Are0002", "2025-01", "SUBIDA", "abc", 80.0, 50.0, 5.0])
        with pytest.raises(ArchivoModeloDnsInvalidoError, match="no es un numero"):
            leer_modelo_dns(tmp_path)

    def test_una_zona_de_una_subarea_desconocida_invalida_toda_la_corrida(self, tmp_path):
        escribir_modelo_dns(tmp_path)
        _csv(tmp_path / "Datos" / "outputs" / "04_zonas" / "indice_priorizacion_zonas.csv",
             ["ranking", "codigo_subarea", "indice_priorizacion", "energia_total_kwh", "n_eventos", "pct_criticos", "variacion_pct"],
             [[1, "Are7777", 1, 1, 1, 0.1, 0]])
        with pytest.raises(ArchivoModeloDnsInvalidoError, match="Are7777"):
            leer_modelo_dns(tmp_path)

    def test_fecha_invalida(self, tmp_path):
        escribir_modelo_dns(tmp_path)
        _csv(tmp_path / "Datos" / "outputs" / "03_causas" / "eventos_enriquecidos.csv",
             ["codigo_subarea", "fecha_hora", "tipo", "energia_no_atendida_kwh", "origen_evento", "causa_definitiva",
              "origen_causa_definitiva", "tipo_evento", "nivel_red"],
             [["Are0001", "ayer", "DNS", "1", "programada", "x", "x", "x", "x"]])
        with pytest.raises(ArchivoModeloDnsInvalidoError, match="fecha invalida"):
            leer_modelo_dns(tmp_path)


# ------------------------------------------------------------------ repositorio DuckDB
@pytest.fixture
def repo_duckdb(tmp_path):
    return DuckDBModeloDnsRepository(DuckDBConnection(str(tmp_path / "dns.duckdb")))


class TestRepositorioDuckDB:
    def test_sin_corrida_devuelve_none(self, repo_duckdb):
        assert repo_duckdb.obtener() is None

    def test_ida_y_vuelta(self, repo_duckdb):
        original = crear_paquete_dns()
        repo_duckdb.reemplazar(original)
        leido = repo_duckdb.obtener()
        assert leido.origen == original.origen and leido.periodo_pronostico == original.periodo_pronostico
        assert sorted(leido.eventos, key=lambda e: (e.fecha_hora, e.codigo_subarea)) == sorted(
            original.eventos, key=lambda e: (e.fecha_hora, e.codigo_subarea))
        assert leido.subareas == sorted(original.subareas, key=lambda s: s.codigo)
        assert leido.zonas == original.zonas and leido.cambios_reporte == original.cambios_reporte
        assert leido.metricas == original.metricas and leido.importancia == original.importancia
        assert leido.pronostico == original.pronostico

    def test_los_resultados_de_los_calculos_son_iguales_con_la_base(self, repo_duckdb):
        repo_duckdb.reemplazar(crear_paquete_dns())
        r = ObtenerResumenDnsUseCase(repo_duckdb).ejecutar(12, None, None, None)
        assert r.eventos == 5 and r.energia_gwh == pytest.approx(0.42)

    def test_una_corrida_nueva_reemplaza_a_la_anterior(self, repo_duckdb):
        repo_duckdb.reemplazar(crear_paquete_dns())
        nueva = replace(crear_paquete_dns(), origen="Otra", eventos=crear_paquete_dns().eventos[:2], zonas=[], pronostico=[])
        repo_duckdb.reemplazar(nueva)
        leido = repo_duckdb.obtener()
        assert leido.origen == "Otra" and len(leido.eventos) == 2 and leido.zonas == [] and leido.pronostico == []

    def test_si_falla_a_mitad_queda_la_corrida_anterior(self, repo_duckdb):
        repo_duckdb.reemplazar(crear_paquete_dns())
        mala = crear_paquete_dns()
        eventos = [replace(e, nivel_red=None) if i == 3 else e for i, e in enumerate(mala.eventos)]
        with pytest.raises(Exception):  # NOT NULL violado despues de haber borrado y escrito otras tablas
            repo_duckdb.reemplazar(replace(mala, origen="Mala", eventos=eventos))
        leido = repo_duckdb.obtener()
        assert leido.origen == "Modelo DNS de prueba" and len(leido.eventos) == 10

    def test_reiniciar_la_base_no_borra_el_modelo_dns(self, tmp_path):
        ruta = str(tmp_path / "d.duckdb")
        conexion = DuckDBConnection(ruta)
        DuckDBModeloDnsRepository(conexion).reemplazar(crear_paquete_dns())
        conexion.cerrar()
        reiniciada = DuckDBConnection(ruta, reiniciar=True)
        assert DuckDBModeloDnsRepository(reiniciada).obtener() is not None
