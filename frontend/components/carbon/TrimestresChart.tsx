"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { ResumenCarbon } from "@/lib/api/types";
import { etiquetaTrimestre } from "@/lib/utils/carbon";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_CARBON } from "./ayudasCarbon";
import { ErrorCarbon } from "./ErrorCarbon";
import { ESTILO_TICK, ESTILO_TOOLTIP } from "./EstiloGrafico";

/** Millones de toneladas (Mt) esperadas por trimestre, con su rango P10-P90 en la tabla. Los trimestres parciales se atenuan. */
export function TrimestresChart({ resumen }: { resumen: { datos: ResumenCarbon | null; error: string | null } }) {
  const { datos, error } = resumen;
  if (error) return <ErrorCarbon que="los trimestres" mensaje={error} />;
  if (!datos) return <SkeletonChart />;

  const filas = datos.trimestres.map((t) => ({
    ...t,
    etiqueta: etiquetaTrimestre(t.trimestre),
    p50: t.carbon_mt.p50,
  }));

  return (
    <Card>
      <CardHeader title="Consumo por trimestre (Mt)" subtitle="Escenario central P50 · rango P10–P90 en la tabla" ayuda={AYUDAS_CARBON.trimestres} />
      <div className="h-56 w-full px-2 pt-4 sm:px-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={filas} margin={{ top: 4, right: 8, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="etiqueta" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
            <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={40} />
            <Tooltip {...ESTILO_TOOLTIP} formatter={(v) => (typeof v === "number" ? `${formatearNumero(v, 2)} Mt` : String(v))} />
            <Bar dataKey="p50" name="P50 (Mt)" radius={[6, 6, 0, 0]} isAnimationActive={false}>
              {filas.map((f) => (
                <Cell key={f.trimestre} fill="var(--chart-volumen)" fillOpacity={f.dentro_del_horizonte ? 1 : 0.35} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="overflow-x-auto px-5 pb-5 pt-2">
        <table className="w-full text-sm tabular-nums">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wide text-foreground-muted">
              <th className="py-1.5 pr-3 font-semibold">Trimestre</th>
              <th className="py-1.5 pr-3 text-right font-semibold">P10</th>
              <th className="py-1.5 pr-3 text-right font-semibold">P50</th>
              <th className="py-1.5 text-right font-semibold">P90</th>
            </tr>
          </thead>
          <tbody>
            {filas.map((f) => (
              <tr key={f.trimestre} className="border-t border-border">
                <td className="py-1.5 pr-3">
                  {f.etiqueta}
                  {!f.dentro_del_horizonte && <span className="ml-2 text-[11px] text-foreground-muted">parcial ({f.meses} {f.meses === 1 ? "mes" : "meses"})</span>}
                </td>
                <td className="py-1.5 pr-3 text-right">{formatearNumero(f.carbon_mt.p10, 2)}</td>
                <td className="py-1.5 pr-3 text-right font-semibold">{formatearNumero(f.carbon_mt.p50, 2)}</td>
                <td className="py-1.5 text-right">{formatearNumero(f.carbon_mt.p90, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
