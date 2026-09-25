"use client";

import { useMemo, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useEmbalseDetalle } from "@/lib/hooks/useEmbalseDetalle";
import { usePrediccion } from "@/lib/hooks/usePrediccion";
import { formatearFechaCorta } from "@/lib/utils/formatters";
import { Card, CardHeader } from "@/components/ui/Card";
import { InfoButton } from "@/components/ui/InfoButton";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { AYUDAS } from "./ayudas";
import { HORIZONTES_PREDICCION, type HorizontePrediccion } from "@/lib/api/types";

interface PuntoGrafico {
  fecha: string;
  fechaLabel: string;
  pctVolumenUtil?: number;
  aportesPctMedia?: number | null;
  prediccion?: number;
  bandaBase?: number;
  bandaRango?: number;
}

export function MainChart({
  embalseId,
  nombreEmbalse,
  fechaInicio,
  fechaFin,
}: {
  embalseId: string | null;
  nombreEmbalse: string;
  fechaInicio: string;
  fechaFin: string;
}) {
  const [horizonte, setHorizonte] = useState<HorizontePrediccion>(30);
  const detalle = useEmbalseDetalle(embalseId, { fechaInicio, fechaFin });
  const prediccion = usePrediccion(embalseId, horizonte);
  const esOutputs = prediccion.datos?.origen === "outputs";

  const datos = useMemo<PuntoGrafico[]>(() => {
    const serie = detalle.datos?.serie_historica ?? [];
    const puntosHistoricos: PuntoGrafico[] = serie.map((p) => ({
      fecha: p.fecha,
      fechaLabel: formatearFechaCorta(p.fecha),
      pctVolumenUtil: p.pct_volumen_util,
      aportesPctMedia: p.aportes_pct_media,
    }));

    const puntosPrediccion = prediccion.datos?.puntos ?? [];
    if (puntosPrediccion.length === 0 || puntosHistoricos.length === 0) {
      return puntosHistoricos;
    }

    const ultimoHistorico = puntosHistoricos[puntosHistoricos.length - 1];
    const puentePrediccion: PuntoGrafico = {
      ...ultimoHistorico,
      prediccion: ultimoHistorico.pctVolumenUtil,
      bandaBase: ultimoHistorico.pctVolumenUtil,
      bandaRango: 0,
    };

    const puntosFuturos: PuntoGrafico[] = puntosPrediccion.map((p) => ({
      fecha: p.fecha,
      fechaLabel: formatearFechaCorta(p.fecha),
      prediccion: p.valor_esperado,
      bandaBase: p.limite_inferior,
      bandaRango: Math.max(0, p.limite_superior - p.limite_inferior),
    }));

    return [...puntosHistoricos.slice(0, -1), puentePrediccion, ...puntosFuturos];
  }, [detalle.datos, prediccion.datos]);

  if (!embalseId) {
    return (
      <Card className="flex h-full min-h-[22rem] items-center justify-center p-8 text-center">
        <p className="text-sm text-foreground-muted">
          Selecciona un embalse en los filtros para ver su curva histórica y proyección.
        </p>
      </Card>
    );
  }

  if (detalle.cargando && !detalle.datos) {
    return <SkeletonChart />;
  }

  if (detalle.error) {
    return (
      <Card className="p-5">
        <p className="text-sm text-critico">No fue posible cargar la serie histórica: {detalle.error}</p>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader
        ayuda={AYUDAS.graficoPrincipal}
        title={`${nombreEmbalse} — %V. útil vs. aportes y proyección ML`}
        subtitle={
          prediccion.datos
            ? esOutputs
              ? `${prediccion.datos.metodo} · escenarios P10–P90`
              : `${prediccion.datos.metodo} · IC ${Math.round((prediccion.datos.nivel_confianza ?? 0.95) * 100)}%`
            : "Cargando modelo de pronóstico…"
        }
        action={
          <div className="flex items-center gap-1.5">
            <InfoButton titulo={AYUDAS.horizonteDiario.titulo}>{AYUDAS.horizonteDiario.contenido}</InfoButton>
            <div className="flex gap-1 rounded-lg border border-border p-0.5">
              {HORIZONTES_PREDICCION.map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizonte(h)}
                  className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                    horizonte === h
                      ? "bg-marca text-white"
                      : "text-foreground-muted hover:text-foreground"
                  }`}
                  style={horizonte === h ? { backgroundColor: "var(--color-marca)" } : undefined}
                >
                  {h / 30}m
                </button>
              ))}
            </div>
          </div>
        }
      />
      <div className="h-80 w-full px-2 pb-4 pt-4 sm:px-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={datos} margin={{ top: 4, right: 8, left: 4, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis
              dataKey="fechaLabel"
              tick={{ fontSize: 11, fill: "var(--foreground-muted)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--border)" }}
              minTickGap={32}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--foreground-muted)" }}
              tickLine={false}
              axisLine={false}
              unit="%"
              width={48}
            />
            <Tooltip
              contentStyle={{
                background: "var(--background-elevated)",
                border: "1px solid var(--border)",
                borderRadius: 12,
                fontSize: 12,
              }}
              labelStyle={{ color: "var(--foreground)", fontWeight: 600 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area
              dataKey="bandaBase"
              stackId="banda"
              stroke="none"
              fill="transparent"
              legendType="none"
              isAnimationActive={false}
            />
            <Area
              dataKey="bandaRango"
              stackId="banda"
              stroke="none"
              fill="var(--chart-banda)"
              name={esOutputs ? "Escenarios P10–P90 (ENSO)" : "Intervalo de confianza 95%"}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="pctVolumenUtil"
              name="% Volumen útil"
              stroke="var(--chart-volumen)"
              strokeWidth={2.5}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="aportesPctMedia"
              name="Aportes (% media histórica)"
              stroke="var(--chart-aportes)"
              strokeWidth={1.5}
              strokeOpacity={0.7}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="prediccion"
              name="Proyección %V. útil"
              stroke="var(--chart-prediccion)"
              strokeWidth={2.5}
              strokeDasharray="6 4"
              dot={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
