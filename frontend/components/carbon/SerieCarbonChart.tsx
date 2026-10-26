"use client";

import { useMemo } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { useSerieCarbon } from "@/lib/hooks/useCarbon";
import type { HistoriaCarbon, HorizonteCarbon, UnidadCarbon } from "@/lib/api/types";
import { ETIQUETA_UNIDAD, construirPuntosSerie, convertirConsumo, decimalesUnidad, etiquetaMesCarbon } from "@/lib/utils/carbon";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_CARBON } from "./ayudasCarbon";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { COLOR_RECORD, COLOR_TECHO, ESTILO_TICK, ESTILO_TOOLTIP } from "./EstiloGrafico";

interface SerieCarbonChartProps {
  historia: HistoriaCarbon;
  horizonte: HorizonteCarbon;
  unidad: UnidadCarbon;
}

/**
 * Grafico principal: consumo mensual observado + proyeccion P50 con banda P10-P90, y el techo
 * termico y el record historico como referencias. Sigue los filtros de historia, horizonte y unidad.
 */
export function SerieCarbonChart({ historia, horizonte, unidad }: SerieCarbonChartProps) {
  const { datos: serie, error } = useSerieCarbon(historia, horizonte);
  const puntos = useMemo(() => (serie ? construirPuntosSerie(serie, unidad) : []), [serie, unidad]);

  if (error) return <ErrorBloque que="la serie de consumo" mensaje={error} />;
  if (!serie) return <SkeletonChart />;

  const pc = serie.poder_calorifico_mbtu_t;
  const d = decimalesUnidad(unidad);
  const techo = convertirConsumo(serie.techo_gbtu_dia, unidad, pc);
  const record = convertirConsumo(serie.maximo_historico_gbtu_dia, unidad, pc);
  const parcial = serie.proyeccion.find((p) => p.observado_parcial_gbtu_dia !== null);

  return (
    <Card>
      <CardHeader
        title={`Consumo de carbón térmico (${ETIQUETA_UNIDAD[unidad]})`}
        subtitle={`Historia mensual y proyección a ${serie.horizonte_meses} ${serie.horizonte_meses === 1 ? "mes" : "meses"} · escenarios P10–P90`}
        ayuda={AYUDAS_CARBON.graficoPrincipal}
      />
      <div className="h-96 w-full px-2 pb-2 pt-4 sm:px-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={puntos} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="mesLabel" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={28} />
            <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={52} domain={[0, (max: number) => Math.ceil(Math.max(max, techo) * 1.05)]} />
            <Tooltip {...ESTILO_TOOLTIP} formatter={(v) => (typeof v === "number" ? formatearNumero(v, d) : String(v))} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area dataKey="bandaBase" stackId="banda" stroke="none" fill="transparent" legendType="none" isAnimationActive={false} />
            <Area dataKey="bandaRango" stackId="banda" stroke="none" fill="var(--chart-banda)" name="Escenarios P10–P90" isAnimationActive={false} />
            <Line type="monotone" dataKey="observado" name="Consumo observado" stroke="var(--chart-volumen)" strokeWidth={2.5} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="p50" name="Proyección P50" stroke="var(--chart-prediccion)" strokeWidth={2.5} strokeDasharray="6 4" dot={false} isAnimationActive={false} />
            <ReferenceLine y={techo} stroke={COLOR_TECHO} strokeDasharray="4 4" ifOverflow="extendDomain" label={{ value: `Techo ${formatearNumero(techo, d)}`, position: "insideTopLeft", fill: COLOR_TECHO, fontSize: 11 }} />
            <ReferenceLine y={record} stroke={COLOR_RECORD} strokeDasharray="2 4" ifOverflow="extendDomain" label={{ value: `Récord ${formatearNumero(record, d)}`, position: "insideBottomLeft", fill: COLOR_RECORD, fontSize: 11 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {parcial && (
        <p className="px-5 pb-4 text-xs text-foreground-muted">
          {etiquetaMesCarbon(parcial.fecha)} está en curso: lo observado hasta hoy es{" "}
          {formatearNumero(convertirConsumo(parcial.observado_parcial_gbtu_dia as number, unidad, pc), d)} {ETIQUETA_UNIDAD[unidad]} y no se dibuja como mes observado.
        </p>
      )}
    </Card>
  );
}
