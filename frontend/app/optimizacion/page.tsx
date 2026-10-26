import { Suspense } from "react";

import { TableroModelo } from "@/components/modelos/TableroModelo";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Tablero del modelo «Optimización hidrotérmica»: ficha documentada y, cuando existan, sus resultados importados (el período vive en la URL). */
export default function Page() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Optimización hidrotérmica (SDDP)" />}>
      <TableroModelo modeloId="optimizacion" titulo="Optimización hidrotérmica (SDDP)" />
    </Suspense>
  );
}
