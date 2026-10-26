"use client";

import { useMemo } from "react";
import { Area, CartesianGrid, ComposedChart, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { useComparacionXm } from "@/lib/hooks/useCarbon";
import type { HorizonteCarbon, UnidadCarbon } from "@/lib/api/types";
import { ETIQUETA_UNIDAD, construirPuntosXm, convertirConsumo, decimalesUnidad } from "@/lib/utils/carbon";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_CARBON } from "./ayudasCarbon";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { COLOR_TECHO, COLOR_XM, ESTILO_TICK, ESTILO_TOOLTIP } from "./EstiloGrafico";

interface ComparacionXmChartProps {
  horizonte: HorizonteCarbon;
  unidad: UnidadCarbon;
  poderCalorifico: number | null;
}

/** Modelo (P50 y banda) frente al caso estocastico de XM; avisa los meses en que XM supera el techo fisico. */
export function ComparacionXmChart({ horizonte, unidad, poderCalorifico }: ComparacionXmChartProps) {
  const { datos, error } = useComparacionXm(horizonte);
  const puntos = useMemo(() => (datos && poderCalorifico ? construirPuntosXm(datos, unidad, poderCalorifico) : []), [datos, unidad, poderCalorifico]);

  if (error) return <ErrorBloque que="la comparación con XM" mensaje={error} />;
  if (!datos || !poderCalorifico) return <SkeletonChart />;

  const d = decimalesUnidad(unidad);
  const techo = datos.length > 0 ? convertirConsumo(datos[0].techo_gbtu_dia, unidad, poderCalorifico) : null;
  const sobreTecho = datos.filter((f) => f.xm_estocastico_gbtu_dia !== null && f.xm_estocastico_gbtu_dia > f.techo_gbtu_dia).length;

  return (
    <Card>
      <CardHeader title={`Modelo frente a XM (${ETIQUETA_UNIDAD[unidad]})`} subtitle="Proyección P50 y banda P10–P90 del modelo; caso estocástico de XM" ayuda={AYUDAS_CARBON.comparacionXm} />
      <div className="h-64 w-full px-2 pb-2 pt-4 sm:px-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={puntos} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="mesLabel" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={16} />
            <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={52} />
            <Tooltip {...ESTILO_TOOLTIP} formatter={(v) => (typeof v === "number" ? formatearNumero(v, d) : String(v))} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area dataKey="bandaBase" stackId="banda" stroke="none" fill="transparent" legendType="none" isAnimationActive={false} />
            <Area dataKey="bandaRango" stackId="banda" stroke="none" fill="var(--chart-banda)" name="Escenarios P10–P90" isAnimationActive={false} />
            <Line type="monotone" dataKey="p50" name="Modelo P50" stroke="var(--chart-prediccion)" strokeWidth={2.5} dot={false} isAnimationActive={false} />
            <Line type="monotone" dataKey="xm" name="XM estocástico" stroke={COLOR_XM} strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive={false} />
            {techo !== null && <ReferenceLine y={techo} stroke={COLOR_TECHO} strokeDasharray="4 4" ifOverflow="extendDomain" label={{ value: "Techo", position: "insideTopLeft", fill: COLOR_TECHO, fontSize: 11 }} />}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      {sobreTecho > 0 && (
        <p className="px-5 pb-4 text-xs" style={{ color: "var(--color-alerta)" }}>
          En {sobreTecho} {sobreTecho === 1 ? "mes" : "meses"} el caso estocástico de XM supera el techo físico: consulta a XM el supuesto antes de usarlo como referencia.
        </p>
      )}
    </Card>
  );
}
