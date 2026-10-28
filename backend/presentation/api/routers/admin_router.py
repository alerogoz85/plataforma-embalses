"""Modulo de actualizacion de tableros: /api/v1/admin/*. Es la UNICA parte de la API que escribe.

Seguridad (defensa en capas):
* Autenticacion con usuario y contraseña (hash scrypt), bloqueo por intentos y freno por direccion.
* Sesion en una cookie HttpOnly + SameSite=Strict (+ Secure fuera de localhost): el JavaScript de la pagina no la puede leer.
* Toda peticion que escribe exige ademas el encabezado X-CSRF-Token (el valor lo entrega el inicio de sesion): una pagina ajena no puede usarla.
* Permisos por rol y por tablero; cada intento (permitido o no) queda en la bitacora.
* Los archivos se revisan (nombre, tamaño, contenido real, estructura) antes de leerse y de nuevo al aplicar; lo aplicado es exactamente lo validado (sha256).
* El cuerpo se acota antes de leerlo y las respuestas de error no revelan detalles internos."""
from __future__ import annotations

import hashlib
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, File, Form, Header, Request, Response, UploadFile
from pydantic import BaseModel, Field

from application.dtos.actualizacion_dto import CatalogoActualizacionDTO, RegistroAuditoriaDTO, ResultadoCargaDTO, SesionDTO
from application.use_cases.actualizacion import ActualizarTableroUseCase, ListarTablerosActualizablesUseCase
from application.use_cases.seguridad import (
    CerrarSesionUseCase,
    ContextoSesion,
    IniciarSesionUseCase,
    ListarAuditoriaUseCase,
    ObtenerSesionUseCase,
    sesion_dto,
)
from domain.entities.actualizacion import ArchivoRecibido
from domain.entities.seguridad import VIGENCIA_SESION
from domain.exceptions import CargaInvalidaError
from infrastructure.archivos.compresion import GzipInvalidoError, descomprimir_gzip
from infrastructure.archivos.validador import limite_de_bytes, limite_de_contenido, limite_total_de_bytes
from presentation.api import dependencies as dep

router = APIRouter(prefix="/api/v1/admin", tags=["actualizacion"])

NOMBRE_COOKIE = "sesion_tableros"
MAX_ARCHIVOS_POR_PETICION = 20
SOBRECARGA_MULTIPART = 256 * 1024


class CredencialesEntrada(BaseModel):
    usuario: str = Field(min_length=1, max_length=80)
    contrasena: str = Field(min_length=1, max_length=200)


def _ip(request: Request) -> str:
    """Direccion del cliente. Detras de Vercel viene en X-Forwarded-For (primer valor); en local, la del socket."""
    reenviada = request.headers.get("x-forwarded-for", "")
    if reenviada:
        return reenviada.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "desconocida")[:64]


def _cookie_segura(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "") == "https"


def contexto_lectura(sesion_cookie: Optional[str] = Cookie(default=None, alias=NOMBRE_COOKIE), caso: ObtenerSesionUseCase = Depends(dep.obtener_sesion_use_case)) -> ContextoSesion:
    return caso.ejecutar(sesion_cookie)


def contexto_escritura(
    sesion_cookie: Optional[str] = Cookie(default=None, alias=NOMBRE_COOKIE),
    csrf: Optional[str] = Header(default=None, alias="X-CSRF-Token"),
    caso: ObtenerSesionUseCase = Depends(dep.obtener_sesion_use_case),
) -> ContextoSesion:
    return caso.ejecutar(sesion_cookie, csrf, exigir_csrf=True)


@router.post("/sesion", response_model=SesionDTO, summary="Inicia sesión")
def iniciar_sesion(
    entrada: CredencialesEntrada, request: Request, respuesta: Response,
    caso: IniciarSesionUseCase = Depends(dep.obtener_iniciar_sesion_use_case),
    ids: list[str] = Depends(dep.obtener_ids_tableros_actualizables),
) -> SesionDTO:
    iniciada = caso.ejecutar(entrada.usuario, entrada.contrasena, _ip(request))
    respuesta.set_cookie(
        NOMBRE_COOKIE, iniciada.token, max_age=int(VIGENCIA_SESION.total_seconds()), httponly=True, samesite="strict",
        secure=_cookie_segura(request), path="/api/v1/admin",
    )
    respuesta.headers["Cache-Control"] = "no-store"
    return sesion_dto(iniciada.usuario, iniciada.sesion, tuple(ids))


@router.get("/sesion", response_model=SesionDTO, summary="Sesión actual")
def sesion_actual(
    respuesta: Response, contexto: ContextoSesion = Depends(contexto_lectura), ids: list[str] = Depends(dep.obtener_ids_tableros_actualizables)
) -> SesionDTO:
    respuesta.headers["Cache-Control"] = "no-store"
    return sesion_dto(contexto.usuario, contexto.sesion, tuple(ids))


@router.delete("/sesion", status_code=204, summary="Cierra la sesión")
def cerrar_sesion(
    request: Request, respuesta: Response, contexto: ContextoSesion = Depends(contexto_escritura),
    caso: CerrarSesionUseCase = Depends(dep.obtener_cerrar_sesion_use_case),
) -> Response:
    caso.ejecutar(contexto, _ip(request))
    respuesta.delete_cookie(NOMBRE_COOKIE, path="/api/v1/admin")
    respuesta.status_code = 204
    return respuesta


@router.get("/tableros", response_model=CatalogoActualizacionDTO, summary="Tableros que el usuario puede actualizar y archivos que pide cada uno")
def listar_tableros(
    respuesta: Response, contexto: ContextoSesion = Depends(contexto_lectura),
    caso: ListarTablerosActualizablesUseCase = Depends(dep.obtener_listar_tableros_use_case),
) -> CatalogoActualizacionDTO:
    respuesta.headers["Cache-Control"] = "no-store"
    return caso.ejecutar(contexto)


async def _leer_archivos(request: Request, archivos: list[UploadFile], claves: list[str]) -> list[ArchivoRecibido]:
    """Lee cada archivo con tope de tamaño (nunca mas de limite+1 bytes por archivo) y calcula su huella.

    Un archivo «.gz» (el navegador comprime los CSV grandes para que quepan en la peticion) se descomprime aqui con tope de tamaño y se
    trata como el archivo original; la huella es la del contenido descomprimido, que es lo que se valida y se guarda."""
    if len(archivos) != len(claves) or len(archivos) > MAX_ARCHIVOS_POR_PETICION:
        raise CargaInvalidaError(["La petición debe traer un archivo por cada clave indicada (máximo %d)" % MAX_ARCHIVOS_POR_PETICION])
    limite = limite_de_bytes()
    recibidos: list[ArchivoRecibido] = []
    total = 0
    for clave, f in zip(claves, archivos):
        nombre = (f.filename or "")[:200]
        contenido = await f.read(limite + 1)
        total += len(contenido)
        if total > limite_total_de_bytes():
            raise CargaInvalidaError([f"Los archivos suman más de {limite_total_de_bytes() / 1_048_576:.1f} MB; envía menos archivos por vez"])
        if len(contenido) > limite:  # se leyeron limite+1 bytes: lo que sigue no se leyo y el archivo no cabe en la peticion
            raise CargaInvalidaError([f"{nombre[:60]}: pesa más de {limite / 1_048_576:.1f} MB; los CSV grandes se envían comprimidos (.gz)"])
        if nombre.lower().endswith(".gz"):
            try:
                contenido, nombre = descomprimir_gzip(contenido, limite_de_contenido()), nombre[:-3]
            except GzipInvalidoError as error:
                raise CargaInvalidaError([f"{nombre[:60]}: {error}"]) from error
        recibidos.append(ArchivoRecibido(clave=clave[:60], nombre=nombre, contenido=contenido, huella=hashlib.sha256(contenido).hexdigest()))
    return recibidos


def _rechazar_si_excede(request: Request) -> None:
    """Corta antes de leer el cuerpo si el tamaño declarado ya supera el maximo posible de la peticion."""
    declarado = request.headers.get("content-length")
    maximo = limite_de_bytes() * MAX_ARCHIVOS_POR_PETICION + SOBRECARGA_MULTIPART
    if declarado and declarado.isdigit() and int(declarado) > maximo:
        raise CargaInvalidaError([f"La petición es demasiado grande (máximo {limite_de_bytes() // 1_048_576} MB por archivo)"])


@router.post("/tableros/{tablero_id}/validar", response_model=ResultadoCargaDTO, summary="Revisa los archivos sin guardar nada")
async def validar(
    tablero_id: str, request: Request, claves: list[str] = Form(...), archivos: list[UploadFile] = File(...),
    contexto: ContextoSesion = Depends(contexto_escritura), caso: ActualizarTableroUseCase = Depends(dep.obtener_actualizar_tablero_use_case),
) -> ResultadoCargaDTO:
    _rechazar_si_excede(request)
    recibidos = await _leer_archivos(request, archivos, claves)
    return caso.validar(contexto, tablero_id[:40], recibidos, _ip(request))


@router.post("/tableros/{tablero_id}/aplicar", response_model=ResultadoCargaDTO, summary="Guarda los archivos validados y actualiza el tablero")
async def aplicar(
    tablero_id: str, request: Request, claves: list[str] = Form(...), huellas: list[str] = Form(...), archivos: list[UploadFile] = File(...),
    contexto: ContextoSesion = Depends(contexto_escritura), caso: ActualizarTableroUseCase = Depends(dep.obtener_actualizar_tablero_use_case),
) -> ResultadoCargaDTO:
    _rechazar_si_excede(request)
    if len(huellas) != len(claves):
        raise CargaInvalidaError(["Cada archivo debe traer la huella de su validación"])
    recibidos = await _leer_archivos(request, archivos, claves)
    return caso.aplicar(contexto, tablero_id[:40], recibidos, dict(zip(claves, huellas)), _ip(request))


@router.get("/auditoria", response_model=list[RegistroAuditoriaDTO], summary="Bitácora de accesos y cargas (solo administradores)")
def auditoria(
    respuesta: Response, limite: int = 100, contexto: ContextoSesion = Depends(contexto_lectura),
    caso: ListarAuditoriaUseCase = Depends(dep.obtener_listar_auditoria_use_case),
) -> list[RegistroAuditoriaDTO]:
    respuesta.headers["Cache-Control"] = "no-store"
    return caso.ejecutar(contexto, limite)
