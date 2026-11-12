"use client";

import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { RegionResumen } from "@/lib/api/types";
import { AYUDAS } from "./ayudas";
import { COLOR_VAR_RIESGO, formatearPorcentaje } from "@/lib/utils/formatters";
import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonChart } from "@/components/ui/Skeleton";

export function RegionBarChart({
  regiones,
  cargando,
  regionSeleccionada = null,
  onSeleccionar,
}: {
  regiones: RegionResumen[];
  cargando: boolean;
  regionSeleccionada?: string | null;
  /** Con esta funcion las barras filtran el tablero: un clic elige la region y otro sobre la misma la quita. */
  onSeleccionar?: (region: string | null) => void;
}) {
  if (cargando && regiones.length === 0) return <SkeletonChart />;

  const datos = [...regiones].sort((a, b) => a.pct_volumen_util - b.pct_volumen_util);

  return (
    <Card>
      <CardHeader
        ayuda={AYUDAS.distribucionRegional}
        title="Distribución regional del %V. útil"
        subtitle={
          onSeleccionar
            ? "Subsistemas de menor a mayor · haz clic en una barra para filtrar el tablero"
            : "Subsistemas hidrológicos ordenados de menor a mayor"
        }
      />
      <div className="h-72 w-full px-2 pb-4 pt-4 sm:px-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={datos} layout="vertical" margin={{ left: 8, right: 24 }}>
            <XAxis type="number" domain={[0, (maximo: number) => Math.max(100, Math.ceil(maximo))]} hide />
            <YAxis
              dataKey="region"
              type="category"
              width={80}
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 12, fill: "var(--foreground)" }}
            />
            <Tooltip
              cursor={{ fill: "var(--border)", opacity: 0.4 }}
              contentStyle={{
                background: "var(--background-elevated)",
                border: "1px solid var(--border)",
                borderRadius: 12,
                fontSize: 12,
              }}
              formatter={(valor) => [formatearPorcentaje(Number(valor)), "% Vol. útil"]}
            />
            <Bar dataKey="pct_volumen_util" radius={[0, 8, 8, 0]} barSize={22} isAnimationActive={false}>
              {datos.map((region) => (
                <Cell
                  key={region.region}
                  fill={COLOR_VAR_RIESGO[region.nivel_riesgo].texto}
                  fillOpacity={regionSeleccionada && regionSeleccionada !== region.region ? 0.35 : 1}
                  cursor={onSeleccionar ? "pointer" : undefined}
                  onClick={onSeleccionar ? () => onSeleccionar(regionSeleccionada === region.region ? null : region.region) : undefined}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
