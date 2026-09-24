from datetime import date, datetime

import openpyxl
import pytest

from domain.entities.proyeccion_senda import ProyeccionSendaMensual
from infrastructure.ingesta.proyeccion_outputs import (
    ArchivoProyeccionInvalidoError,
    convertir_filas,
    leer_proyecciones,
)
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.duckdb_proyeccion_senda_repository import (
    DuckDBProyeccionSendaRepository,
)

ENCABEZADO = ("CodigoEmbalse", "Fecha", "P10", "P50", "Promedio", "P90")
ORIGEN = "Modelo de prueba"


def _fila(embalse="GUAVIO", fecha=datetime(2026, 10, 1), p10=0.5, p50=0.6, prom=0.6, p90=0.7):
    return (embalse, fecha, p10, p50, prom, p90)


class TestEntidad:
    def test_acepta_p10_menor_o_igual_p50_menor_o_igual_p90(self):
        ProyeccionSendaMensual("A", date(2026, 10, 1), 50.0, 50.0, 50.0, ORIGEN)

    @pytest.mark.parametrize("p10,p50,p90", [(60, 50, 70), (40, 80, 70)])
    def test_rechaza_valores_fuera_de_orden(self, p10, p50, p90):
        with pytest.raises(ValueError, match="P10 <= P50 <= P90"):
            ProyeccionSendaMensual("A", date(2026, 10, 1), p10, p50, p90, ORIGEN)


class TestConvertirFilas:
    def test_convierte_fracciones_a_puntos_porcentuales_y_toma_p10_p50_p90(self):
        [p] = convertir_filas([ENCABEZADO, _fila(p10=0.4, p50=0.55, prom=0.99, p90=0.7)], ORIGEN)
        assert (p.limite_inferior, p.valor_esperado, p.limite_superior) == (40.0, 55.0, 70.0)
        assert p.embalse_id == "GUAVIO" and p.mes == date(2026, 10, 1) and p.origen == ORIGEN

    def test_normaliza_la_fecha_al_primer_dia_del_mes(self):
        [p] = convertir_filas([ENCABEZADO, _fila(fecha=datetime(2026, 10, 17))], ORIGEN)
        assert p.mes == date(2026, 10, 1)

    def test_ignora_filas_vacias(self):
        filas = [ENCABEZADO, _fila(), (None,) * 6]
        assert len(convertir_filas(filas, ORIGEN)) == 1

    def test_acepta_bandas_sin_ancho(self):
        [p] = convertir_filas([ENCABEZADO, _fila(p10=0.5, p50=0.5, p90=0.5)], ORIGEN)
        assert p.limite_inferior == p.limite_superior == 50.0

    def test_exige_las_columnas(self):
        with pytest.raises(ArchivoProyeccionInvalidoError, match="Faltan columnas: P90"):
            convertir_filas([("CodigoEmbalse", "Fecha", "P10", "P50"), ("A", datetime(2026, 10, 1), 0.1, 0.2)], ORIGEN)

    def test_archivo_vacio_o_sin_datos(self):
        with pytest.raises(ArchivoProyeccionInvalidoError, match="vacio"):
            convertir_filas([], ORIGEN)
        with pytest.raises(ArchivoProyeccionInvalidoError, match="no tiene filas"):
            convertir_filas([ENCABEZADO], ORIGEN)

    def test_rechaza_porcentajes_ya_multiplicados_por_100(self):
        with pytest.raises(ArchivoProyeccionInvalidoError, match="fraccion"):
            convertir_filas([ENCABEZADO, _fila(p10=50, p50=60, p90=70)], ORIGEN)

    def test_rechaza_valores_no_numericos_y_fechas_invalidas(self):
        with pytest.raises(ArchivoProyeccionInvalidoError, match="P50 no es numerico"):
            convertir_filas([ENCABEZADO, _fila(p50="n/d")], ORIGEN)
        with pytest.raises(ArchivoProyeccionInvalidoError, match="Fecha no valida"):
            convertir_filas([ENCABEZADO, _fila(fecha="octubre")], ORIGEN)

    def test_rechaza_meses_repetidos_para_el_mismo_embalse(self):
        with pytest.raises(ArchivoProyeccionInvalidoError, match="repetido"):
            convertir_filas([ENCABEZADO, _fila(), _fila()], ORIGEN)

    def test_rechaza_bandas_desordenadas(self):
        with pytest.raises(ValueError, match="P10 <= P50 <= P90"):
            convertir_filas([ENCABEZADO, _fila(p10=0.8, p50=0.6, p90=0.7)], ORIGEN)


def test_lee_un_archivo_xlsx_real(tmp_path):
    ruta = tmp_path / "proyeccion.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(ENCABEZADO)
    hoja.append(_fila("TOTAL", datetime(2026, 10, 1), 0.7, 0.72, 0.72, 0.75))
    hoja.append(_fila("TOTAL", datetime(2026, 11, 1), 0.6, 0.65, 0.65, 0.7))
    libro.save(ruta)

    proyecciones = leer_proyecciones(ruta, ORIGEN)

    assert [(p.embalse_id, p.mes.month, p.valor_esperado) for p in proyecciones] == [
        ("TOTAL", 10, 72.0),
        ("TOTAL", 11, 65.0),
    ]


class TestRepositorioDuckDB:
    @pytest.fixture
    def repo(self, tmp_path):
        return DuckDBProyeccionSendaRepository(DuckDBConnection(str(tmp_path / "p.duckdb")))

    def _puntos(self, embalse, valores):
        return [
            ProyeccionSendaMensual(embalse, date(2026, 10 + i, 1), v - 5, v, v + 5, ORIGEN)
            for i, v in enumerate(valores)
        ]

    def test_guarda_y_devuelve_ordenado_por_mes(self, repo):
        repo.reemplazar_todas(list(reversed(self._puntos("A", [50.0, 40.0, 30.0]))))
        obtenidas = repo.obtener("A")
        assert [p.valor_esperado for p in obtenidas] == [50.0, 40.0, 30.0]
        assert obtenidas[0] == ProyeccionSendaMensual("A", date(2026, 10, 1), 45.0, 50.0, 55.0, ORIGEN)

    def test_solo_devuelve_el_embalse_pedido_y_vacio_si_no_hay(self, repo):
        repo.reemplazar_todas(self._puntos("A", [50.0]) + self._puntos("B", [60.0]))
        assert [p.embalse_id for p in repo.obtener("B")] == ["B"]
        assert repo.obtener("Z") == []

    def test_reemplazar_sustituye_la_corrida_anterior(self, repo):
        repo.reemplazar_todas(self._puntos("A", [50.0, 40.0]) + self._puntos("B", [60.0]))
        repo.reemplazar_todas(self._puntos("A", [10.0]))
        assert [p.valor_esperado for p in repo.obtener("A")] == [10.0]
        assert repo.obtener("B") == []

    def test_reiniciar_la_base_no_borra_la_proyeccion_publicada(self, tmp_path):
        ruta = str(tmp_path / "p.duckdb")
        conexion = DuckDBConnection(ruta)
        DuckDBProyeccionSendaRepository(conexion).reemplazar_todas(self._puntos("A", [50.0]))
        conexion.cerrar()
        reiniciada = DuckDBConnection(ruta, reiniciar=True)
        assert len(DuckDBProyeccionSendaRepository(reiniciada).obtener("A")) == 1
