"use client";

import { useMemo } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import type { GraficoModelo } from "@/lib/api/types";
import { formatearNumero } from "@/lib/utils/formatters";
import { construirDatosGrafico } from "@/lib/utils/modelos";

const TICK = { fontSize: 11, fill: "var(--foreground-muted)" } as const;
const TOOLTIP = {
  contentStyle: { background: "var(--background-elevated)", border: "1px solid var(--border)", borderRadius: 12, fontSize: 12 },
  labelStyle: { color: "var(--foreground)", fontWeight: 600 },
} as const;
/** Colores de las líneas por orden: la primera (lo observado) en el azul de marca; las demás se distinguen también por el trazo. */
const COLORES = ["var(--chart-volumen)", "var(--color-alerta)", "var(--color-critico)", "var(--color-optimo)", "var(--foreground-muted)"];

/** Gráfico con varias líneas (observado, pronóstico con banda, referencias). Ya llega filtrado por campo, variable y período. */
export function GraficoModeloChart({ grafico }: { grafico: GraficoModelo }) {
  const { datos, lineas } = useMemo(() => construirDatosGrafico(grafico), [grafico]);
  const formato = (v: unknown) => (typeof v === "number" ? `${formatearNumero(v, 1)} ${grafico.unidad}` : String(v));

  return (
    <Card>
      <CardHeader title={grafico.titulo} subtitle={grafico.unidad + (lineas.some((l) => l.banda) ? " · banda: intervalo o escenarios P10–P90" : "")} />
      {datos.length === 0 ? (
        <p className="px-5 py-10 text-center text-sm text-foreground-muted">Sin datos en el período elegido.</p>
      ) : (
        <div className="h-72 w-full px-2 pb-3 pt-3 sm:px-4" role="img" aria-label={`Gráfico: ${grafico.titulo}. Líneas: ${lineas.map((l) => l.nombre).join(", ")}`}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={datos} margin={{ top: 6, right: 10, left: 4, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="etiqueta" tick={TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={20} />
              <YAxis tick={TICK} tickLine={false} axisLine={false} width={52} />
              <Tooltip {...TOOLTIP} formatter={formato} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {lineas.map((l) =>
                l.banda ? (
                  <Area key={`${l.clave}_base`} dataKey={`${l.clave}_base`} stackId={`banda_${l.clave}`} stroke="none" fill="transparent" legendType="none" isAnimationActive={false} />
                ) : null,
              )}
              {lineas.map((l, i) =>
                l.banda ? (
                  <Area key={`${l.clave}_rango`} dataKey={`${l.clave}_rango`} stackId={`banda_${l.clave}`} stroke="none" fill={COLORES[i % COLORES.length]} fillOpacity={0.15} name={`${l.nombre}: banda`} legendType="none" isAnimationActive={false} />
                ) : null,
              )}
              {lineas.map((l, i) => (
                <Line
                  key={l.clave}
                  type="monotone"
                  dataKey={l.clave}
                  name={l.nombre}
                  stroke={COLORES[i % COLORES.length]}
                  strokeWidth={i === 0 ? 2.5 : 2}
                  strokeDasharray={l.estilo === "punteada" ? "6 4" : undefined}
                  dot={datos.length <= 24}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  );
}
