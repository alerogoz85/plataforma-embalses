import { Suspense } from "react";

import { TableroCarbon } from "@/components/carbon/TableroCarbon";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Tablero del modelo de carbón térmico. Sus filtros viven en la URL, por eso el contenido va dentro de un `Suspense`. */
export default function CarbonPage() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Modelo de carbón térmico" />}>
      <TableroCarbon />
    </Suspense>
  );
}
