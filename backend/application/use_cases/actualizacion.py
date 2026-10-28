"""Casos de uso de la actualizacion de tableros: listar, validar (sin escribir) y aplicar (escribe y deja bitacora)."""
from __future__ import annotations

import logging
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from application.dtos.actualizacion_dto import (
    ArchivoRequeridoDTO,
    CatalogoActualizacionDTO,
    DatoResumenDTO,
    HuellaArchivoDTO,
    ResultadoCargaDTO,
    TableroActualizableDTO,
)
from application.use_cases.seguridad import ContextoSesion, Reloj
from domain.entities.actualizacion import ArchivoRecibido, TableroActualizable
from domain.entities.seguridad import RegistroAuditoria
from domain.exceptions import AccesoDenegadoError, AlmacenamientoNoPersistenteError, CargaInvalidaError, TableroNoActualizableError
from domain.repositories.seguridad_repository import AuditoriaRepository

registro = logging.getLogger(__name__)
MAX_ARCHIVOS = 20


class AdaptadorTableroPuerto(Protocol):
    definicion: TableroActualizable
    errores_de_lectura: tuple[type[Exception], ...]

    def leer(self, carpeta: Path) -> Any: ...
    def resumir(self, objeto: Any) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...]]: ...
    def guardar(self, objeto: Any) -> None: ...


class AreaDeTrabajo(Protocol):
    """Carpeta temporal privada donde se ubican los archivos recibidos con la estructura que espera el lector."""

    def preparar(self, definicion: TableroActualizable, archivos: list[ArchivoRecibido]) -> AbstractContextManager[Path]: ...


ValidadorArchivo = Callable[[Any, str, bytes], list[str]]


def _tablero_dto(t: TableroActualizable) -> TableroActualizableDTO:
    return TableroActualizableDTO(
        id=t.id, titulo=t.titulo, descripcion=t.descripcion,
        archivos=[ArchivoRequeridoDTO(clave=a.clave, etiqueta=a.etiqueta, formatos=list(a.formatos), obligatorio=a.obligatorio, descripcion=a.descripcion, patron_nombre=a.patron_nombre) for a in t.archivos],
    )


class ListarTablerosActualizablesUseCase:
    def __init__(self, adaptadores: Mapping[str, AdaptadorTableroPuerto], limites: Callable[[], tuple[int, int, int]], persistente: Callable[[], bool]) -> None:
        self._adaptadores, self._limites, self._persistente = adaptadores, limites, persistente

    def ejecutar(self, contexto: ContextoSesion) -> CatalogoActualizacionDTO:
        permitidos = [a.definicion for a in self._adaptadores.values() if contexto.usuario.puede_actualizar(a.definicion.id)]
        archivo, total, contenido = self._limites()
        return CatalogoActualizacionDTO(
            tableros=[_tablero_dto(t) for t in permitidos], limite_bytes=archivo, limite_total_bytes=total, limite_contenido_bytes=contenido,
            almacenamiento_persistente=self._persistente(),
        )


class ActualizarTableroUseCase:
    def __init__(
        self, adaptadores: Mapping[str, AdaptadorTableroPuerto], area: AreaDeTrabajo, validar_archivo: ValidadorArchivo,
        auditoria: AuditoriaRepository, reloj: Reloj, persistente: Callable[[], bool],
    ) -> None:
        self._adaptadores, self._area, self._validar_archivo, self._auditoria, self._reloj, self._persistente = (
            adaptadores, area, validar_archivo, auditoria, reloj, persistente,
        )

    # -- auditoria -------------------------------------------------------------------------------------------
    def _auditar(self, contexto: ContextoSesion, accion: str, tablero: str | None, resultado: str, detalle: str, ip: str) -> None:
        self._auditoria.registrar(RegistroAuditoria(self._reloj(), contexto.usuario.nombre_usuario, accion, tablero, resultado, detalle, ip))

    def _adaptador(self, contexto: ContextoSesion, tablero_id: str, ip: str) -> AdaptadorTableroPuerto:
        adaptador = self._adaptadores.get(tablero_id)
        if adaptador is None:
            raise TableroNoActualizableError(tablero_id[:40])
        if not contexto.usuario.puede_actualizar(tablero_id):
            self._auditar(contexto, "acceso_denegado", tablero_id, "rechazado", "intento de actualizar un tablero sin permiso", ip)
            raise AccesoDenegadoError("No tienes permiso para actualizar este tablero")
        return adaptador

    # -- revision completa -----------------------------------------------------------------------------------
    def _revisar(self, adaptador: AdaptadorTableroPuerto, archivos: list[ArchivoRecibido]) -> tuple[list[str], list[str], tuple, Any]:
        """(errores, advertencias, resumen, objeto leido). Si hay errores no se lee el contenido."""
        definicion = adaptador.definicion
        por_clave = {a.clave: a for a in definicion.archivos}
        errores: list[str] = []
        if len(archivos) > MAX_ARCHIVOS:
            return [f"Se recibieron demasiados archivos (máximo {MAX_ARCHIVOS})"], [], (), None
        vistas: set[str] = set()
        for a in archivos:
            if a.clave not in por_clave:
                errores.append(f"Archivo no esperado para este tablero: «{a.clave[:40]}»")
            elif a.clave in vistas:
                errores.append(f"El archivo «{por_clave[a.clave].etiqueta}» llegó más de una vez")
            vistas.add(a.clave)
        for requerido in definicion.archivos:
            if requerido.obligatorio and requerido.clave not in vistas:
                errores.append(f"Falta el archivo obligatorio: {requerido.etiqueta}")
        for a in archivos:
            if a.clave in por_clave:
                errores.extend(self._validar_archivo(por_clave[a.clave], a.nombre, a.contenido))
        if errores:
            return errores, [], (), None

        with self._area.preparar(definicion, archivos) as carpeta:
            try:
                objeto = adaptador.leer(carpeta)
            except adaptador.errores_de_lectura as error:
                return [str(error)[:500]], [], (), None
            except Exception:  # noqa: BLE001 - un archivo malformado no debe romper el servicio ni filtrar detalles internos
                registro.exception("Error inesperado al leer los archivos de %s", definicion.id)
                return ["No fue posible interpretar los archivos: la estructura no corresponde a la esperada para este tablero"], [], (), None
        resumen, advertencias = adaptador.resumir(objeto)
        return [], list(advertencias), resumen, objeto

    @staticmethod
    def _dto(tablero: str, errores: list[str], advertencias: list[str], resumen: tuple, archivos: list[ArchivoRecibido], aplicada: bool) -> ResultadoCargaDTO:
        return ResultadoCargaDTO(
            tablero=tablero, valido=not errores, aplicada=aplicada, resumen=[DatoResumenDTO(etiqueta=e, valor=v) for e, v in resumen],
            errores=errores, advertencias=advertencias, huellas=[HuellaArchivoDTO(clave=a.clave, sha256=a.huella) for a in archivos],
        )

    def validar(self, contexto: ContextoSesion, tablero_id: str, archivos: list[ArchivoRecibido], ip: str) -> ResultadoCargaDTO:
        """Revisa los archivos y dice que pasaria; no escribe nada."""
        adaptador = self._adaptador(contexto, tablero_id, ip)
        errores, advertencias, resumen, _ = self._revisar(adaptador, archivos)
        nombres = ", ".join(f"{a.clave}={a.nombre[:60]}" for a in archivos)
        self._auditar(contexto, "validacion", tablero_id, "ok" if not errores else "rechazado", f"{len(archivos)} archivo(s): {nombres}" + (f" · {len(errores)} error(es)" if errores else ""), ip)
        return self._dto(tablero_id, errores, advertencias, resumen, archivos, aplicada=False)

    def aplicar(self, contexto: ContextoSesion, tablero_id: str, archivos: list[ArchivoRecibido], huellas_validadas: dict[str, str], ip: str) -> ResultadoCargaDTO:
        """Vuelve a revisar TODO (no confia en la validacion previa), comprueba que los archivos son los mismos que se validaron y los guarda."""
        adaptador = self._adaptador(contexto, tablero_id, ip)
        if not self._persistente():
            self._auditar(contexto, "actualizacion", tablero_id, "rechazado", "entorno sin almacenamiento persistente", ip)
            raise AlmacenamientoNoPersistenteError()
        actuales = {a.clave: a.huella for a in archivos}
        if actuales != huellas_validadas:
            self._auditar(contexto, "actualizacion", tablero_id, "rechazado", "los archivos no coinciden con los validados", ip)
            raise CargaInvalidaError(["Los archivos no coinciden con los que se validaron: valida de nuevo antes de aplicar"])
        errores, advertencias, resumen, objeto = self._revisar(adaptador, archivos)
        if errores:
            self._auditar(contexto, "actualizacion", tablero_id, "rechazado", f"{len(errores)} error(es) de validación", ip)
            raise CargaInvalidaError(errores)
        try:
            adaptador.guardar(objeto)
        except Exception:
            registro.exception("No se pudo guardar la actualizacion de %s", tablero_id)
            self._auditar(contexto, "actualizacion", tablero_id, "error", "falló al guardar; los datos anteriores se conservan", ip)
            raise
        huellas = ", ".join(f"{a.clave}:{a.huella[:12]}" for a in archivos)
        self._auditar(contexto, "actualizacion", tablero_id, "ok", f"{len(archivos)} archivo(s) [{huellas}] · " + "; ".join(f"{e}: {v}" for e, v in resumen)[:600], ip)
        return self._dto(tablero_id, [], advertencias, resumen, archivos, aplicada=True)
