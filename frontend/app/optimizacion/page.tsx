import { TableroModelo } from "@/components/modelos/TableroModelo";

/** Tablero del modelo «Optimización hidrotérmica»: ficha documentada y, cuando existan, sus resultados importados. */
export default function Page() {
  return <TableroModelo modeloId="optimizacion" titulo="Optimización hidrotérmica (SDDP)" />;
}
