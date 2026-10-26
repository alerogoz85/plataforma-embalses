import { TableroModelo } from "@/components/modelos/TableroModelo";

/** Tablero del modelo «Riesgo de apagón»: ficha documentada y, cuando existan, sus resultados importados. */
export default function Page() {
  return <TableroModelo modeloId="apagon" titulo="Riesgo de apagón condicionado por ENOS" />;
}
