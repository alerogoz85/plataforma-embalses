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

import type { EmbalseResumen } from "@/lib/api/types";
import { HORIZONTES_SENDA_VOLUMEN, ID_TOTAL_NACIONAL, type HorizonteSendaVolumen } from "@/lib/api/types";
import { useSendaVolumen } from "@/lib/hooks/useSendaVolumen";
import { formatearMes, formatearPorcentaje } from "@/lib/utils/formatters";
import { Card, CardHeader } from "@/components/ui/Card";
import { InfoButton } from "@/components/ui/InfoButton";
import { AYUDAS } from "./ayudas";
import { SkeletonChart } from "@/components/ui/Skeleton";

interface PuntoGrafico {
  mes: string;
  mesLabel: string;
  observado?: number;
  proyeccion?: number;
  bandaBase?: number;
  bandaRango?: number;
}

// Umbrales de riesgo propios de la senda de largo plazo (rojo <55%, ambar
// <65%), distintos de los umbrales OPTIMO/ALERTA/CRITICO/REBOCE que
// clasifican el %V.util del dia a dia.
function colorMinimoProyectado(valor: number): string {
  if (valor < 55) return "var(--color-critico)";
  if (valor < 65) return "var(--color-alerta)";
  return "var(--color-optimo)";
}

export function SendaVolumenPanel({ embalses }: { embalses: EmbalseResumen[] }) {
  const [embalseId, setEmbalseId] = useState<string>(ID_TOTAL_NACIONAL);
  const [horizonte, setHorizonte] = useState<HorizonteSendaVolumen>(12);
  const senda = useSendaVolumen(embalseId, horizonte);
  const esOutputs = senda.datos?.origen_proyeccion === "outputs";

  const datos = useMemo<PuntoGrafico[]>(() => {
    if (!senda.datos) return [];

    const puntosHistoricos: PuntoGrafico[] = senda.datos.historico.map((p) => ({
      mes: p.mes,
      mesLabel: formatearMes(p.mes),
      observado: p.pct_volumen_util,
    }));

    if (senda.datos.proyeccion.length === 0 || puntosHistoricos.length === 0) {
      return puntosHistoricos;
    }

    const ultimoHistorico = puntosHistoricos[puntosHistoricos.length - 1];
    const puente: PuntoGrafico = {
      ...ultimoHistorico,
      proyeccion: ultimoHistorico.observado,
      bandaBase: ultimoHistorico.observado,
      bandaRango: 0,
    };

    const puntosProyectados: PuntoGrafico[] = senda.datos.proyeccion.map((p) => ({
      mes: p.mes,
      mesLabel: formatearMes(p.mes),
      proyeccion: p.valor_esperado,
      bandaBase: p.limite_inferior,
      bandaRango: Math.max(0, p.limite_superior - p.limite_inferior),
    }));

    return [...puntosHistoricos.slice(0, -1), puente, ...puntosProyectados];
  }, [senda.datos]);

  return (
    <Card>
      <CardHeader
        ayuda={AYUDAS.senda}
        title="Senda del volumen útil — proyección de largo plazo"
        subtitle={
          senda.datos
            ? `${senda.datos.nombre} · ${senda.datos.metodo}`
            : "Trayectoria mensual observada y proyectada"
        }
        action={
          <div className="flex flex-wrap items-center gap-2">
            <InfoButton titulo={AYUDAS.selectorSenda.titulo}>{AYUDAS.selectorSenda.contenido}</InfoButton>
            <select
              value={embalseId}
              onChange={(e) => setEmbalseId(e.target.value)}
              className="rounded-lg border border-border-strong bg-background px-2.5 py-1.5 text-xs text-foreground outline-none"
            >
              <option value={ID_TOTAL_NACIONAL}>Total nacional</option>
              {embalses.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre}
                </option>
              ))}
            </select>
            <InfoButton titulo={AYUDAS.horizonteSenda.titulo}>{AYUDAS.horizonteSenda.contenido}</InfoButton>
            <div className="flex gap-1 rounded-lg border border-border p-0.5">
              {HORIZONTES_SENDA_VOLUMEN.map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizonte(h)}
                  className="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
                  style={
                    horizonte === h
                      ? { backgroundColor: "var(--color-marca)", color: "white" }
                      : { color: "var(--foreground-muted)" }
                  }
                >
                  {h}m
                </button>
              ))}
            </div>
          </div>
        }
      />

      {senda.cargando && !senda.datos && <SkeletonChart />}

      {senda.error && (
        <p className="px-5 py-4 text-sm" style={{ color: "var(--color-critico)" }}>
          No fue posible cargar la senda de volumen: {senda.error}
        </p>
      )}

      {senda.datos && (
        <>
          <div className="grid grid-cols-1 gap-3 px-5 pt-4 sm:grid-cols-2">
            <div className="rounded-xl border border-border p-3">
              <div className="flex items-center gap-1.5">
                <p className="text-[11px] font-medium uppercase tracking-wide text-foreground-muted">
                  Último observado
                </p>
                <InfoButton titulo={AYUDAS.ultimoObservado.titulo}>{AYUDAS.ultimoObservado.contenido}</InfoButton>
              </div>
              <p className="mt-1 text-xl font-semibold tabular-nums text-foreground">
                {formatearPorcentaje(senda.datos.ultimo_observado.pct_volumen_util)}
              </p>
              <p className="text-xs text-foreground-muted">
                {formatearMes(senda.datos.ultimo_observado.mes)}
              </p>
            </div>
            <div className="rounded-xl border border-border p-3">
              <div className="flex items-center gap-1.5">
                <p className="text-[11px] font-medium uppercase tracking-wide text-foreground-muted">
                  Mínimo proyectado
                </p>
                <InfoButton titulo={AYUDAS.minimoProyectado.titulo}>{AYUDAS.minimoProyectado.contenido}</InfoButton>
              </div>
              <p
                className="mt-1 text-xl font-semibold tabular-nums"
                style={{ color: colorMinimoProyectado(senda.datos.minimo_proyectado.valor_esperado) }}
              >
                {formatearPorcentaje(senda.datos.minimo_proyectado.valor_esperado)}
              </p>
              <p className="text-xs text-foreground-muted">
                {formatearMes(senda.datos.minimo_proyectado.mes)}
              </p>
            </div>
          </div>
          <p className="px-5 pt-2 text-[11px] text-foreground-muted">
            Riesgo de la senda: rojo &lt;55% · ámbar &lt;65% · verde ≥65%
          </p>
          {senda.datos.horizonte_efectivo_meses < horizonte && (
            <p className="px-5 pt-1 text-[11px] text-foreground-muted">
              El modelo publica {senda.datos.horizonte_efectivo_meses} meses de proyección: se
              muestran {senda.datos.horizonte_efectivo_meses} aunque se pidieron {horizonte}.
            </p>
          )}

          <div className="h-72 w-full px-2 pb-2 pt-4 sm:px-4">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={datos} margin={{ top: 4, right: 8, left: 4, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis
                  dataKey="mesLabel"
                  tick={{ fontSize: 11, fill: "var(--foreground-muted)" }}
                  tickLine={false}
                  axisLine={{ stroke: "var(--border)" }}
                  minTickGap={28}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "var(--foreground-muted)" }}
                  tickLine={false}
                  axisLine={false}
                  unit="%"
                  width={48}
                  domain={[0, (maximo: number) => Math.max(100, Math.ceil(maximo))]}
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
                  dataKey="observado"
                  name="Observado"
                  stroke="var(--chart-volumen)"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="proyeccion"
                  name="Proyección"
                  stroke="var(--chart-prediccion)"
                  strokeWidth={2.5}
                  strokeDasharray="6 4"
                  dot={false}
                  isAnimationActive={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {esOutputs ? (
            <div className="px-5 pb-5 pt-2">
              <p
                className="rounded-lg p-3 text-xs leading-relaxed"
                style={{ backgroundColor: "var(--color-marca-bg)", color: "var(--foreground-muted)" }}
              >
                <strong style={{ color: "var(--color-marca-oscuro)" }}>Sobre esta proyección: </strong>
                proviene del modelo de largo plazo (Prophet + XGBoost) con escenarios climáticos
                ENSO simulados por Monte Carlo. La banda son los escenarios P10–P90, no un
                intervalo de confianza estadístico, y en los primeros meses puede ser muy angosta.
                Los resultados entregados no incluyen validación fuera de muestra, por eso no se
                muestra una tabla walk-forward.
              </p>
            </div>
          ) : (
            <div className="px-5 pb-5 pt-2">
              <div className="mb-2 flex items-center gap-1.5">
                <p className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">
                  Validación walk-forward (honesta)
                </p>
                <InfoButton titulo={AYUDAS.validacion.titulo}>{AYUDAS.validacion.contenido}</InfoButton>
              </div>
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-xs text-foreground-muted">
                    <th className="py-1.5 pr-4 font-medium"><span className="inline-flex items-center gap-1">Modelo<InfoButton titulo={AYUDAS.valModelo.titulo}>{AYUDAS.valModelo.contenido}</InfoButton></span></th>
                    <th className="py-1.5 pr-4 font-medium"><span className="inline-flex items-center gap-1">MAE<InfoButton titulo={AYUDAS.valMae.titulo}>{AYUDAS.valMae.contenido}</InfoButton></span></th>
                    <th className="py-1.5 font-medium"><span className="inline-flex items-center gap-1">R²<InfoButton titulo={AYUDAS.valR2.titulo}>{AYUDAS.valR2.contenido}</InfoButton></span></th>
                  </tr>
                </thead>
                <tbody>
                  {senda.datos.validacion.map((m) => (
                    <tr key={m.modelo} className="border-b border-border/60 last:border-0">
                      <td className="py-1.5 pr-4 text-foreground">{m.modelo}</td>
                      <td className="py-1.5 pr-4 tabular-nums text-foreground-muted">{m.mae.toFixed(3)}</td>
                      <td className="py-1.5 tabular-nums text-foreground-muted">{m.r2.toFixed(3)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p
                className="mt-3 rounded-lg p-3 text-xs leading-relaxed"
                style={{ backgroundColor: "var(--color-alerta-bg)", color: "var(--foreground-muted)" }}
              >
                <strong style={{ color: "var(--color-alerta)" }}>Nota de honestidad: </strong>
                la senda se valida contra una línea base ingenua de persistencia (repetir el último
                valor observado) para los últimos meses de historia. Cuando la persistencia iguala o
                supera al modelo, la senda debe leerse como la{" "}
                <strong>forma estacional esperada</strong> del embalse, no como una predicción
                puntual superior. Misma vara aplicada a todos los embalses.
              </p>
            </div>
          )}
        </>
      )}
    </Card>
  );
}
