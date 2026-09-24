import pytest

from presentation.api.arranque_vercel import preparar_base_en_tmp


def test_copia_la_base_empaquetada_al_destino_escribible(tmp_path):
    origen = tmp_path / "empaquetada" / "hidrologia.duckdb"
    origen.parent.mkdir()
    origen.write_bytes(b"contenido de la base")
    destino = tmp_path / "tmp" / "hidrologia.duckdb"

    ruta = preparar_base_en_tmp(origen, destino)

    assert ruta == str(destino)
    assert destino.read_bytes() == b"contenido de la base"


def test_crea_el_directorio_destino_si_no_existe(tmp_path):
    origen = tmp_path / "a.duckdb"
    origen.write_bytes(b"x")
    destino = tmp_path / "no" / "existe" / "a.duckdb"
    preparar_base_en_tmp(origen, destino)
    assert destino.exists()


def test_no_pisa_una_copia_existente_en_arranques_en_caliente(tmp_path):
    origen = tmp_path / "a.duckdb"
    origen.write_bytes(b"original")
    destino = tmp_path / "copia.duckdb"
    destino.write_bytes(b"con cambios de la instancia")

    preparar_base_en_tmp(origen, destino)

    assert destino.read_bytes() == b"con cambios de la instancia"


def test_falla_con_un_mensaje_claro_si_el_despliegue_no_incluye_la_base(tmp_path):
    with pytest.raises(FileNotFoundError, match="data/hidrologia.duckdb"):
        preparar_base_en_tmp(tmp_path / "falta.duckdb", tmp_path / "destino.duckdb")
