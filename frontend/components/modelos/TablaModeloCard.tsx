"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import type { TablaModelo } from "@/lib/api/types";
import { formatearNumero } from "@/lib/utils/formatters";
import { SEMAFOROS } from "@/lib/utils/modelos";

const formatear = (v: string | number | null) => (v === null ? "—" : typeof v === "number" ? formatearNumero(v, Number.isInteger(v) ? 0 : 2) : v);

/** Celda: el semáforo («Verde», «Amarillo», «Rojo») se pinta como insignia con su texto; el resto, como valor. */
function Celda({ valor }: { valor: string | number | null }) {
  const semaforo = typeof valor === "string" ? SEMAFOROS[valor] : undefined;
  if (!semaforo) return <>{formatear(valor)}</>;
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold" style={{ color: semaforo.color, backgroundColor: semaforo.fondo }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: semaforo.color }} aria-hidden="true" />
      {valor}
    </span>
  );
}

/** Tabla tal como la dejó el modelo. Una celda vacía se muestra como «—» (dato no entregado), nunca como cero. */
export function TablaModeloCard({ tabla, filas = tabla.filas }: { tabla: TablaModelo; /** Filas a mostrar (por defecto, todas); la página pasa las que corresponden a los filtros. */ filas?: TablaModelo["filas"] }) {
  return (
    <Card>
      <CardHeader title={tabla.titulo} subtitle={filas.length !== tabla.filas.length ? `${filas.length} de ${tabla.filas.length} filas según los filtros` : undefined} />
      <div className="max-h-96 overflow-auto px-5 pb-4 pt-3">
        <table className="w-full text-sm tabular-nums">
          <caption className="sr-only">{tabla.titulo}</caption>
          <thead className="sticky top-0 bg-background-elevated">
            <tr className="text-left text-[11px] uppercase tracking-wide text-foreground-muted">
              {tabla.columnas.map((c) => (
                <th key={c} scope="col" className="py-1.5 pr-3 font-semibold">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filas.length === 0 ? (
              <tr>
                <td colSpan={tabla.columnas.length} className="py-6 text-center text-foreground-muted">
                  Sin filas.
                </td>
              </tr>
            ) : (
              filas.map((fila, i) => (
                <tr key={i} className="border-t border-border">
                  {fila.map((v, j) => (
                    <td key={j} className="py-1.5 pr-3">
                      <Celda valor={v} />
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {tabla.nota && <p className="px-5 pb-4 text-xs text-foreground-muted">{tabla.nota}</p>}
    </Card>
  );
}
