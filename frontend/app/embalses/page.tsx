import { Suspense } from "react";

import { TableroEmbalses } from "@/components/dashboard/TableroEmbalses";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Tablero de embalses. Sus filtros viven en la URL, por eso el contenido va dentro de un `Suspense`. */
export default function EmbalsesPage() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Monitoreo y predicción de embalses" />}>
      <TableroEmbalses />
    </Suspense>
  );
}
