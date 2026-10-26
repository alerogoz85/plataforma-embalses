"use client";

import { CardHeader } from "@/components/ui/Card";
import { PanelAmpliable } from "@/components/ui/PanelAmpliable";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { ZonaDns } from "@/lib/api/types";
import { colorTendenciaZona, formatearVariacionPct } from "@/lib/utils/dns";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_DNS } from "./ayudasDns";

interface ZonasDnsPanelProps {
  zonas: { datos: { zonas: ZonaDns[] } | null; error: string | null };
  subareaSeleccionada: string | null;
  /** Un clic en una zona la elige como filtro de subárea de todo el tablero. */
  onSeleccionar: (zona: ZonaDns) => void;
  /** Por defecto mide lo mismo que el panel de al lado; ampliado muestra todas las zonas. */
  ampliado: boolean;
  onAlternarAmpliado: () => void;
}

/**
 * Ranking del índice de priorización de zonas (0-100). Es un resultado del modelo sobre todo el histórico: solo
 * respeta la región y la subárea. Cada fila es un botón (teclado y lector de pantalla) que filtra el tablero.
 */
export function ZonasDnsPanel({ zonas, subareaSeleccionada, onSeleccionar, ampliado, onAlternarAmpliado }: ZonasDnsPanelProps) {
  if (zonas.error) return <ErrorBloque que="el ranking de zonas" mensaje={zonas.error} />;
  if (!zonas.datos) return <SkeletonChart />;

  const filas = zonas.datos.zonas;
  return (
    <PanelAmpliable
      id="panel-zonas"
      resumen={`${filas.length} ${filas.length === 1 ? "zona" : "zonas"}`}
      ampliado={ampliado}
      onAlternar={onAlternarAmpliado}
      encabezado={
        <CardHeader
          title="Priorización de zonas"
          subtitle="Índice 0-100 sobre todo el histórico · rojo: la energía de los últimos 24 meses empeoró"
          ayuda={AYUDAS_DNS.zonas}
        />
      }
    >
      <div className="overflow-x-auto px-5 pb-5 pt-3">
        {filas.length === 0 ? (
          <p className="py-6 text-center text-sm text-foreground-muted">El modelo no prioriza ninguna subárea de este ámbito.</p>
        ) : (
          <table className="w-full text-sm tabular-nums">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-foreground-muted">
                <th className="py-1.5 pr-2 font-semibold">#</th>
                <th className="py-1.5 pr-3 font-semibold">Subárea</th>
                <th className="min-w-[8rem] py-1.5 pr-3 font-semibold">Índice</th>
                <th className="py-1.5 pr-3 text-right font-semibold">GWh</th>
                <th className="py-1.5 pr-3 text-right font-semibold">Eventos</th>
                <th className="py-1.5 pr-3 text-right font-semibold">Críticos</th>
                <th className="py-1.5 text-right font-semibold">24 m vs. 24 m previos</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((z) => {
                const elegida = z.codigo === subareaSeleccionada;
                return (
                  <tr key={z.codigo} className="border-t border-border" style={elegida ? { backgroundColor: "var(--color-marca-bg)" } : undefined}>
                    <td className="py-1.5 pr-2 text-foreground-muted">{z.ranking}</td>
                    <td className="py-1.5 pr-3">
                      <button
                        type="button"
                        onClick={() => onSeleccionar(z)}
                        aria-pressed={elegida}
                        title={`Filtrar el tablero a ${z.nombre}`}
                        className="text-left font-medium hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
                        style={{ color: "var(--color-marca-oscuro)" }}
                      >
                        {z.nombre}
                      </button>
                      <span className="block text-[11px] text-foreground-muted">{z.region}</span>
                    </td>
                    <td className="py-1.5 pr-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-full rounded-full" style={{ backgroundColor: "var(--border)" }} aria-hidden="true">
                          <div className="h-2 rounded-full" style={{ width: `${Math.min(100, Math.max(0, z.indice_priorizacion))}%`, backgroundColor: colorTendenciaZona(z.variacion_pct) }} />
                        </div>
                        <span className="w-10 shrink-0 text-right font-semibold">{formatearNumero(z.indice_priorizacion, 1)}</span>
                      </div>
                    </td>
                    <td className="py-1.5 pr-3 text-right">{formatearNumero(z.energia_total_gwh, 1)}</td>
                    <td className="py-1.5 pr-3 text-right">{formatearNumero(z.n_eventos, 0)}</td>
                    <td className="py-1.5 pr-3 text-right">{formatearNumero(z.pct_criticos, 0)} %</td>
                    <td className="py-1.5 text-right font-medium" style={{ color: z.variacion_pct > 0 ? "var(--color-critico)" : "var(--color-optimo)" }}>
                      {formatearVariacionPct(z.variacion_pct)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </PanelAmpliable>
  );
}
