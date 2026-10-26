"use client";

import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { useInventarioCarbon } from "@/lib/hooks/useCarbon";
import type { DiasInventario, HorizonteCarbon } from "@/lib/api/types";
import { etiquetaMesCarbon } from "@/lib/utils/carbon";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_CARBON } from "./ayudasCarbon";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { ESTILO_TICK, ESTILO_TOOLTIP } from "./EstiloGrafico";

/** kt de carbon que cubren N dias de consumo cada mes (escenario central P50 y adverso P90). Siempre en kt. */
export function InventarioChart({ horizonte, dias }: { horizonte: HorizonteCarbon; dias: DiasInventario }) {
  const { datos, error } = useInventarioCarbon(horizonte, dias);
  const filas = useMemo(() => (datos ?? []).map((f) => ({ ...f, mesLabel: etiquetaMesCarbon(f.fecha) })), [datos]);

  if (error) return <ErrorBloque que="el inventario" mensaje={error} />;
  if (!datos) return <SkeletonChart />;

  return (
    <Card>
      <CardHeader title={`Inventario requerido: ${dias} días de consumo (kt)`} subtitle="Miles de toneladas por mes · P50 central, P90 adverso" ayuda={AYUDAS_CARBON.inventario} />
      <div className="h-64 w-full px-2 pb-4 pt-4 sm:px-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={filas} margin={{ top: 4, right: 8, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="mesLabel" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={16} />
            <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={48} />
            <Tooltip {...ESTILO_TOOLTIP} formatter={(v) => (typeof v === "number" ? `${formatearNumero(v, 0)} kt` : String(v))} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="kt_p50" name="P50 (central)" fill="var(--chart-volumen)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
            <Bar dataKey="kt_p90" name="P90 (adverso)" fill="var(--color-alerta)" radius={[4, 4, 0, 0]} isAnimationActive={false} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
