"""Descompresion segura de archivos .gz. Los CSV grandes (p. ej. los eventos del modelo DNS, ~6 MB) no caben en el limite de una peticion de
Vercel (4,5 MB); el navegador los comprime antes de enviarlos y aqui se descomprimen con tope de tamaño (contra bombas de compresion)."""
from __future__ import annotations

import zlib


class GzipInvalidoError(ValueError):
    pass


def descomprimir_gzip(datos: bytes, maximo: int) -> bytes:
    """Descomprime sin pasar de `maximo` bytes: lo que excede se rechaza sin llegar a descomprimirse entero."""
    if not datos.startswith(b"\x1f\x8b"):
        raise GzipInvalidoError("no es un archivo .gz válido")
    descompresor = zlib.decompressobj(wbits=31)
    try:
        salida = descompresor.decompress(datos, maximo + 1)
        if descompresor.unconsumed_tail or not descompresor.eof and len(salida) > maximo:
            raise GzipInvalidoError("al descomprimirse supera el tamaño máximo permitido")
        if not descompresor.eof:
            raise GzipInvalidoError("el archivo .gz está incompleto o dañado")
    except zlib.error as error:
        raise GzipInvalidoError("el archivo .gz está dañado") from error
    if len(salida) > maximo:
        raise GzipInvalidoError("al descomprimirse supera el tamaño máximo permitido")
    return salida
