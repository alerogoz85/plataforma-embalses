"""CSV de la tanda de escenarios del visor de apagon: ida y vuelta y rechazos."""
import pytest

from domain.entities.escenario_apagon import EscenarioApagon, clave_escenario
from infrastructure.ingesta.resultados_modelos.comun import SalidaModeloInvalidaError
from infrastructure.ingesta.resultados_modelos.escenarios_apagon import combinaciones
from infrastructure.ingesta.resultados_modelos.escenarios_csv import ENCABEZADO, a_csv, desde_csv
from tests.test_escenarios_apagon import FUENTE, escenario


def tanda_completa() -> list[EscenarioApagon]:
    out = []
    for modo, oni, sims, hor in combinaciones():
        base = escenario(modo, oni if oni is not None else 1.0, sims, hor)
        out.append(base)
    return out


@pytest.fixture(scope="module")
def csv_completo() -> str:
    return a_csv(tanda_completa(), FUENTE)


class TestCsvDeEscenarios:
    def test_ida_y_vuelta_exacta_de_las_468_combinaciones(self, csv_completo):
        escenarios, fuente = desde_csv(csv_completo)
        assert len(escenarios) == 468 and {e.clave for e in escenarios} == {clave_escenario(*c) for c in combinaciones()}
        original = {e.clave: e for e in tanda_completa()}
        assert all(e.meses == original[e.clave].meses for e in escenarios)
        assert (fuente.ultimo_oni_observado, fuente.ultimo_mes_demanda, fuente.semilla) == (1.8, "2026-08-01", 7)

    def test_el_tamano_cabe_en_el_limite_de_vercel(self, csv_completo):
        assert len(csv_completo.encode()) < 4 * 1024 * 1024

    def test_faltan_columnas(self, csv_completo):
        with pytest.raises(SalidaModeloInvalidaError, match="faltan columnas"):
            desde_csv(csv_completo.replace("semaforo", "color", 1))

    def test_tanda_incompleta(self, csv_completo):
        lineas = csv_completo.splitlines()
        sin_24 = [lineas[0]] + [l for l in lineas[1:] if l.split(",")[3] != "24"]  # quita todos los escenarios de 24 meses
        with pytest.raises(SalidaModeloInvalidaError, match="468 combinaciones"):
            desde_csv("\n".join(sin_24) + "\n")

    def test_filas_duplicadas(self, csv_completo):
        lineas = csv_completo.splitlines()
        with pytest.raises(SalidaModeloInvalidaError):
            desde_csv("\n".join(lineas + [lineas[1]]) + "\n")

    @pytest.mark.parametrize("columna,valor", [("indice_riesgo", "abc"), ("indice_riesgo", "nan"), ("probabilidad_deficit", "1.5"), ("semaforo", "AZUL"), ("mes", "2026/10")])
    def test_valores_invalidos_se_explican(self, csv_completo, columna, valor):
        lineas = csv_completo.splitlines()
        cab = lineas[0].split(",")
        celdas = lineas[1].split(",")
        celdas[cab.index(columna)] = valor
        with pytest.raises(SalidaModeloInvalidaError):
            desde_csv("\n".join([lineas[0], ",".join(celdas)] + lineas[2:]) + "\n")

    def test_procedencia_inconsistente(self, csv_completo):
        lineas = csv_completo.splitlines()
        celdas = lineas[1].split(",")
        celdas[-1] = "999"
        with pytest.raises(SalidaModeloInvalidaError, match="procedencia"):
            desde_csv("\n".join([lineas[0], ",".join(celdas)] + lineas[2:]) + "\n")

    def test_archivo_vacio_o_solo_encabezado(self):
        with pytest.raises(SalidaModeloInvalidaError):
            desde_csv(",".join(ENCABEZADO) + "\n")
