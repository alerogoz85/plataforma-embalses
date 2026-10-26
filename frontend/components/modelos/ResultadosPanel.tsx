"use client";

import { useMemo } from "react";

import { KpiCard } from "@/components/dashboard/KpiCard";
import { Campo } from "@/components/ui/Campo";
import { Card, CardHeader } from "@/components/ui/Card";
import type { ResultadoModelo } from "@/lib/api/types";
import { useEstadoUrl, type EsquemaUrl } from "@/lib/hooks/useEstadoUrl";
import { formatearFecha } from "@/lib/utils/formatters";
import {
  COLOR_NIVEL_INDICADOR,
  etiquetaX,
  filasVisibles,
  filtrarSeries,
  graficosVisibles,
  opcionesPeriodo,
  recortarGraficos,
} from "@/lib/utils/modelos";
import { enLista, mesIso } from "@/lib/utils/url";
import { AYUDAS_MODELOS } from "./ayudasModelos";
import { GraficoModeloChart } from "./GraficoModeloChart";
import { SerieModeloChart } from "./SerieModeloChart";
import { TablaModeloCard } from "./TablaModeloCard";

const ICONO_NIVEL = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 8v5M12 16h.01" />
  </svg>
);

type EstadoFiltros = Record<string, string>;

/**
 * Esquema de la URL de un resultado: el rango de meses (`desde`, `hasta`) y un parámetro por cada dimensión que declara el
 * modelo (p. ej. `serie` y `variable` en gas). Cada valor se valida contra sus opciones: uno inválido se ignora.
 */
function construirEsquema(resultado: ResultadoModelo): EsquemaUrl<EstadoFiltros> {
  const esquema: EsquemaUrl<EstadoFiltros> = {
    desde: { param: "desde", defecto: () => "", leer: mesIso },
    hasta: { param: "hasta", defecto: () => "", leer: mesIso },
  };
  for (const d of resultado.dimensiones) {
    if (d.id === "desde" || d.id === "hasta") continue; // nombres reservados del rango
    esquema[d.id] = { param: d.id, defecto: () => d.por_defecto, leer: enLista(d.opciones) };
  }
  return esquema;
}

/**
 * Resultados importados del modelo: filtros (período y las dimensiones del modelo, que recortan TODOS los gráficos y tablas a la vez),
 * advertencias, indicadores, series, gráficos, tablas y procedencia. Todo sale tal cual del resultado: aquí no se calcula nada.
 */
export function ResultadosPanel({ resultado }: { resultado: ResultadoModelo }) {
  const opciones = useMemo(() => opcionesPeriodo(resultado.series, resultado.graficos), [resultado.series, resultado.graficos]);
  const esquema = useMemo(() => construirEsquema(resultado), [resultado]);
  const [enUrl, { actualizar, restablecer }] = useEstadoUrl(esquema);

  // Un mes de la URL que no está en los datos (dirección escrita a mano) se ignora en lugar de dejar los gráficos vacíos.
  const desde = opciones.includes(enUrl.desde) ? enUrl.desde : "";
  const hasta = opciones.includes(enUrl.hasta) ? enUrl.hasta : "";
  const seleccion = useMemo(() => Object.fromEntries(resultado.dimensiones.map((d) => [d.id, enUrl[d.id] ?? d.por_defecto])), [resultado.dimensiones, enUrl]);

  const series = useMemo(() => filtrarSeries(resultado.series, desde, hasta), [resultado.series, desde, hasta]);
  const graficosDeLaSeleccion = useMemo(() => graficosVisibles(resultado.graficos, seleccion), [resultado.graficos, seleccion]);
  const graficos = useMemo(() => recortarGraficos(graficosDeLaSeleccion, desde, hasta), [graficosDeLaSeleccion, desde, hasta]);
  const hayFiltros = opciones.length > 1 || resultado.dimensiones.length > 0;

  return (
    <div className="flex flex-col gap-5">
      {hayFiltros && (
        <div className="grid grid-cols-1 gap-x-5 gap-y-4 rounded-2xl border border-border bg-background-elevated p-5 sm:grid-cols-2 lg:grid-cols-4">
          {resultado.dimensiones.map((d) => (
            <Campo key={d.id} etiqueta={d.etiqueta} ayuda={AYUDAS_MODELOS.filtroDimension}>
              <select className="campo-select" value={seleccion[d.id]} onChange={(e) => actualizar({ [d.id]: e.target.value })}>
                {d.opciones.map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
              </select>
            </Campo>
          ))}
          {opciones.length > 1 && (
            <>
              <Campo etiqueta="Desde" ayuda={AYUDAS_MODELOS.filtroPeriodo}>
                <select className="campo-select" value={desde} onChange={(e) => actualizar({ desde: e.target.value })}>
                  <option value="">Desde el inicio</option>
                  {opciones.filter((o) => !hasta || o <= hasta).map((o) => (
                    <option key={o} value={o}>
                      {etiquetaX(o)}
                    </option>
                  ))}
                </select>
              </Campo>
              <Campo etiqueta="Hasta" ayuda={AYUDAS_MODELOS.filtroPeriodo}>
                <select className="campo-select" value={hasta} onChange={(e) => actualizar({ hasta: e.target.value })}>
                  <option value="">Hasta el final</option>
                  {opciones.filter((o) => !desde || o >= desde).map((o) => (
                    <option key={o} value={o}>
                      {etiquetaX(o)}
                    </option>
                  ))}
                </select>
              </Campo>
            </>
          )}
          <div className="flex items-end justify-end sm:col-span-2 lg:col-span-4">
            <button
              type="button"
              onClick={restablecer}
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

      {(series.length > 0 || resultado.graficos.length > 0) && (
        <section aria-label="Gráficos del modelo" className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {series.map((s) => (
            <SerieModeloChart key={s.id} serie={s} />
          ))}
          {graficos.map((g) => (
            <GraficoModeloChart key={g.id} grafico={g} />
          ))}
          {resultado.graficos.length > 0 && graficosDeLaSeleccion.length === 0 && (
            <Card className="xl:col-span-2">
              <p className="px-5 py-10 text-center text-sm text-foreground-muted">
                El modelo no entregó un gráfico para esta combinación ({Object.values(seleccion).join(" · ")}); la tabla de resumen explica por qué cuando hay una advertencia.
              </p>
            </Card>
          )}
        </section>
      )}

      {resultado.tablas.length > 0 && (
        <section aria-label="Tablas del modelo" className="grid grid-cols-1 gap-5 xl:grid-cols-2">
          {resultado.tablas.map((t) => (
            <TablaModeloCard key={t.id} tabla={t} filas={filasVisibles(t, seleccion)} />
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
