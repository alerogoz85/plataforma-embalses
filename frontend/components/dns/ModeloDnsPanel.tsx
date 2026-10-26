"use client";

import { CardHeader } from "@/components/ui/Card";
import { PanelAmpliable } from "@/components/ui/PanelAmpliable";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { ModeloDns } from "@/lib/api/types";
import { etiquetaMesDns, formatearVariacionPct } from "@/lib/utils/dns";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_DNS } from "./ayudasDns";

const NOMBRE_VARIABLE: Record<string, string> = { n_eventos: "Número de eventos", energia_kwh: "Energía no atendida (kWh)" };

/**
 * Modelo predictivo: cuánto mejora a la persistencia (suponer que el mes siguiente será igual al actual), qué variables
 * pesan más y el pronóstico por subárea. Las métricas no cambian con los filtros; el pronóstico respeta región y subárea.
 */
interface ModeloDnsPanelProps {
  modelo: { datos: ModeloDns | null; error: string | null };
  /** Por defecto mide lo mismo que el panel de al lado; ampliado muestra métricas, variables y pronóstico completos. */
  ampliado: boolean;
  onAlternarAmpliado: () => void;
}

export function ModeloDnsPanel({ modelo, ampliado, onAlternarAmpliado }: ModeloDnsPanelProps) {
  if (modelo.error) return <ErrorBloque que="el modelo predictivo" mensaje={modelo.error} />;
  if (!modelo.datos) return <SkeletonChart />;
  const m = modelo.datos;
  const variables = [...new Set(m.metricas.map((x) => x.variable))];
  const maxImportancia = Math.max(...m.importancia.map((i) => i.importancia_n_eventos), 0.0001);

  return (
    <PanelAmpliable
      id="panel-modelo"
      resumen={`${m.pronostico.length} ${m.pronostico.length === 1 ? "subárea" : "subáreas"} y más`}
      ampliado={ampliado}
      onAlternar={onAlternarAmpliado}
      encabezado={
        <CardHeader
          title="Modelo predictivo"
          subtitle={`Pronóstico de ${etiquetaMesDns(m.periodo_pronostico)} por subárea, evaluado contra la persistencia`}
          ayuda={AYUDAS_DNS.modelo}
        />
      }
    >
      <div className="space-y-6 px-5 pb-5 pt-3">
        {variables.map((v) => (
          <section key={v} aria-label={`Métricas de ${NOMBRE_VARIABLE[v] ?? v}`} className="overflow-x-auto">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground-muted">{NOMBRE_VARIABLE[v] ?? v}</h3>
            <table className="w-full text-sm tabular-nums">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-foreground-muted">
                  <th className="py-1 pr-3 font-semibold">Modelo</th>
                  <th className="py-1 pr-3 text-right font-semibold">MAE</th>
                  <th className="py-1 pr-3 text-right font-semibold">RMSE</th>
                  <th className="py-1 text-right font-semibold">Mejora vs. persistencia</th>
                </tr>
              </thead>
              <tbody>
                {m.metricas.filter((x) => x.variable === v).map((x) => (
                  <tr key={x.modelo} className="border-t border-border">
                    <td className="py-1 pr-3">{x.modelo}</td>
                    <td className="py-1 pr-3 text-right">{formatearNumero(x.mae, x.mae >= 1000 ? 0 : 2)}</td>
                    <td className="py-1 pr-3 text-right">{formatearNumero(x.rmse, x.rmse >= 1000 ? 0 : 2)}</td>
                    <td className="py-1 text-right font-medium" style={{ color: x.mejora_vs_persistencia_pct === null ? undefined : "var(--color-optimo)" }}>
                      {x.mejora_vs_persistencia_pct === null ? "referencia" : formatearVariacionPct(x.mejora_vs_persistencia_pct).replace("+", "")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        ))}

        <section aria-label="Variables más importantes">
          <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Variables que más pesan (eventos)</h3>
          <ul className="space-y-1.5">
            {m.importancia.map((i) => (
              <li key={i.variable} className="grid grid-cols-[minmax(0,12rem)_1fr_3rem] items-center gap-2 text-xs">
                <span className="truncate font-mono" title={i.variable}>{i.variable}</span>
                <div className="h-2 rounded-full" style={{ backgroundColor: "var(--border)" }} aria-hidden="true">
                  <div className="h-2 rounded-full" style={{ width: `${(i.importancia_n_eventos / maxImportancia) * 100}%`, backgroundColor: "var(--chart-volumen)" }} />
                </div>
                <span className="text-right tabular-nums text-foreground-muted">{formatearNumero(i.importancia_n_eventos * 100, 1)} %</span>
              </li>
            ))}
          </ul>
        </section>

        <section aria-label="Pronóstico por subárea" className="overflow-x-auto">
          <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Pronóstico de {etiquetaMesDns(m.periodo_pronostico)} por subárea</h3>
          {m.pronostico.length === 0 ? (
            <p className="py-3 text-sm text-foreground-muted">El modelo no pronostica ninguna subárea de este ámbito.</p>
          ) : (
            <table className="w-full text-sm tabular-nums">
              <thead>
                <tr className="text-left text-[11px] uppercase tracking-wide text-foreground-muted">
                  <th className="py-1 pr-3 font-semibold">Subárea</th>
                  <th className="py-1 pr-3 text-right font-semibold">Eventos</th>
                  <th className="py-1 text-right font-semibold">Energía (GWh)</th>
                </tr>
              </thead>
              <tbody>
                {m.pronostico.map((p) => (
                  <tr key={p.codigo} className="border-t border-border">
                    <td className="py-1 pr-3">{p.nombre}</td>
                    <td className="py-1 pr-3 text-right">{formatearNumero(p.n_eventos, 1)}</td>
                    <td className="py-1 text-right">{formatearNumero(p.energia_gwh, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </PanelAmpliable>
  );
}
