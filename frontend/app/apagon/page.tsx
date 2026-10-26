import { Suspense } from "react";

import { TableroModelo } from "@/components/modelos/TableroModelo";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Tablero del modelo «Riesgo de apagón»: ficha documentada y, cuando existan, sus resultados importados (el período vive en la URL). */
export default function Page() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Riesgo de apagón condicionado por ENOS" />}>
      <TableroModelo modeloId="apagon" titulo="Riesgo de apagón condicionado por ENOS" />
    </Suspense>
  );
}
