"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { CausasDns } from "@/lib/api/types";
import { COLOR_CAUSA, NOMBRES_ORIGEN_CAUSA, nombreCausa } from "@/lib/utils/dns";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_DNS } from "./ayudasDns";

/** Por qué ocurren los eventos: causa (con su energía), de dónde sale la causa y los tipos de evento más comunes. */
export function CausasDnsPanel({ causas }: { causas: { datos: CausasDns | null; error: string | null } }) {
  if (causas.error) return <ErrorBloque que="las causas" mensaje={causas.error} />;
  if (!causas.datos) return <SkeletonChart />;
  const c = causas.datos;
  const inferidos = c.origen_de_la_causa.filter((o) => o.nombre.startsWith("inferida")).reduce((s, o) => s + o.eventos, 0);

  return (
    <Card>
      <CardHeader title="Causas de los eventos" subtitle={`${formatearNumero(c.total, 0)} eventos`} ayuda={AYUDAS_DNS.causas} />
      {c.total === 0 ? (
        <p className="px-5 py-8 text-center text-sm text-foreground-muted">No hay eventos con estos filtros.</p>
      ) : (
        <div className="space-y-5 px-5 pb-5 pt-3">
          <ul className="space-y-2.5" aria-label="Eventos por causa">
            {c.causas.map((x) => (
              <li key={x.causa}>
                <div className="flex items-baseline justify-between gap-2 text-sm">
                  <span className="font-medium">{nombreCausa(x.causa)}</span>
                  <span className="tabular-nums text-foreground-muted">
                    {formatearNumero(x.eventos, 0)} eventos · {formatearNumero(x.pct_eventos, 0)} % · {formatearNumero(x.energia_gwh, 1)} GWh
                  </span>
                </div>
                <div className="mt-1 h-2 rounded-full" style={{ backgroundColor: "var(--border)" }} aria-hidden="true">
                  <div className="h-2 rounded-full" style={{ width: `${x.pct_eventos}%`, backgroundColor: COLOR_CAUSA[x.causa] ?? "var(--chart-volumen)" }} />
                </div>
              </li>
            ))}
          </ul>

          <section aria-label="Origen de la causa">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground-muted">De dónde sale la causa</h3>
            <ul className="space-y-1 text-sm">
              {c.origen_de_la_causa.map((o) => (
                <li key={o.nombre} className="flex justify-between gap-2 tabular-nums">
                  <span>{NOMBRES_ORIGEN_CAUSA[o.nombre] ?? o.nombre}</span>
                  <span className="text-foreground-muted">{formatearNumero(o.eventos, 0)} ({formatearNumero((o.eventos / c.total) * 100, 0)} %)</span>
                </li>
              ))}
            </ul>
            {inferidos > 0 && (
              <p className="mt-1.5 text-xs text-foreground-muted">
                {formatearNumero((inferidos / c.total) * 100, 0)} % de las causas se infirieron del texto: son estimaciones, no lo que reportó el operador.
              </p>
            )}
          </section>

          <section aria-label="Tipos de evento">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Tipos de evento más comunes</h3>
            <ul className="space-y-1 text-sm">
              {c.tipos_evento.slice(0, 5).map((t) => (
                <li key={t.nombre} className="flex justify-between gap-2 tabular-nums">
                  <span>{t.nombre}</span>
                  <span className="text-foreground-muted">{formatearNumero(t.eventos, 0)}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
    </Card>
  );
}
