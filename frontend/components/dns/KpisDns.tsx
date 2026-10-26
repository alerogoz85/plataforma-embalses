"use client";

import { KpiCard } from "@/components/dashboard/KpiCard";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonKpiCard } from "@/components/ui/Skeleton";
import type { ResumenDns } from "@/lib/api/types";
import { esMejora, formatearVariacionPct, nombreCausa } from "@/lib/utils/dns";
import { formatearMes, formatearNumero, formatearPorcentajeOpcional } from "@/lib/utils/formatters";
import { AYUDAS_DNS } from "./ayudasDns";

const ICONO_RAYO = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" />
  </svg>
);
const ICONO_ALERTA = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 3 2 20h20L12 3Z" />
    <path d="M12 10v4M12 17h.01" />
  </svg>
);
const ICONO_BATERIA = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="2" y="7" width="18" height="10" rx="2" />
    <path d="M22 11v2M6 10v4" />
  </svg>
);
const ICONO_RELOJ = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7v5l3 2" />
  </svg>
);

/** Cuatro tarjetas del resumen del período filtrado. El resumen lo consulta la página una sola vez. */
export function KpisDns({ resumen }: { resumen: { datos: ResumenDns | null; error: string | null } }) {
  const { datos, error } = resumen;
  if (error) return <ErrorBloque que="los indicadores" mensaje={error} />;
  if (!datos) {
    return (
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonKpiCard key={i} />
        ))}
      </section>
    );
  }

  const comparacion = datos.periodo_meses === 0 ? "todo el histórico, sin comparación" : "frente al período anterior";
  const delta = (v: number | null) =>
    v === null ? null : { texto: `${formatearVariacionPct(v)} ${comparacion}`, positivo: esMejora(v) };

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        etiqueta={`Eventos DNS · ${formatearMes(datos.desde)} a ${formatearMes(datos.hasta)}`}
        valor={formatearNumero(datos.eventos, 0)}
        delta={delta(datos.variacion_eventos_pct)}
        detalle={
          datos.causa_mas_frecuente
            ? `Causa conocida más frecuente: ${nombreCausa(datos.causa_mas_frecuente).toLowerCase()} (${formatearNumero(datos.causa_mas_frecuente_eventos, 0)})`
            : undefined
        }
        icono={ICONO_RAYO}
        acento="var(--color-alerta)"
        ayuda={AYUDAS_DNS.eventos}
      />
      <KpiCard
        etiqueta="Energía no atendida"
        valor={`${formatearNumero(datos.energia_gwh, 1)} GWh`}
        delta={delta(datos.variacion_energia_pct)}
        icono={ICONO_BATERIA}
        acento="var(--color-critico)"
        ayuda={AYUDAS_DNS.energia}
      />
      <KpiCard
        etiqueta="Eventos críticos (≥ 100 MWh)"
        valor={formatearPorcentajeOpcional(datos.eventos ? datos.pct_criticos : null)}
        detalle="Del total de eventos del período"
        icono={ICONO_ALERTA}
        acento="var(--color-critico)"
        ayuda={AYUDAS_DNS.criticos}
      />
      <KpiCard
        etiqueta="Eventos no programados"
        valor={formatearPorcentajeOpcional(datos.pct_no_programados)}
        detalle={datos.eventos_edac > 0 ? `Además, ${formatearNumero(datos.eventos_edac, 0)} eventos EDAC (no incluidos)` : "Sin eventos EDAC en el período"}
        icono={ICONO_RELOJ}
        acento="var(--color-marca)"
        ayuda={AYUDAS_DNS.noProgramados}
      />
    </section>
  );
}
