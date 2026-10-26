"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import type { TablaModelo } from "@/lib/api/types";
import { formatearNumero } from "@/lib/utils/formatters";

const formatear = (v: string | number | null) => (v === null ? "—" : typeof v === "number" ? formatearNumero(v, Number.isInteger(v) ? 0 : 2) : v);

/** Tabla tal como la dejó el modelo. Una celda vacía se muestra como «—» (dato no entregado), nunca como cero. */
export function TablaModeloCard({ tabla }: { tabla: TablaModelo }) {
  return (
    <Card>
      <CardHeader title={tabla.titulo} />
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
            {tabla.filas.length === 0 ? (
              <tr>
                <td colSpan={tabla.columnas.length} className="py-6 text-center text-foreground-muted">
                  Sin filas.
                </td>
              </tr>
            ) : (
              tabla.filas.map((fila, i) => (
                <tr key={i} className="border-t border-border">
                  {fila.map((v, j) => (
                    <td key={j} className="py-1.5 pr-3">
                      {formatear(v)}
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
