import { Card } from "@/components/ui/Card";

/** Aviso de fallo de un bloque del tablero. El 404 de «modelo no cargado» trae ya la instruccion para corregirlo. */
export function ErrorCarbon({ que, mensaje }: { que: string; mensaje: string }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-critico">
        No fue posible cargar {que}: {mensaje}
      </p>
    </Card>
  );
}
