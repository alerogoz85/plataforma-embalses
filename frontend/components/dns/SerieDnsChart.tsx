"use client";

import { useMemo, useState } from "react";
import { Bar, CartesianGrid, Cell, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { SerieDns } from "@/lib/api/types";
import { ETIQUETA_MEDIDA, construirPuntosSerieDns, type MedidaDns } from "@/lib/utils/dns";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_DNS } from "./ayudasDns";
import { COLOR_PRONOSTICO, ESTILO_TICK, ESTILO_TOOLTIP } from "./EstiloGraficoDns";

/**
 * Serie mensual de eventos o de energía no atendida (el usuario alterna la medida) con el pronóstico del
 * modelo como un punto aparte. El mes del corte, que no ha terminado, se dibuja atenuado.
 */
export function SerieDnsChart({ serie }: { serie: { datos: SerieDns | null; error: string | null } }) {
  const [medida, setMedida] = useState<MedidaDns>("eventos");
  const puntos = useMemo(() => (serie.datos ? construirPuntosSerieDns(serie.datos, medida) : []), [serie.datos, medida]);

  if (serie.error) return <ErrorBloque que="la serie mensual" mensaje={serie.error} />;
  if (!serie.datos) return <SkeletonChart />;

  const decimales = medida === "eventos" ? 0 : 1;
  const p = serie.datos.pronostico;
  const parcial = serie.datos.meses.some((m) => m.parcial);

  return (
    <Card>
      <CardHeader
        title={`${ETIQUETA_MEDIDA[medida]} por mes`}
        subtitle={
          p
            ? `Pronóstico del modelo para ${p.mes}: ${formatearNumero(medida === "eventos" ? p.eventos : p.energia_gwh, decimales)} (${p.subareas} ${p.subareas === 1 ? "subárea" : "subáreas"})`
            : "Observado mensual"
        }
        ayuda={AYUDAS_DNS.serie}
        action={
          <div className="flex gap-1 rounded-lg border border-border p-0.5" role="group" aria-label="Medida del gráfico">
            {(Object.keys(ETIQUETA_MEDIDA) as MedidaDns[]).map((m) => (
              <button
                key={m}
                type="button"
                aria-pressed={medida === m}
                onClick={() => setMedida(m)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${medida === m ? "text-white" : "text-foreground-muted hover:text-foreground"}`}
                style={medida === m ? { backgroundColor: "var(--color-marca)" } : undefined}
              >
                {m === "eventos" ? "Eventos" : "Energía"}
              </button>
            ))}
          </div>
        }
      />
      <div className="h-80 w-full px-2 pb-2 pt-4 sm:px-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={puntos} margin={{ top: 8, right: 12, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="mesLabel" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={24} />
            <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={48} />
            <Tooltip {...ESTILO_TOOLTIP} formatter={(v) => (typeof v === "number" ? formatearNumero(v, decimales) : String(v))} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="valor" name={medida === "eventos" ? "Eventos observados" : "Energía observada (GWh)"} fill="var(--chart-volumen)" radius={[3, 3, 0, 0]} isAnimationActive={false}>
              {puntos.map((x) => (
                <Cell key={x.mes} fill="var(--chart-volumen)" fillOpacity={x.parcial ? 0.4 : 1} />
              ))}
            </Bar>
            <Line type="monotone" dataKey="pronostico" name="Pronóstico del modelo" stroke={COLOR_PRONOSTICO} strokeWidth={0} dot={{ r: 6, fill: COLOR_PRONOSTICO, stroke: "var(--background-elevated)", strokeWidth: 2 }} activeDot={{ r: 7 }} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="space-y-1 px-5 pb-4 text-xs text-foreground-muted">
        {parcial && <p>El último mes está atenuado: aún no termina, así que su valor es parcial.</p>}
        {serie.datos.nota_pronostico && <p>{serie.datos.nota_pronostico}</p>}
      </div>
    </Card>
  );
}
