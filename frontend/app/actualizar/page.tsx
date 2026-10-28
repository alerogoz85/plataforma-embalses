import { Suspense } from "react";

import { ModuloActualizacion } from "@/components/actualizacion/ModuloActualizacion";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Módulo de actualización de tableros (carga de archivos con sesión; el tablero elegido vive en la URL: `?tablero=gas`). */
export default function Page() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Actualizar los tableros" />}>
      <ModuloActualizacion />
    </Suspense>
  );
}
