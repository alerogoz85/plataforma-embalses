import { Suspense } from "react";

import { TableroApagon } from "@/components/apagon/TableroApagon";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Tablero «Riesgo de apagón»: visor interactivo con los escenarios del modelo (los controles viven en la URL) o, sin ellos, la ficha documentada. */
export default function Page() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Riesgo de apagón condicionado por ENOS" />}>
      <TableroApagon />
    </Suspense>
  );
}
