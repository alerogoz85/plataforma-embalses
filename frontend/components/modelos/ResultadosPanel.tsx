"use client";

import { useMemo, useState } from "react";

import { KpiCard } from "@/components/dashboard/KpiCard";
import { Campo } from "@/components/ui/Campo";
import { Card, CardHeader } from "@/components/ui/Card";
import type { ResultadoModelo } from "@/lib/api/types";
import { COLOR_NIVEL_INDICADOR, etiquetaX, filtrarSeries, opcionesPeriodo } from "@/lib/utils/modelos";
import { formatearFecha } from "@/lib/utils/formatters";
import { AYUDAS_MODELOS } from "./ayudasModelos";
import { SerieModeloChart } from "./SerieModeloChart";
import { TablaModeloCard } from "./TablaModeloCard";

const ICONO_NIVEL = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v5M12 16h.01" />
  </svg>
);

/**
 * Resultados importados del modelo: filtro de período (que recorta todos los gráficos), indicadores, series, tablas,
 * advertencias y parámetros de la corrida. Todo sale tal cual del resultado: aquí no se calcula nada.
 */
export function ResultadosPanel({ resultado }: { resultado: ResultadoModelo }) {
  const opciones = useMemo(() => opcionesPeriodo(resultado.series), [resultado.series]);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const series = useMemo(() => filtrarSeries(resultado.series, desde, hasta), [resultado.series, desde, hasta]);

  return (
    <div className="flex flex-col gap-5">
      {opciones.length > 1 && (
        <div className="grid grid-cols-1 gap-x-5 gap-y-4 rounded-2xl border border-border bg-background-elevated p-5 sm:grid-cols-3">
          <Campo etiqueta="Desde" ayuda={AYUDAS_MODELOS.filtroPeriodo}>
            <select className="campo-select" value={desde} onChange={(e) => setDesde(e.target.value)}>
              <option value="">Desde el inicio</option>
              {opciones.filter((o) => !hasta || o <= hasta).map((o) => (
                <option key={o} value={o}>
                  {etiquetaX(o)}
                </option>
              ))}
            </select>
          </Campo>
          <Campo etiqueta="Hasta" ayuda={AYUDAS_MODELOS.filtroPeriodo}>
            <select className="campo-select" value={hasta} onChange={(e) => setHasta(e.target.value)}>
              <option value="">Hasta el final</option>
              {opciones.filter((o) => !desde || o >= desde).map((o) => (
                <option key={o} value={o}>
                  {etiquetaX(o)}
                </option>
              ))}
            </select>
          </Campo>
          <div className="flex items-end justify-end">
            <button
              type="button"
              onClick={() => {
                setDesde("");
                setHasta("");
              }}
              className="inline-flex h-9 items-center gap-2 rounded-lg border px-3 text-xs font-semibold transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
              style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}
            >
              Restablecer filtros
            </button>
          </div>
        </div>
      )}

      {resultado.advertencias.length > 0 && (
        <Card>
          <CardHeader title="Cómo leer este resultado" ayuda={AYUDAS_MODELOS.advertencias} />
          <ul className="list-disc space-y-1.5 px-9 pb-5 pt-3 text-sm leading-relaxed">
            {resultado.advertencias.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </Card>
      )}

      {resultado.indicadores.length > 0 && (
        <section aria-label="Indicadores del resultado" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {resultado.indicadores.map((i, n) => (
            <KpiCard
              key={i.etiqueta}
              etiqueta={i.etiqueta}
              valor={i.valor}
              detalle={i.detalle ?? undefined}
              icono={i.nivel ? ICONO_NIVEL : undefined}
              acento={i.nivel ? COLOR_NIVEL_INDICADOR[i.nivel] : undefined}
              ayuda={n === 0 ? AYUDAS_MODELOS.indicadores : undefined}
            />
          ))}
        </section>
      )}

      {series.length > 0 && (
        <section aria-label="Series del modelo" className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {series.map((s) => (
            <SerieModeloChart key={s.id} serie={s} />
          ))}
        </section>
      )}

      {resultado.tablas.length > 0 && (
        <section aria-label="Tablas del modelo" className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {resultado.tablas.map((t) => (
            <TablaModeloCard key={t.id} tabla={t} />
          ))}
        </section>
      )}

      <Card>
        <CardHeader title="Procedencia de la corrida" subtitle={`${resultado.origen} · importada ${formatearFecha(resultado.generado_en.slice(0, 10))}`} />
        {resultado.configuracion.length > 0 && (
          <dl className="grid grid-cols-1 gap-x-6 gap-y-2 px-5 pb-5 pt-3 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {resultado.configuracion.map((p) => (
              <div key={p.nombre} className="border-t border-border pt-2">
                <dt className="text-[11px] font-semibold uppercase tracking-wide text-foreground-muted">{p.nombre}</dt>
                <dd>{p.valor}</dd>
              </div>
            ))}
          </dl>
        )}
      </Card>
    </div>
  );
}
