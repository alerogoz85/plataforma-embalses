"use client";

import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { PatronesDns } from "@/lib/api/types";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_DNS } from "./ayudasDns";
import { COLOR_NO_PROGRAMADA, COLOR_PROGRAMADA, ESTILO_TICK, ESTILO_TOOLTIP } from "./EstiloGraficoDns";

/** Cuándo ocurren los eventos: por hora del día, por día de la semana y composición programada/no programada por franja. */
export function PatronesDnsChart({ patrones }: { patrones: { datos: PatronesDns | null; error: string | null } }) {
  const { datos } = patrones;
  const porHora = useMemo(() => (datos?.por_hora ?? []).map((n, h) => ({ hora: `${h}h`, eventos: n })), [datos]);
  const porDia = useMemo(() => (datos?.dias ?? []).map((d, i) => ({ dia: d.slice(0, 3), eventos: datos!.por_dia_semana[i] })), [datos]);
  const franjas = useMemo(
    () =>
      (datos?.franjas ?? []).map((f) => {
        const total = f.no_programada + f.programada;
        return {
          franja: f.franja.replace(/ \(.*\)$/, ""),
          noProgramada: total ? (f.no_programada / total) * 100 : 0,
          programada: total ? (f.programada / total) * 100 : 0,
        };
      }),
    [datos],
  );

  if (patrones.error) return <ErrorBloque que="los patrones" mensaje={patrones.error} />;
  if (!datos) return <SkeletonChart />;

  const horaPico = datos.por_hora.indexOf(Math.max(...datos.por_hora));
  const sinDatos = datos.eventos_usados === 0;

  return (
    <Card>
      <CardHeader
        title="Patrones en el tiempo"
        subtitle={sinDatos ? "Sin eventos con hora conocida en este filtro" : `Hora con más eventos: ${horaPico}h · ${formatearNumero(datos.eventos_usados, 0)} eventos con hora conocida`}
        ayuda={AYUDAS_DNS.patrones}
      />
      <div className="grid grid-cols-1 gap-4 px-2 pb-2 pt-4 sm:px-4 lg:grid-cols-3">
        <figure className="h-56" aria-label="Eventos por hora del día">
          <figcaption className="px-2 text-xs font-semibold text-foreground-muted">Por hora del día</figcaption>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={porHora} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="hora" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} interval={2} />
              <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={36} />
              <Tooltip {...ESTILO_TOOLTIP} />
              <Bar dataKey="eventos" name="Eventos" fill="var(--chart-volumen)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </figure>
        <figure className="h-56" aria-label="Eventos por día de la semana">
          <figcaption className="px-2 text-xs font-semibold text-foreground-muted">Por día de la semana</figcaption>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={porDia} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="dia" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
              <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={36} />
              <Tooltip {...ESTILO_TOOLTIP} />
              <Bar dataKey="eventos" name="Eventos" fill="var(--chart-volumen)" radius={[3, 3, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </figure>
        <figure className="h-56" aria-label="Origen de los eventos por franja del día">
          <figcaption className="px-2 text-xs font-semibold text-foreground-muted">Origen por franja del día (%)</figcaption>
          <ResponsiveContainer width="100%" height="90%">
            <BarChart data={franjas} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="franja" tick={ESTILO_TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} />
              <YAxis tick={ESTILO_TICK} tickLine={false} axisLine={false} width={36} unit="%" domain={[0, 100]} />
              <Tooltip {...ESTILO_TOOLTIP} formatter={(v) => (typeof v === "number" ? `${formatearNumero(v, 0)} %` : String(v))} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="noProgramada" name="No programada" stackId="origen" fill={COLOR_NO_PROGRAMADA} isAnimationActive={false} />
              <Bar dataKey="programada" name="Programada" stackId="origen" fill={COLOR_PROGRAMADA} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </figure>
      </div>
      <p className="px-5 pb-4 text-xs text-foreground-muted">
        Se excluyen {formatearNumero(datos.eventos_hora_desconocida, 0)} eventos con hora desconocida (00:00:00 exacto, valor por defecto de SIMEM: no es un pico de medianoche).
      </p>
    </Card>
  );
}
