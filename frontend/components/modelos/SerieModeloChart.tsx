"use client";

import { useMemo } from "react";
import { Area, Bar, BarChart, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import type { SerieModelo } from "@/lib/api/types";
import { construirPuntosModelo, tieneBanda } from "@/lib/utils/modelos";
import { formatearNumero } from "@/lib/utils/formatters";

const TICK = { fontSize: 11, fill: "var(--foreground-muted)" } as const;
const TOOLTIP = {
  contentStyle: { background: "var(--background-elevated)", border: "1px solid var(--border)", borderRadius: 12, fontSize: 12 },
  labelStyle: { color: "var(--foreground)", fontWeight: 600 },
} as const;

/** Un gráfico por serie del modelo: línea (con banda P10-P90 si la trae) o barras. Ya llega recortado por los filtros. */
export function SerieModeloChart({ serie }: { serie: SerieModelo }) {
  const puntos = useMemo(() => construirPuntosModelo(serie.puntos), [serie.puntos]);
  const banda = tieneBanda(serie.puntos);
  const formato = (v: unknown) => (typeof v === "number" ? `${formatearNumero(v, 2)} ${serie.unidad}` : String(v));

  return (
    <Card>
      <CardHeader title={serie.titulo} subtitle={`${serie.unidad}${banda ? " · banda: escenarios P10–P90" : ""}`} />
      {puntos.length === 0 ? (
        <p className="px-5 py-10 text-center text-sm text-foreground-muted">Sin datos en el período elegido.</p>
      ) : (
        <div className="h-64 w-full px-2 pb-3 pt-3 sm:px-4" role="img" aria-label={`Gráfico: ${serie.titulo}`}>
          <ResponsiveContainer width="100%" height="100%">
            {serie.tipo === "barras" ? (
              <BarChart data={puntos} margin={{ top: 6, right: 10, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="etiqueta" tick={TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={16} />
                <YAxis tick={TICK} tickLine={false} axisLine={false} width={48} />
                <Tooltip {...TOOLTIP} formatter={formato} />
                <Bar dataKey="valor" name={serie.titulo} fill="var(--chart-volumen)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
              </BarChart>
            ) : (
              <ComposedChart data={puntos} margin={{ top: 6, right: 10, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="etiqueta" tick={TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={16} />
                <YAxis tick={TICK} tickLine={false} axisLine={false} width={48} />
                <Tooltip {...TOOLTIP} formatter={formato} />
                {banda && <Legend wrapperStyle={{ fontSize: 12 }} />}
                {banda && <Area dataKey="bandaBase" stackId="banda" stroke="none" fill="transparent" legendType="none" isAnimationActive={false} />}
                {banda && <Area dataKey="bandaRango" stackId="banda" stroke="none" fill="var(--chart-banda)" name="Escenarios P10–P90" isAnimationActive={false} />}
                <Line type="monotone" dataKey="valor" name={banda ? "Valor central (P50)" : serie.titulo} stroke="var(--chart-volumen)" strokeWidth={2.5} dot={puntos.length <= 24} isAnimationActive={false} />
              </ComposedChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
