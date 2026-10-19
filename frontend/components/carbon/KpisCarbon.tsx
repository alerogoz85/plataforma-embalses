"use client";

import { KpiCard } from "@/components/dashboard/KpiCard";
import { SkeletonKpiCard } from "@/components/ui/Skeleton";
import type { ResumenCarbon, UnidadCarbon } from "@/lib/api/types";
import { formatearNumero, formatearPorcentaje } from "@/lib/utils/formatters";
import {
  COLOR_NIVEL,
  ETIQUETA_NIVEL,
  ETIQUETA_UNIDAD,
  convertirBanda,
  convertirConsumo,
  decimalesUnidad,
  etiquetaMesCarbon,
  nivelUsoTecho,
} from "@/lib/utils/carbon";
import { AYUDAS_CARBON } from "./ayudasCarbon";
import { ErrorCarbon } from "./ErrorCarbon";

const ICONO_FUEGO = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 2s5 4.5 5 9.5A5 5 0 0 1 7 12c0-1.5.6-2.6 1.5-3.5C9 10 10 10.5 10 10.5S9 6 12 2Z" />
    <path d="M12 22a4 4 0 0 0 4-4c0-2-2-3-4-5-2 2-4 3-4 5a4 4 0 0 0 4 4Z" />
  </svg>
);
const ICONO_MEDIDOR = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
    <path d="M4 18a8 8 0 1 1 16 0" />
    <path d="m12 18 4-6" />
  </svg>
);
const ICONO_DADOS = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="3" y="3" width="18" height="18" rx="3" />
    <path d="M8 8h.01M16 8h.01M8 16h.01M16 16h.01M12 12h.01" />
  </svg>
);
const ICONO_CAJA = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 8 12 3 3 8v8l9 5 9-5V8Z" />
    <path d="m3 8 9 5 9-5M12 13v8" />
  </svg>
);

interface KpisCarbonProps {
  /** Resultado de /carbon/resumen; lo consulta la pagina una sola vez y lo comparte con los trimestres. */
  resumen: { datos: ResumenCarbon | null; error: string | null };
  unidad: UnidadCarbon;
  dias: number;
}

/** Cuatro tarjetas del resumen: pico, uso del techo, probabilidad de superar el record e inventario del pico. */
export function KpisCarbon({ resumen, unidad, dias }: KpisCarbonProps) {
  const { datos, error } = resumen;

  if (error) return <ErrorCarbon que="los indicadores" mensaje={error} />;
  if (!datos) {
    return (
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonKpiCard key={i} />
        ))}
      </section>
    );
  }

  const pc = datos.poder_calorifico_mbtu_t;
  const d = decimalesUnidad(unidad);
  const banda = convertirBanda(datos.pico.carbon_gbtu_dia, unidad, pc);
  const nivel = nivelUsoTecho(datos.pico.uso_techo_p50_pct);
  const mesPico = etiquetaMesCarbon(datos.pico.fecha);
  const record = convertirConsumo(datos.maximo_historico.carbon_gbtu_dia, unidad, pc);
  const inv = datos.inventario_pico;

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        etiqueta={`Pico esperado · ${mesPico}`}
        valor={`${formatearNumero(banda.p50, d)} ${ETIQUETA_UNIDAD[unidad]}`}
        detalle={`P10–P90: ${formatearNumero(banda.p10, d)} – ${formatearNumero(banda.p90, d)}`}
        icono={ICONO_FUEGO}
        acento="var(--color-alerta)"
        ayuda={AYUDAS_CARBON.picoEsperado}
      />
      <KpiCard
        etiqueta="Uso del techo térmico"
        valor={formatearPorcentaje(datos.pico.uso_techo_p50_pct)}
        detalle={`${ETIQUETA_NIVEL[nivel]} · récord ${formatearNumero(record, d)} (${etiquetaMesCarbon(datos.maximo_historico.fecha)})`}
        icono={ICONO_MEDIDOR}
        acento={COLOR_NIVEL[nivel]}
        ayuda={AYUDAS_CARBON.usoTecho}
      />
      <KpiCard
        etiqueta="Prob. de superar el récord"
        valor={formatearPorcentaje(datos.pico.prob_supera_maximo_pct, 0)}
        detalle={`En ${mesPico}, según las simulaciones del modelo`}
        icono={ICONO_DADOS}
        acento="var(--color-marca)"
        ayuda={AYUDAS_CARBON.probabilidadRecord}
      />
      <KpiCard
        etiqueta={`Inventario de ${dias} días`}
        valor={inv ? `${formatearNumero(inv.kt_p50, 0)} kt` : "—"}
        detalle={inv ? `P90: ${formatearNumero(inv.kt_p90, 0)} kt · pico en ${etiquetaMesCarbon(inv.fecha)}` : "Sin inventario calculado"}
        icono={ICONO_CAJA}
        acento="var(--chart-aportes)"
        ayuda={AYUDAS_CARBON.inventarioPico}
      />
    </section>
  );
}
