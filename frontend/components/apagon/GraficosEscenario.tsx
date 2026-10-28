"use client";

import { useMemo } from "react";
import { Area, Bar, CartesianGrid, Cell, ComposedChart, LabelList, Legend, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardHeader } from "@/components/ui/Card";
import type { MesEscenario } from "@/lib/api/types";
import {
  COLOR_SEMAFORO, UMBRALES_DEFICIT, UMBRALES_SEVERO, colorCalor, formatearMillones, rotuloFranja, rotuloMes, semaforoPorUmbral,
} from "@/lib/utils/gemelo";
import { AYUDAS_APAGON } from "./ayudasApagon";

const TICK = { fontSize: 11, fill: "var(--foreground-muted)" } as const;
const TOOLTIP = {
  contentStyle: { background: "var(--background-elevated)", border: "1px solid var(--border)", borderRadius: 12, fontSize: 12 },
  labelStyle: { color: "var(--foreground)", fontWeight: 600 },
} as const;
const MARGEN = { top: 18, right: 12, left: 0, bottom: 0 } as const;

const pct = (v: unknown) => (typeof v === "number" ? `${v.toFixed(1)} %` : String(v));

/** Índice de riesgo (0-100) por mes: una barra por mes, coloreada con el semáforo del modelo y con el valor encima. */
export function GraficoIndiceRiesgo({ meses }: { meses: MesEscenario[] }) {
  const datos = useMemo(() => meses.map((m) => ({ ...m, etiqueta: rotuloMes(m.mes), indice: Math.round(m.indice_riesgo) })), [meses]);
  return (
    <Card>
      <CardHeader title="Índice de riesgo por mes (0–100) · color = semáforo" />
      <div className="h-72 w-full px-2 pb-3 pt-2 sm:px-4" role="img" aria-label={`Índice de riesgo por mes: ${datos.map((d) => `${d.etiqueta} ${d.indice} ${d.semaforo.toLowerCase()}`).join(", ")}`}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={datos} margin={MARGEN}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="etiqueta" tick={TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={24} />
            <YAxis domain={[0, 100]} tick={TICK} tickLine={false} axisLine={false} width={36} />
            <Tooltip {...TOOLTIP} formatter={(v: unknown) => [String(v), "Índice"]} />
            <Bar dataKey="indice" name="Índice de riesgo" isAnimationActive={false} radius={[3, 3, 0, 0]}>
              {datos.map((d) => (
                <Cell key={d.mes} fill={COLOR_SEMAFORO[d.semaforo]} />
              ))}
              <LabelList dataKey="indice" position="top" style={{ fontSize: 10, fill: "var(--foreground-muted)" }} />
            </Bar>
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

interface PuntoProps { cx?: number; cy?: number; payload?: { color: string } }
const PuntoSemaforo = ({ cx, cy, payload }: PuntoProps) =>
  cx === undefined || cy === undefined || !payload ? <g /> : <circle cx={cx} cy={cy} r={5} fill={payload.color} stroke="var(--background-elevated)" strokeWidth={1} />;

function PanelProbabilidad({ titulo, clave, umbrales, meses }: { titulo: string; clave: "probabilidad_deficit" | "probabilidad_apagon_severo"; umbrales: readonly [number, number]; meses: MesEscenario[] }) {
  const datos = useMemo(
    () => meses.map((m) => ({ etiqueta: rotuloMes(m.mes), valor: m[clave] * 100, color: COLOR_SEMAFORO[semaforoPorUmbral(m[clave], umbrales)] })),
    [meses, clave, umbrales],
  );
  return (
    <div>
      <p className="text-center text-xs text-foreground-muted">{titulo}</p>
      <div className="h-44 w-full" role="img" aria-label={`${titulo}: ${datos.map((d) => `${d.etiqueta} ${d.valor.toFixed(0)} %`).join(", ")}`}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={datos} margin={MARGEN}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="etiqueta" tick={TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={24} />
            <YAxis domain={[0, "auto"]} tick={TICK} tickLine={false} axisLine={false} width={36} tickFormatter={(v: number) => `${v}`} unit="" />
            {umbrales.map((u) => (
              <ReferenceLine key={u} y={u * 100} stroke="var(--foreground-muted)" strokeDasharray="2 3" strokeOpacity={0.7} />
            ))}
            <Tooltip {...TOOLTIP} formatter={(v: unknown) => [pct(v), "Probabilidad"]} />
            <Line type="linear" dataKey="valor" name={titulo} stroke="var(--foreground-muted)" strokeWidth={1} dot={<PuntoSemaforo />} activeDot={false} isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

/** Las dos probabilidades mensuales (déficit y apagón severo): línea fina con un punto por mes coloreado según los umbrales de la leyenda. */
export function GraficoProbabilidades({ meses }: { meses: MesEscenario[] }) {
  return (
    <Card>
      <CardHeader title="Indicadores de probabilidad por mes · color = semáforo por índice" subtitle="Probabilidad en %; las líneas punteadas marcan los umbrales amarillo y rojo" />
      <div className="space-y-2 px-2 pb-3 pt-2 sm:px-4">
        <PanelProbabilidad titulo="Probabilidad de Déficit · déficit relativo > 3 %" clave="probabilidad_deficit" umbrales={UMBRALES_DEFICIT} meses={meses} />
        <PanelProbabilidad titulo="Probabilidad de Apagón Severo · déficit relativo > 15 %" clave="probabilidad_apagon_severo" umbrales={UMBRALES_SEVERO} meses={meses} />
      </div>
      <Leyenda />
    </Card>
  );
}

const Punto = ({ color }: { color: string }) => <span aria-hidden="true" className="mx-0.5 inline-block h-2.5 w-2.5 rounded-full align-baseline" style={{ backgroundColor: color }} />;

/** Leyenda del semáforo por índice, con los mismos umbrales que se usan para pintar los puntos. */
function Leyenda() {
  const v = COLOR_SEMAFORO.VERDE, a = COLOR_SEMAFORO.AMARILLO, r = COLOR_SEMAFORO.ROJO;
  return (
    <p className="px-5 pb-5 text-xs leading-relaxed text-foreground-muted">
      Semáforo por índice — <b>Déficit:</b> <Punto color={v} />&lt;10 % · <Punto color={a} />10–25 % · <Punto color={r} />≥25 % · <b>Apagón severo:</b> <Punto color={v} />&lt;3 % · <Punto color={a} />3–10 % ·{" "}
      <Punto color={r} />≥10 %. Ambos salen de la misma distribución Monte Carlo con dos umbrales de severidad; el severo es un subconjunto (siempre ≤ déficit). Umbrales no calibrados contra
      apagones reales (proxies): leer como probabilidad relativa entre meses.
    </p>
  );
}

/** Mapa de calor: déficit esperado (MWh) por mes (columnas) y franja horaria (filas; la noche arriba, como en el visor). */
export function MapaCalorDeficit({ meses, franjas }: { meses: MesEscenario[]; franjas: string[] }) {
  const maximo = useMemo(() => Math.max(0, ...meses.flatMap((m) => m.deficit_por_franja_mwh)), [meses]);
  const filas = useMemo(() => franjas.map((f, i) => ({ franja: f, indice: i })).reverse(), [franjas]);
  const marcas = [0, 0.25, 0.5, 0.75, 1].map((t) => Math.round(maximo * t));
  const etiquetasX = meses.map((m, i) => (i % Math.max(1, Math.ceil(meses.length / 4)) === 0 ? rotuloMes(m.mes) : ""));
  return (
    <Card>
      <CardHeader title="Mapa de calor · déficit esperado por mes y franja horaria (MWh)" ayuda={AYUDAS_APAGON.mapaCalor} />
      <div className="px-5 pb-2 pt-4" role="img" aria-label={`Mapa de calor del déficit esperado en MWh, máximo ${Math.round(maximo)}. ${filas.map(({ franja, indice }) => `${rotuloFranja(franja)}: máximo ${Math.round(Math.max(...meses.map((m) => m.deficit_por_franja_mwh[indice])))}`).join("; ")}`}>
        <div className="flex gap-3">
          <div className="min-w-0 flex-1">
            <div className="grid gap-px" style={{ gridTemplateColumns: "7rem 1fr" }}>
              {filas.map(({ franja, indice }) => (
                <div key={franja} className="contents">
                  <span className="flex items-center justify-end pr-2 text-right text-[11px] leading-tight text-foreground-muted">{rotuloFranja(franja)}</span>
                  <div className="grid h-9 gap-px" style={{ gridTemplateColumns: `repeat(${meses.length}, minmax(0, 1fr))` }}>
                    {meses.map((m) => (
                      <div key={m.mes} title={`${rotuloMes(m.mes)} · ${rotuloFranja(franja)}: ${Math.round(m.deficit_por_franja_mwh[indice])} MWh`} style={{ backgroundColor: colorCalor(m.deficit_por_franja_mwh[indice], maximo) }} />
                    ))}
                  </div>
                </div>
              ))}
              <span />
              <div className="grid gap-px pt-1 text-[10px] text-foreground-muted" style={{ gridTemplateColumns: `repeat(${meses.length}, minmax(0, 1fr))` }}>
                {etiquetasX.map((t, i) => (
                  <span key={meses[i].mes} className="whitespace-nowrap">{t}</span>
                ))}
              </div>
            </div>
          </div>
          <div className="flex shrink-0 flex-col items-center text-[10px] text-foreground-muted" aria-hidden="true">
            <span>MWh</span>
            <div className="my-1 flex flex-1 gap-1">
              <div className="w-3 rounded-sm" style={{ background: `linear-gradient(to top, ${colorCalor(0, 1)}, ${colorCalor(1, 1)})` }} />
              <div className="flex flex-col-reverse justify-between">
                {marcas.map((m) => (
                  <span key={m} className="tabular-nums">{m}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
      <p className="px-5 pb-5 text-xs leading-relaxed text-foreground-muted">
        El riesgo se concentra en el <b>pico de la noche (18–21 h)</b>, cuando la demanda es alta y la solar ya no aporta.
      </p>
    </Card>
  );
}

/** Demanda y oferta mensual (MWh/mes): P50 de cada una y la banda P10–P90 de la oferta. */
export function GraficoOfertaDemanda({ meses }: { meses: MesEscenario[] }) {
  const datos = useMemo(
    () => meses.map((m) => ({ etiqueta: rotuloMes(m.mes), demanda: m.demanda_mwh_p50, oferta: m.oferta_mwh_p50, base: m.oferta_mwh_p10, rango: Math.max(0, m.oferta_mwh_p90 - m.oferta_mwh_p10) })),
    [meses],
  );
  const formato = (v: unknown) => (typeof v === "number" ? `${Math.round(v).toLocaleString("es-CO")} MWh` : String(v));
  return (
    <Card>
      <CardHeader title="Oferta vs demanda · banda P10–P90 (MWh/mes)" />
      <div className="h-72 w-full px-2 pb-1 pt-3 sm:px-4" role="img" aria-label="Demanda y oferta mensual P50 con la banda P10–P90 de la oferta, en MWh por mes">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={datos} margin={MARGEN}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="etiqueta" tick={TICK} tickLine={false} axisLine={{ stroke: "var(--border)" }} minTickGap={24} />
            <YAxis domain={[(min: number) => Math.floor((min * 0.97) / 1e5) * 1e5, (max: number) => Math.ceil((max * 1.03) / 1e5) * 1e5]} tick={TICK} tickLine={false} axisLine={false} width={44} tickFormatter={formatearMillones} />
            <Tooltip {...TOOLTIP} formatter={formato} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Area dataKey="base" stackId="oferta" stroke="none" fill="transparent" legendType="none" isAnimationActive={false} />
            <Area dataKey="rango" stackId="oferta" stroke="none" fill="var(--chart-volumen)" fillOpacity={0.18} name="Oferta P10–P90" isAnimationActive={false} />
            <Line type="linear" dataKey="demanda" name="Demanda P50" stroke="var(--color-critico)" strokeWidth={2} dot isAnimationActive={false} />
            <Line type="linear" dataKey="oferta" name="Oferta P50" stroke="var(--chart-volumen)" strokeWidth={2} dot isAnimationActive={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="px-5 pb-5 text-xs leading-relaxed text-foreground-muted">Cuando la banda de oferta baja hacia la demanda, sube la probabilidad de déficit.</p>
    </Card>
  );
}
