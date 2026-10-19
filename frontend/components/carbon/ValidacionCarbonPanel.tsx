"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { useValidacionCarbon } from "@/lib/hooks/useCarbon";
import type { CriterioCarbon } from "@/lib/api/types";
import { formatearFecha, formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_CARBON } from "./ayudasCarbon";
import { ErrorCarbon } from "./ErrorCarbon";

function ListaCriterios({ criterios }: { criterios: CriterioCarbon[] }) {
  return (
    <ul className="space-y-2">
      {criterios.map((c) => (
        <li key={c.criterio} className="flex items-start gap-2 text-sm">
          <span
            className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white"
            style={{ backgroundColor: c.cumple ? "var(--color-optimo)" : "var(--color-critico)" }}
            role="img"
            aria-label={c.cumple ? "Cumple" : "No cumple"}
          >
            {c.cumple ? "✓" : "✕"}
          </span>
          <span>
            <b>{c.criterio}</b> · {c.resultado}
            <span className="block text-xs text-foreground-muted">{c.interpretacion}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

const TH = "py-1.5 pr-3 text-[11px] font-semibold uppercase tracking-wide text-foreground-muted";
const TH_L = `${TH} text-left`;
const TH_R = `${TH} text-right`;

/**
 * Validacion del modelo: criterios de validez (cumple / no cumple), error por horizonte frente a
 * metodos ingenuos y comportamiento en episodios criticos. No depende de los filtros.
 */
export function ValidacionCarbonPanel() {
  const { datos, error } = useValidacionCarbon();

  if (error) return <ErrorCarbon que="la validación" mensaje={error} />;
  if (!datos) return <SkeletonChart />;

  const incumplidos = datos.veredicto.filter((c) => !c.cumple);
  const cumplidos = datos.veredicto.filter((c) => c.cumple);

  return (
    <Card>
      <CardHeader
        title="Validación del modelo"
        subtitle={`Cumple ${datos.criterios_cumplidos} de ${datos.criterios_total} criterios de validez`}
        ayuda={AYUDAS_CARBON.validacion}
      />
      <div className="space-y-6 px-5 pb-5 pt-4">
        <section aria-label="Criterios de validez">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Criterios</h3>
          {incumplidos.length > 0 && (
            <>
              <p className="mb-2 text-xs text-foreground-muted">
                {incumplidos.length} {incumplidos.length === 1 ? "criterio no cumple" : "criterios no cumplen"}: son las limitaciones que hay que conocer.
              </p>
              <ListaCriterios criterios={incumplidos} />
            </>
          )}
          {cumplidos.length > 0 && (
            <details className="mt-3 rounded-lg border border-border px-3 py-2">
              <summary className="cursor-pointer text-xs font-semibold text-marca">
                {cumplidos.length === 1 ? "Ver el criterio que cumple" : `Ver los ${cumplidos.length} criterios que cumplen`}
              </summary>
              <div className="mt-2">
                <ListaCriterios criterios={cumplidos} />
              </div>
            </details>
          )}
        </section>

        <section aria-label="Error por horizonte" className="overflow-x-auto">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Error medio (MAE, GBTU/día) por horizonte</h3>
          <table className="w-full text-sm tabular-nums">
            <thead>
              <tr>
                <th className={TH_L}>Horizonte</th>
                <th className={TH_R}>Modelo</th>
                <th className={TH_R}>Persistencia</th>
                <th className={TH_R}>Estacional</th>
                <th className={TH_R}>Climatología</th>
                <th className={TH_R}>Sesgo</th>
              </tr>
            </thead>
            <tbody>
              {datos.errores_horizonte.map((e) => (
                <tr key={e.horizonte_meses} className="border-t border-border">
                  <td className="py-1.5 pr-3">{e.horizonte_meses} {e.horizonte_meses === 1 ? "mes" : "meses"}</td>
                  <td className="py-1.5 pr-3 text-right font-semibold">{formatearNumero(e.mae_modelo, 1)}</td>
                  <td className="py-1.5 pr-3 text-right">{formatearNumero(e.mae_persistencia, 1)}</td>
                  <td className="py-1.5 pr-3 text-right">{formatearNumero(e.mae_estacional, 1)}</td>
                  <td className="py-1.5 pr-3 text-right">{formatearNumero(e.mae_climatologia, 1)}</td>
                  <td className="py-1.5 pr-3 text-right">{formatearNumero(e.sesgo_modelo, 1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section aria-label="Episodios críticos" className="overflow-x-auto">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Episodios críticos pasados</h3>
          <table className="w-full text-sm tabular-nums">
            <thead>
              <tr>
                <th className={TH_L}>Episodio</th>
                <th className={TH_R}>Real</th>
                <th className={TH_R}>P50</th>
                <th className={TH_R}>Error</th>
                <th className={TH_R}>Cobertura P10–P90</th>
              </tr>
            </thead>
            <tbody>
              {datos.episodios.map((e) => (
                <tr key={e.episodio} className="border-t border-border">
                  <td className="py-1.5 pr-3">
                    {e.episodio}
                    <span className="block text-[11px] text-foreground-muted">
                      {formatearFecha(e.inicio)} – {formatearFecha(e.fin)}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 text-right">{formatearNumero(e.real_gbtu_dia, 1)}</td>
                  <td className="py-1.5 pr-3 text-right">{formatearNumero(e.p50_gbtu_dia, 1)}</td>
                  <td className="py-1.5 pr-3 text-right">{formatearNumero(e.error_total_pct, 1)}%</td>
                  <td className="py-1.5 text-right">{formatearNumero(e.cobertura_p10_p90_pct, 0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </Card>
  );
}
