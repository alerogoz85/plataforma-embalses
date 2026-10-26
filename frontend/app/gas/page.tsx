import { Suspense } from "react";

import { TableroModelo } from "@/components/modelos/TableroModelo";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Tablero del modelo «Gas natural»: ficha documentada y, cuando existan, sus resultados importados (el período vive en la URL). */
export default function Page() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Gas natural: oferta declarada y fiscalizada" />}>
      <TableroModelo modeloId="gas" titulo="Gas natural: oferta declarada y fiscalizada" />
    </Suspense>
  );
}
