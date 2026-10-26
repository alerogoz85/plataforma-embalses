import { Suspense } from "react";

import { TableroDns } from "@/components/dns/TableroDns";
import { CargandoTablero } from "@/components/ui/CargandoTablero";

/** Tablero de demanda no atendida. Sus filtros viven en la URL, por eso el contenido va dentro de un `Suspense`. */
export default function DnsPage() {
  return (
    <Suspense fallback={<CargandoTablero titulo="Demanda no atendida (DNS)" />}>
      <TableroDns />
    </Suspense>
  );
}
