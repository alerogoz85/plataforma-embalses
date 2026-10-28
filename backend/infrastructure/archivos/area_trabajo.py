"""Carpeta temporal privada donde se ubican los archivos recibidos con la estructura que espera cada lector.

La ruta de cada archivo sale del catalogo (nunca del nombre que envia el navegador) y se comprueba que queda DENTRO de la carpeta.
La carpeta se crea con permisos solo para el propietario y se borra siempre al terminar, haya o no error."""
from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from domain.entities.actualizacion import ArchivoRecibido, TableroActualizable


class AreaTemporal:
    @contextmanager
    def preparar(self, definicion: TableroActualizable, archivos: list[ArchivoRecibido]) -> Iterator[Path]:
        raiz = Path(tempfile.mkdtemp(prefix="actualizacion_")).resolve()
        try:
            raiz.chmod(0o700)
            por_clave = {a.clave: a for a in definicion.archivos}
            for recibido in archivos:
                requerido = por_clave[recibido.clave]
                relativa = Path(requerido.ruta) / recibido.nombre if requerido.patron_nombre else Path(requerido.ruta)
                destino = (raiz / relativa).resolve()
                if raiz not in destino.parents:
                    raise ValueError("Ruta de destino fuera del area de trabajo")
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_bytes(recibido.contenido)
            yield raiz
        finally:
            shutil.rmtree(raiz, ignore_errors=True)
