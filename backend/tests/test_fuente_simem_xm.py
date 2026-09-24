from datetime import date

import pytest
import requests

from domain.exceptions import FuenteDatosError
from infrastructure.fuentes.clientes_http import DIAS_POR_CONSULTA_XM, ClienteXm
from infrastructure.fuentes.simem_xm_fuente import (
    SimemXmFuenteMediciones,
    ensamblar,
    indexar_aportes,
    indexar_descargas,
    indexar_energia,
    normalizar_codigo,
)

D1 = date(2026, 9, 1)
D2 = date(2026, 9, 2)
D3 = date(2026, 9, 3)


def _volumen(codigo="GUAVIO", fecha="2026-09-01", util=500e6, cap=1000e6, region="Oriente", pub="2026-09-05"):
    return {
        "FechaPublicacion": pub,
        "Fecha": fecha,
        "CodigoEmbalse": codigo,
        "RegionHidrologica": region,
        "CapacidadUtilMasa": cap,
        "VolumenUtilDiarioMasa": util,
        "VolumenTotalMasa": util + 100e6,
        "VertimientosMasa": 0.0,
    }


class TestNormalizacionYIndices:
    @pytest.mark.parametrize("codigo", ["AGREGADO", "AGREGADO_BOGOTA"])
    def test_el_agregado_de_bogota_tiene_un_solo_id(self, codigo):
        assert normalizar_codigo(codigo) == "AGREGADO_BOGOTA"

    def test_otros_codigos_no_cambian(self):
        assert normalizar_codigo("GUAVIO") == "GUAVIO"

    def test_energia_pasa_de_kwh_a_gwh(self):
        filas = [{"Date": "2026-09-01", "Name": "GUAVIO", "Value": 2_500_000_000.0}]
        assert indexar_energia(filas, {"GUAVIO": "GUAVIO"}) == {("GUAVIO", D1): 2500.0}

    def test_energia_ignora_nombres_desconocidos_y_valores_nulos(self):
        filas = [
            {"Date": "2026-09-01", "Name": "DESCONOCIDO", "Value": 1.0},
            {"Date": "2026-09-01", "Name": "GUAVIO", "Value": None},
        ]
        assert indexar_energia(filas, {"GUAVIO": "GUAVIO"}) == {}

    def test_descargas_pasan_de_m3_por_dia_a_m3_por_segundo(self):
        filas = [
            {"Fecha": "2026-09-01", "CodigoEmbalse": "GUAVIO", "TipoDescarga": "DESCARGA TURBINADA", "Volumen": 8_640_000},
            {"Fecha": "2026-09-01", "CodigoEmbalse": "GUAVIO", "TipoDescarga": "VERTIMIENTO", "Volumen": 864_000},
        ]
        indice = indexar_descargas(filas)
        assert indice[("GUAVIO", D1, "DESCARGA TURBINADA")] == pytest.approx(100.0)
        assert indice[("GUAVIO", D1, "VERTIMIENTO")] == pytest.approx(10.0)

    def test_descargas_normalizan_el_codigo_del_agregado(self):
        filas = [{"Fecha": "2026-09-01", "CodigoEmbalse": "AGREGADO", "TipoDescarga": "VERTIMIENTO", "Volumen": 86_400}]
        assert ("AGREGADO_BOGOTA", D1, "VERTIMIENTO") in indexar_descargas(filas)

    def test_aportes_suman_las_series_de_rio_de_un_mismo_embalse(self):
        filas = [
            {"Fecha": "2026-09-01", "CodigoSerieHidrologica": "AMANMIEL", "AportesHidricosMasa": 10.0, "MediaHistoricaMasa": 20.0},
            {"Fecha": "2026-09-01", "CodigoSerieHidrologica": "PTEHMIEL", "AportesHidricosMasa": 5.0, "MediaHistoricaMasa": 8.0},
        ]
        assert indexar_aportes(filas) == {("MIEL1", D1): (15.0, 28.0)}

    def test_aportes_ignoran_series_que_no_alimentan_un_embalse(self):
        filas = [{"Fecha": "2026-09-01", "CodigoSerieHidrologica": "DESVCHIV", "AportesHidricosMasa": 9.0, "MediaHistoricaMasa": 9.0}]
        assert indexar_aportes(filas) == {}

    def test_los_codigos_antiguos_y_nuevos_de_una_serie_apuntan_al_mismo_embalse(self):
        for codigo in ("GUAVGUAV", "EMBAGUAV"):
            filas = [{"Fecha": "2026-09-01", "CodigoSerieHidrologica": codigo, "AportesHidricosMasa": 1.0, "MediaHistoricaMasa": 1.0}]
            assert ("GUAVIO", D1) in indexar_aportes(filas)


class TestEnsamblar:
    def _todo(self):
        return dict(
            volumenes=[_volumen()],
            descargas=[
                {"Fecha": "2026-09-01", "CodigoEmbalse": "GUAVIO", "TipoDescarga": "DESCARGA TURBINADA", "Volumen": 8_640_000},
                {"Fecha": "2026-09-01", "CodigoEmbalse": "GUAVIO", "TipoDescarga": "VERTIMIENTO", "Volumen": 0},
            ],
            aportes=[{"Fecha": "2026-09-01", "CodigoSerieHidrologica": "GUAVGUAV", "AportesHidricosMasa": 80.0, "MediaHistoricaMasa": 100.0}],
            energia_util={("GUAVIO", D1): 1200.0},
            capacidad_energia={("GUAVIO", D1): 2400.0},
        )

    def test_convierte_unidades_y_une_las_fuentes(self):
        embalses, mediciones, descartadas = ensamblar(**self._todo())

        assert descartadas == 0
        assert [(e.id, e.nombre, str(e.region), e.es_agregado) for e in embalses] == [
            ("GUAVIO", "Guavio", "Oriente", False)
        ]
        m = mediciones[0]
        assert m.volumen_util.valor_mm3 == 500.0
        assert m.capacidad_util.valor_mm3 == 1000.0
        assert m.energia_util_gwh == 1200.0
        assert m.capacidad_util_energia_gwh == 2400.0
        assert m.turbinado.valor_m3s == pytest.approx(100.0)
        assert m.vertimientos.valor_m3s == 0.0
        assert m.aportes.valor_m3s == 80.0
        assert m.aportes_media_historica_m3s == 100.0

    def test_lo_que_la_fuente_no_publica_queda_en_none_no_en_cero(self):
        datos = self._todo()
        datos["descargas"] = []
        datos["aportes"] = []
        m = ensamblar(**datos)[1][0]
        assert m.turbinado is None
        assert m.vertimientos is None
        assert m.aportes is None
        assert m.aportes_media_historica_m3s is None

    def test_el_agregado_nacional_oficial_no_es_un_embalse(self):
        datos = self._todo()
        datos["volumenes"].append(_volumen("AGREGADO_SIN", region="Colombia"))
        datos["energia_util"][("AGREGADO_SIN", D1)] = 1.0
        datos["capacidad_energia"][("AGREGADO_SIN", D1)] = 1.0
        embalses, mediciones, _ = ensamblar(**datos)
        assert [e.id for e in embalses] == ["GUAVIO"]
        assert len(mediciones) == 1

    def test_el_agregado_de_bogota_se_unifica_y_se_marca_como_agregado(self):
        datos = dict(
            volumenes=[
                _volumen("AGREGADO_BOGOTA", "2026-09-01", region="Centro"),
                _volumen("AGREGADO", "2026-09-02", region="Centro"),
            ],
            descargas=[],
            aportes=[],
            energia_util={("AGREGADO_BOGOTA", D1): 1.0, ("AGREGADO_BOGOTA", D2): 1.0},
            capacidad_energia={("AGREGADO_BOGOTA", D1): 2.0, ("AGREGADO_BOGOTA", D2): 2.0},
        )
        embalses, mediciones, _ = ensamblar(**datos)
        assert [(e.id, e.es_agregado) for e in embalses] == [("AGREGADO_BOGOTA", True)]
        assert {m.embalse_id for m in mediciones} == {"AGREGADO_BOGOTA"}
        assert len(mediciones) == 2

    def test_sin_energia_ese_dia_conserva_los_volumenes_reales(self):
        datos = self._todo()
        datos["volumenes"].append(_volumen(fecha="2026-09-02", util=600e6))
        datos["energia_util"] = {("GUAVIO", D1): 1200.0}
        datos["capacidad_energia"] = {("GUAVIO", D1): 2400.0}

        _, mediciones, descartadas = ensamblar(**datos)

        dia2 = next(m for m in mediciones if m.fecha == D2)
        assert descartadas == 0
        assert dia2.volumen_util.valor_mm3 == 600.0
        assert dia2.energia_util_gwh is None
        assert dia2.capacidad_util_energia_gwh == 2400.0

    def test_el_peso_faltante_usa_la_capacidad_publicada_mas_cercana(self):
        datos = dict(
            volumenes=[_volumen(fecha="2026-09-02")],
            descargas=[],
            aportes=[],
            energia_util={},
            capacidad_energia={("GUAVIO", D1): 100.0, ("GUAVIO", date(2026, 9, 10)): 900.0},
        )
        m = ensamblar(**datos)[1][0]
        assert m.capacidad_util_energia_gwh == 100.0

    def test_sin_ninguna_capacidad_de_energia_se_descarta_la_fila(self):
        datos = self._todo()
        datos["energia_util"] = {}
        datos["capacidad_energia"] = {}
        embalses, mediciones, descartadas = ensamblar(**datos)
        assert mediciones == [] and embalses == []
        assert descartadas == 1

    def test_una_region_desconocida_es_un_error_explicito(self):
        datos = self._todo()
        datos["volumenes"] = [_volumen(region="Atlantida")]
        with pytest.raises(FuenteDatosError, match="Atlantida"):
            ensamblar(**datos)

    def test_un_embalse_nuevo_sin_nombre_conocido_usa_su_codigo(self):
        datos = self._todo()
        datos["volumenes"] = [_volumen("NUEVO1")]
        datos["energia_util"] = {("NUEVO1", D1): 1.0}
        datos["capacidad_energia"] = {("NUEVO1", D1): 1.0}
        assert ensamblar(**datos)[0][0].nombre == "Nuevo1"

    def test_la_publicacion_mas_reciente_prevalece_ante_duplicados(self):
        datos = self._todo()
        datos["volumenes"] = [
            _volumen(util=100e6, pub="2026-09-02"),
            _volumen(util=700e6, pub="2026-09-10"),
        ]
        mediciones = ensamblar(**datos)[1]
        assert mediciones[-1].volumen_util.valor_mm3 == 700.0


class _ClienteSimemFalso:
    def __init__(self, datasets):
        self.datasets = datasets
        self.llamadas = []

    def consultar(self, dataset_id, desde, hasta):
        self.llamadas.append((dataset_id, desde, hasta))
        return self.datasets.get(dataset_id, [])


class _ClienteXmFalso:
    def __init__(self, energia, capacidad):
        self.metricas = {"VoluUtilDiarEner": energia, "CapaUtilDiarEner": capacidad}
        self.llamadas = []

    def listar_embalses(self):
        return [{"Code": "GUAVIO", "Name": "GUAVIO"}, {"Code": "AGREGADO", "Name": "AGREGADO BOGOTA"}]

    def metrica_diaria_embalses(self, metrica, desde, hasta):
        self.llamadas.append((metrica, desde, hasta))
        return self.metricas[metrica]


class TestAdaptadorCompleto:
    def _fuente(self, volumenes=None):
        simem = _ClienteSimemFalso({"138ED1": volumenes if volumenes is not None else [_volumen()]})
        xm = _ClienteXmFalso(
            energia=[{"Date": "2026-09-01", "Name": "GUAVIO", "Value": 1.2e9}],
            capacidad=[{"Date": "2026-09-01", "Name": "GUAVIO", "Value": 2.4e9}],
        )
        return SimemXmFuenteMediciones(simem, xm), simem, xm

    def test_descarga_datos_reales_y_los_marca_como_tales(self):
        fuente, _, _ = self._fuente()
        descarga = fuente.descargar(D1, D3)
        assert descarga.es_real is True
        assert "SIMEM" in descarga.fuente
        assert descarga.mediciones[0].energia_util_gwh == 1200.0

    def test_pide_a_ambas_fuentes_el_rango_solicitado(self):
        fuente, simem, xm = self._fuente()
        fuente.descargar(D1, D3)
        assert {c[0] for c in simem.llamadas} == {"138ED1", "1445AC", "02B289"}
        assert all(c[1:] == (D1, D3) for c in simem.llamadas)
        assert {c[0] for c in xm.llamadas} == {"VoluUtilDiarEner", "CapaUtilDiarEner"}

    def test_sin_mediciones_es_un_error_no_un_exito_vacio(self):
        fuente, _, _ = self._fuente(volumenes=[])
        with pytest.raises(FuenteDatosError):
            fuente.descargar(D1, D3)


class _RespuestaFalsa:
    def __init__(self, cuerpo, ok=True):
        self._cuerpo, self._ok = cuerpo, ok

    def raise_for_status(self):
        if not self._ok:
            raise requests.HTTPError("500")

    def json(self):
        return self._cuerpo


class _SesionFalsa:
    def __init__(self, error=None):
        self.cuerpos = []
        self.error = error

    def post(self, url, json=None, **kwargs):
        if self.error:
            raise self.error
        self.cuerpos.append(json)
        return _RespuestaFalsa({"Items": []})


class TestClienteXm:
    def test_divide_el_rango_en_bloques_permitidos_por_la_api(self):
        sesion = _SesionFalsa()
        ClienteXm(sesion).metrica_diaria_embalses("VoluUtilDiarEner", date(2026, 1, 1), date(2026, 3, 16))

        rangos = [(date.fromisoformat(c["StartDate"]), date.fromisoformat(c["EndDate"])) for c in sesion.cuerpos]
        assert len(rangos) == 3
        assert rangos[0][0] == date(2026, 1, 1) and rangos[-1][1] == date(2026, 3, 16)
        for (_, fin), (inicio, _) in zip(rangos, rangos[1:]):
            assert (inicio - fin).days == 1
        assert all((fin - inicio).days + 1 <= DIAS_POR_CONSULTA_XM for inicio, fin in rangos)

    def test_un_dia_es_una_sola_consulta(self):
        sesion = _SesionFalsa()
        ClienteXm(sesion).metrica_diaria_embalses("CapaUtilDiarEner", D1, D1)
        assert len(sesion.cuerpos) == 1

    def test_un_error_de_red_se_traduce_a_error_de_fuente(self):
        sesion = _SesionFalsa(error=requests.ConnectionError("sin red"))
        with pytest.raises(FuenteDatosError, match="VoluUtilDiarEner"):
            ClienteXm(sesion).metrica_diaria_embalses("VoluUtilDiarEner", D1, D2)
