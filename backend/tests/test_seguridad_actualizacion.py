"""Seguridad del modulo de actualizacion: contraseñas, bloqueo, sesiones, CSRF, permisos, bitacora y validacion de archivos."""
import io
import zipfile
from datetime import datetime, timedelta

import pytest
from application.use_cases.actualizacion import ListarTablerosActualizablesUseCase
from application.use_cases.seguridad import (
    CerrarSesionUseCase,
    IniciarSesionUseCase,
    ListarAuditoriaUseCase,
    ObtenerSesionUseCase,
    huella_de,
)
from domain.entities.actualizacion import ArchivoRequerido
from domain.entities.seguridad import CredencialUsuario, Usuario, validar_contrasena
from domain.exceptions import CredencialesInvalidasError, CuentaBloqueadaError, SesionInvalidaError
from infrastructure.actualizacion.tableros import construir_adaptadores
from infrastructure.archivos.area_trabajo import AreaTemporal
from infrastructure.archivos.validador import limite_de_bytes, validar_archivo, validar_nombre
from infrastructure.persistence.duckdb_connection import DuckDBConnection
from infrastructure.persistence.sql_seguridad_repository import SqlAuditoriaRepository, SqlSesionRepository, SqlUsuarioRepository
from infrastructure.seguridad import contrasenas

CONTRASENA = "Clave-Segura-2026"


class RelojFalso:
    def __init__(self) -> None:
        self.ahora = datetime(2026, 10, 27, 9, 0, 0)

    def __call__(self) -> datetime:
        self.ahora += timedelta(microseconds=1)  # cada consulta del reloj es un instante distinto (la bitacora se ordena por momento)
        return self.ahora

    def avanzar(self, **kw) -> None:
        self.ahora += timedelta(**kw)


class _Contrasenas:
    verificar = staticmethod(contrasenas.verificar)
    verificar_falso = staticmethod(contrasenas.verificar_falso)


class _RepoVacio:
    """Repositorio de tableros que no se usa en estas pruebas (solo interesa el catalogo de archivos)."""

    def reemplazar(self, *_):
        self.llamado = True


@pytest.fixture
def mundo(tmp_path, monkeypatch):
    monkeypatch.setattr(contrasenas, "N", 2**10)  # scrypt barato: la prueba no necesita el costo real
    db = DuckDBConnection(str(tmp_path / "s.duckdb"))
    reloj = RelojFalso()
    usuarios, sesiones, auditoria = SqlUsuarioRepository(db), SqlSesionRepository(db), SqlAuditoriaRepository(db)
    h = contrasenas.hashear(CONTRASENA)
    usuarios.guardar(CredencialUsuario(Usuario("ana", "Ana", "administrador", ()), h))
    usuarios.guardar(CredencialUsuario(Usuario("luis", "Luis", "cargador", ("gas",)), h))
    usuarios.guardar(CredencialUsuario(Usuario("inactivo", "Off", "administrador", (), activo=False), h))
    repo = _RepoVacio()
    adaptadores = construir_adaptadores(repo, repo, repo, repo)  # type: ignore[arg-type]
    return dict(db=db, reloj=reloj, usuarios=usuarios, sesiones=sesiones, auditoria=auditoria, repo=repo, adaptadores=adaptadores)


def iniciar(m):
    return IniciarSesionUseCase(m["usuarios"], m["sesiones"], m["auditoria"], _Contrasenas(), m["reloj"])


class TestContrasenas:
    def test_el_hash_no_contiene_la_contrasena_y_verifica(self):
        h = contrasenas.hashear(CONTRASENA)
        assert CONTRASENA not in h and h.startswith("scrypt$")
        assert contrasenas.verificar(CONTRASENA, h) and not contrasenas.verificar("otra", h)

    def test_dos_hashes_de_la_misma_contrasena_son_distintos(self):
        assert contrasenas.hashear(CONTRASENA) != contrasenas.hashear(CONTRASENA)

    @pytest.mark.parametrize("malo", ["", "scrypt$1$2", "md5$a$b$c$d$e", "scrypt$x$8$1$AAAA$AAAA"])
    def test_un_hash_mal_formado_nunca_verifica_ni_lanza(self, malo):
        assert contrasenas.verificar(CONTRASENA, malo) is False

    @pytest.mark.parametrize("clave,motivo", [
        ("corta1!", "12 caracteres"), ("sololetrasminusculas", "letras con números"), ("1234567890123", "letras con números"),
        ("ana-clave-2026", "nombre de usuario"), ("aaaaaaaaaaa1", "repetitiva"),
    ])
    def test_politica_de_contrasenas(self, clave, motivo):
        with pytest.raises(ValueError, match=motivo):
            validar_contrasena(clave, "ana")

    def test_una_contrasena_valida_pasa(self):
        validar_contrasena(CONTRASENA, "ana")


class TestInicioDeSesion:
    def test_inicio_correcto_guarda_solo_la_huella_del_token(self, mundo):
        r = iniciar(mundo).ejecutar("Ana", CONTRASENA, "10.0.0.1")
        assert r.token and r.sesion.huella_token == huella_de(r.token) and r.token != r.sesion.huella_token
        assert mundo["sesiones"].obtener(huella_de(r.token)) is not None
        assert mundo["sesiones"].obtener(r.token) is None  # el token en claro no esta en la base

    def test_credenciales_incorrectas_dan_el_mismo_error_exista_o_no_el_usuario(self, mundo):
        for usuario in ("ana", "no_existe", "inactivo"):
            with pytest.raises(CredencialesInvalidasError) as e:
                iniciar(mundo).ejecutar(usuario, "incorrecta", "10.0.0.2")
            assert str(e.value) == "Usuario o contraseña incorrectos"

    def test_cinco_fallos_bloquean_la_cuenta_incluso_con_la_clave_correcta(self, mundo):
        for _ in range(4):
            with pytest.raises(CredencialesInvalidasError):
                iniciar(mundo).ejecutar("ana", "mala", "10.0.0.3")
        with pytest.raises(CuentaBloqueadaError):
            iniciar(mundo).ejecutar("ana", "mala", "10.0.0.3")
        with pytest.raises(CuentaBloqueadaError):
            iniciar(mundo).ejecutar("ana", CONTRASENA, "10.0.0.3")

    def test_el_bloqueo_vence_y_un_acierto_reinicia_el_contador(self, mundo):
        for _ in range(5):
            with pytest.raises((CredencialesInvalidasError, CuentaBloqueadaError)):
                iniciar(mundo).ejecutar("ana", "mala", "10.0.0.4")
        mundo["reloj"].avanzar(minutes=16)
        iniciar(mundo).ejecutar("ana", CONTRASENA, "10.0.0.4")
        assert mundo["usuarios"].obtener("ana").intentos_fallidos == 0

    def test_tras_el_bloqueo_vencido_un_solo_fallo_no_vuelve_a_bloquear(self, mundo):
        for _ in range(5):
            with pytest.raises((CredencialesInvalidasError, CuentaBloqueadaError)):
                iniciar(mundo).ejecutar("ana", "mala", "10.0.0.5")
        mundo["reloj"].avanzar(minutes=16)
        with pytest.raises(CredencialesInvalidasError):
            iniciar(mundo).ejecutar("ana", "mala", "10.0.0.5")

    def test_muchos_fallos_desde_una_misma_direccion_se_frenan(self, mundo):
        for i in range(20):
            with pytest.raises((CredencialesInvalidasError, CuentaBloqueadaError)):
                iniciar(mundo).ejecutar(f"usuario{i}", "mala", "10.9.9.9")
        with pytest.raises(CuentaBloqueadaError):
            iniciar(mundo).ejecutar("ana", CONTRASENA, "10.9.9.9")
        iniciar(mundo).ejecutar("ana", CONTRASENA, "10.9.9.10")  # otra direccion no se ve afectada

    def test_la_bitacora_registra_aciertos_y_fallos_sin_contrasenas(self, mundo):
        with pytest.raises(CredencialesInvalidasError):
            iniciar(mundo).ejecutar("ana", "mala-clave-123", "10.0.0.6")
        iniciar(mundo).ejecutar("ana", CONTRASENA, "10.0.0.6")
        registros = mundo["auditoria"].listar(10)
        assert [r.accion for r in registros] == ["inicio_sesion", "inicio_sesion_fallido"]
        assert all("mala-clave-123" not in r.detalle and CONTRASENA not in r.detalle for r in registros)

    def test_la_bitacora_no_admite_saltos_de_linea_falsificados(self, mundo):
        with pytest.raises(CredencialesInvalidasError):
            iniciar(mundo).ejecutar("ana\n2026-01-01 ok admin", "x", "10.0.0.7\r\nforjada")
        r = mundo["auditoria"].listar(1)[0]
        assert "\n" not in r.nombre_usuario and "\n" not in r.ip and "\r" not in r.ip


class TestSesion:
    def _sesion(self, mundo, usuario="ana"):
        return iniciar(mundo).ejecutar(usuario, CONTRASENA, "10.0.0.8")

    def _obtener(self, mundo):
        return ObtenerSesionUseCase(mundo["usuarios"], mundo["sesiones"], mundo["reloj"])

    def test_sin_token_o_con_token_inventado_no_hay_sesion(self, mundo):
        for token in (None, "", "x" * 300, "inventado"):
            with pytest.raises(SesionInvalidaError):
                self._obtener(mundo).ejecutar(token)

    def test_la_sesion_vence_por_inactividad(self, mundo):
        s = self._sesion(mundo)
        mundo["reloj"].avanzar(minutes=31)
        with pytest.raises(SesionInvalidaError, match="venció"):
            self._obtener(mundo).ejecutar(s.token)
        assert mundo["sesiones"].obtener(s.sesion.huella_token) is None

    def test_la_actividad_la_mantiene_pero_no_pasa_de_8_horas(self, mundo):
        s = self._sesion(mundo)
        for _ in range(16):
            mundo["reloj"].avanzar(minutes=29)
            self._obtener(mundo).ejecutar(s.token)
        mundo["reloj"].avanzar(minutes=29)
        with pytest.raises(SesionInvalidaError):
            self._obtener(mundo).ejecutar(s.token)

    def test_las_peticiones_que_escriben_exigen_el_token_csrf(self, mundo):
        s = self._sesion(mundo)
        for malo in (None, "", "otro", s.token):
            with pytest.raises(SesionInvalidaError, match="CSRF"):
                self._obtener(mundo).ejecutar(s.token, malo, exigir_csrf=True)
        assert self._obtener(mundo).ejecutar(s.token, s.sesion.token_csrf, exigir_csrf=True).usuario.nombre_usuario == "ana"

    def test_cerrar_sesion_la_revoca_y_queda_en_bitacora(self, mundo):
        s = self._sesion(mundo)
        ctx = self._obtener(mundo).ejecutar(s.token)
        CerrarSesionUseCase(mundo["sesiones"], mundo["auditoria"], mundo["reloj"]).ejecutar(ctx, "10.0.0.8")
        with pytest.raises(SesionInvalidaError):
            self._obtener(mundo).ejecutar(s.token)
        assert mundo["auditoria"].listar(1)[0].accion == "cierre_sesion"

    def test_desactivar_al_usuario_invalida_su_sesion(self, mundo):
        s = self._sesion(mundo, "luis")
        c = mundo["usuarios"].obtener("luis")
        mundo["usuarios"].guardar(CredencialUsuario(Usuario("luis", "Luis", "cargador", ("gas",), activo=False), c.hash_contrasena))
        with pytest.raises(SesionInvalidaError):
            self._obtener(mundo).ejecutar(s.token)

    def test_solo_el_administrador_ve_la_bitacora(self, mundo):
        ana = self._obtener(mundo).ejecutar(self._sesion(mundo, "ana").token)
        luis = self._obtener(mundo).ejecutar(self._sesion(mundo, "luis").token)
        assert ListarAuditoriaUseCase(mundo["auditoria"]).ejecutar(ana)
        from domain.exceptions import AccesoDenegadoError
        with pytest.raises(AccesoDenegadoError):
            ListarAuditoriaUseCase(mundo["auditoria"]).ejecutar(luis)


class TestPermisos:
    def test_el_cargador_solo_ve_sus_tableros_y_el_admin_todos(self, mundo):
        listar = ListarTablerosActualizablesUseCase(mundo["adaptadores"], lambda: (limite_de_bytes(), 4_400_000, 60 * 1024 * 1024), lambda: True)
        obtener = ObtenerSesionUseCase(mundo["usuarios"], mundo["sesiones"], mundo["reloj"])
        luis = obtener.ejecutar(iniciar(mundo).ejecutar("luis", CONTRASENA, "1.1.1.1").token)
        ana = obtener.ejecutar(iniciar(mundo).ejecutar("ana", CONTRASENA, "1.1.1.1").token)
        assert [t.id for t in listar.ejecutar(luis).tableros] == ["gas"]
        assert {t.id for t in listar.ejecutar(ana).tableros} == {"carbon", "dns", "gas", "optimizacion", "apagon", "apagon_visor"}

    def test_el_usuario_inactivo_no_puede_actualizar(self):
        assert not Usuario("x", "X", "administrador", (), activo=False).puede_actualizar("gas")

    @pytest.mark.parametrize("nombre", ["", "con espacio", "a/b", "../x", "a;b", "ñandú"])
    def test_nombres_de_usuario_invalidos(self, nombre):
        with pytest.raises(ValueError):
            Usuario(nombre, "X", "cargador", ("gas",))

    def test_rol_desconocido(self):
        with pytest.raises(ValueError):
            Usuario("x", "X", "superusuario", ())


# ------------------------------------------------------------------------------------ validacion de archivos
def xlsx_minimo(extra: dict[str, bytes] | None = None) -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("xl/workbook.xml", "<workbook/>")
        for n, c in (extra or {}).items():
            z.writestr(n, c)
    return b.getvalue()


XLSX = ArchivoRequerido("v2", "Libro", "a.xlsx", ("xlsx",))
CSV = ArchivoRequerido("c", "Tabla", "a.csv", ("csv",))
JSON = ArchivoRequerido("j", "Datos", "a.json", ("json",))
PAR = ArchivoRequerido("p", "Base", "a.parquet", ("parquet",))
PATRON = ArchivoRequerido("pr", "Pronóstico", "d", ("csv",), patron_nombre=r"pronostico_\d{4}-(0[1-9]|1[0-2])\.csv")


class TestValidadorDeArchivos:
    def test_archivos_validos_pasan(self):
        assert validar_archivo(XLSX, "libro.xlsx", xlsx_minimo()) == []
        assert validar_archivo(CSV, "t.csv", b"a,b\n1,2\n") == []
        assert validar_archivo(CSV, "t.CSV", "a;b\nñ;2\n".encode("utf-8-sig")) == []
        assert validar_archivo(JSON, "d.json", b'{"a": 1}') == []
        assert validar_archivo(PAR, "b.parquet", b"PAR1xxxxPAR1") == []
        assert validar_archivo(PATRON, "pronostico_2026-11.csv", b"a\n1\n") == []

    @pytest.mark.parametrize("nombre", ["../etc/passwd.csv", "a/b.csv", "a\\b.csv", ".oculto.csv", "a\x00.csv", "a\n.csv", "x..csv", ""])
    def test_nombres_peligrosos_se_rechazan(self, nombre):
        assert validar_nombre(CSV, nombre)

    def test_extension_no_admitida(self):
        assert "no admitido" in validar_archivo(CSV, "t.exe", b"a,b\n1,2")[0]
        assert "no admitido" in validar_archivo(XLSX, "libro.xlsm", xlsx_minimo())[0]
        assert "no admitido" in validar_archivo(CSV, "t", b"a,b\n1,2")[0]

    def test_nombre_exacto_si_el_archivo_lo_pide(self):
        assert validar_archivo(PATRON, "pronostico_2026-13.csv", b"a\n1\n")
        assert validar_archivo(PATRON, "otro.csv", b"a\n1\n")

    def test_vacio_y_demasiado_grande(self, monkeypatch):
        assert "vacío" in validar_archivo(CSV, "t.csv", b"")[0]
        monkeypatch.setenv("MAX_CONTENT_BYTES", "100")  # CSV y JSON se miden ya descomprimidos
        assert "máximo" in validar_archivo(CSV, "t.csv", b"a,b\n" + b"1" * 200)[0]

    def test_un_limite_mal_configurado_vuelve_al_defecto(self, monkeypatch):
        for valor in ("abc", "0", "-5"):
            monkeypatch.setenv("MAX_UPLOAD_BYTES", valor)
            assert limite_de_bytes() == 4 * 1024 * 1024

    def test_el_contenido_debe_corresponder_a_la_extension(self):
        assert "no es un libro" in validar_archivo(XLSX, "libro.xlsx", b"MZ\x90\x00ejecutable")[0]
        assert "dañado" in validar_archivo(XLSX, "libro.xlsx", b"PK\x03\x04basura")[0]
        assert "Parquet" in validar_archivo(PAR, "b.parquet", b"no es parquet")[0]
        assert "JSON" in validar_archivo(JSON, "d.json", b"{no json")[0]
        assert "objeto o una lista" in validar_archivo(JSON, "d.json", b"42")[0]

    def test_xlsx_sin_estructura_de_libro(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("hola.txt", "x")
        assert "estructura" in validar_archivo(XLSX, "l.xlsx", b.getvalue())[0]

    def test_xlsx_con_macros_vinculos_externos_o_rutas_peligrosas(self):
        assert "macros" in validar_archivo(XLSX, "l.xlsx", xlsx_minimo({"xl/vbaProject.bin": b"x"}))[0]
        assert "vínculos" in validar_archivo(XLSX, "l.xlsx", xlsx_minimo({"xl/externalLinks/externalLink1.xml": b"x"}))[0]
        assert "rutas" in validar_archivo(XLSX, "l.xlsx", xlsx_minimo({"../evil.txt": b"x"}))[0]

    def test_bomba_de_compresion(self, monkeypatch):
        monkeypatch.setenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024))
        bomba = xlsx_minimo({"xl/relleno.xml": b"0" * (60 * 1024 * 1024)})
        assert len(bomba) < 1_000_000 and "bomba" in validar_archivo(XLSX, "l.xlsx", bomba)[0]

    def test_csv_con_bytes_nulos_o_codificacion_invalida(self):
        assert "nulos" in validar_archivo(CSV, "t.csv", b"a,b\n1,\x002\n")[0]
        assert "UTF-8" in validar_archivo(CSV, "t.csv", "a,b\nñ,2".encode("latin-1"))[0]
        assert "encabezado" in validar_archivo(CSV, "t.csv", b"soloencabezado")[0]

    def test_json_demasiado_anidado(self):
        assert "anidado" in validar_archivo(JSON, "d.json", (b"[" * 80 + b"]" * 80))[0]


class TestAreaDeTrabajo:
    def test_ubica_cada_archivo_en_la_ruta_del_catalogo_y_limpia(self, mundo):
        from domain.entities.actualizacion import ArchivoRecibido
        dns = mundo["adaptadores"]["dns"].definicion
        archivos = [ArchivoRecibido("pronostico", "pronostico_2026-11.csv", b"a\n1\n", "h"), ArchivoRecibido("mapeo", "cualquier_nombre.csv", b"x\n", "h")]
        with AreaTemporal().preparar(dns, archivos) as carpeta:
            assert (carpeta / "Datos/outputs/07_modelo/pronostico_2026-11.csv").read_bytes() == b"a\n1\n"
            assert (carpeta / "Datos/outputs_datos/mapeo_subareas.csv").is_file()  # el nombre del navegador no decide la ruta
            assert oct(carpeta.stat().st_mode & 0o777) == "0o700"
        assert not carpeta.exists()

    def test_limpia_aunque_el_lector_falle(self, mundo):
        from domain.entities.actualizacion import ArchivoRecibido
        gas = mundo["adaptadores"]["gas"].definicion
        carpeta_usada = None
        with pytest.raises(RuntimeError):
            with AreaTemporal().preparar(gas, [ArchivoRecibido("v2", "x.xlsx", b"x", "h")]) as carpeta:
                carpeta_usada = carpeta
                raise RuntimeError("fallo del lector")
        assert carpeta_usada and not carpeta_usada.exists()
