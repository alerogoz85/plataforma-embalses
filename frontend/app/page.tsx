"use client";

import { useMemo, useState } from "react";

import { Header } from "@/components/layout/Header";
import { FiltersPanel } from "@/components/dashboard/FiltersPanel";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { SistemaRiesgoCard } from "@/components/dashboard/SistemaRiesgoCard";
import { MainChart } from "@/components/dashboard/MainChart";
import { RegionBarChart } from "@/components/dashboard/RegionBarChart";
import { SendaVolumenPanel } from "@/components/dashboard/SendaVolumenPanel";
import { EmbalsesTable } from "@/components/dashboard/EmbalsesTable";
import { AYUDAS } from "@/components/dashboard/ayudas";
import { SkeletonKpiCard } from "@/components/ui/Skeleton";
import { useFuenteDatos } from "@/lib/hooks/useFuenteDatos";
import { useResumenNacional } from "@/lib/hooks/useResumenNacional";
import {
  formatearDelta,
  formatearFecha,
  formatearNumero,
  formatearPorcentaje,
  formatearPorcentajeOpcional,
} from "@/lib/utils/formatters";
import { fechaHaceDias, hoyISO } from "@/lib/utils/dates";

const ICONO_GOTA = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 2s7 7.58 7 12a7 7 0 1 1-14 0c0-4.42 7-12 7-12Z" />
  </svg>
);
const ICONO_LLUVIA = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M16 13v8M8 13v8M12 15v8" strokeLinecap="round" />
    <path d="M20 16.58A5 5 0 0 0 18 7h-1.26A8 8 0 1 0 4 15.25" />
  </svg>
);
const ICONO_RAYO = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" strokeLinejoin="round" />
  </svg>
);

export default function DashboardPage() {
  const [region, setRegion] = useState<string | null>(null);
  const [embalseId, setEmbalseId] = useState<string | null>(null);
  const [fechaInicio, setFechaInicio] = useState(fechaHaceDias(180));
  const [fechaFin, setFechaFin] = useState(hoyISO());

  const filtros = useMemo(
    () => ({ regiones: region ? [region] : undefined }),
    [region],
  );
  const resumen = useResumenNacional(filtros);
  const fuente = useFuenteDatos();

  const embalses = resumen.datos?.embalses ?? [];
  const embalseActual = embalses.find((e) => e.id === embalseId);

  // Mantiene la seleccion apuntando a un embalse presente en la lista
  // filtrada actual (por ejemplo, tras cambiar de region), ajustando el
  // estado durante el render (sin efecto) siguiendo el patron recomendado
  // por React para derivar un valor a partir de datos que llegan de forma
  // asincrona.
  if (embalses.length > 0 && !embalseActual) {
    setEmbalseId(embalses[0].id);
  }

  return (
    <div className="flex min-h-full flex-col">
      <Header fechaCorte={resumen.datos ? formatearFecha(resumen.datos.kpis.fecha_corte) : undefined} />

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 px-4 py-6 sm:px-6">
        <FiltersPanel
          regionSeleccionada={region}
          onCambiarRegion={setRegion}
          embalseSeleccionado={embalseId}
          onCambiarEmbalse={setEmbalseId}
          fechaInicio={fechaInicio}
          fechaFin={fechaFin}
          onCambiarFechaInicio={setFechaInicio}
          onCambiarFechaFin={setFechaFin}
          embalsesDisponibles={embalses}
        />

        {resumen.error && (
          <div
            className="rounded-2xl border p-4 text-sm"
            style={{ borderColor: "var(--color-critico)", color: "var(--color-critico)" }}
          >
            No fue posible conectar con la API ({resumen.error}). Verifica que el backend esté
            corriendo en <code>NEXT_PUBLIC_API_BASE_URL</code>.
          </div>
        )}

        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {!resumen.datos ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonKpiCard key={i} />)
          ) : (
            <>
              <KpiCard
                etiqueta="% Volumen útil nacional"
                valor={formatearPorcentaje(resumen.datos.kpis.pct_volumen_util_nacional)}
                delta={{
                  texto: `${formatearDelta(resumen.datos.kpis.delta_diario_pct)} diario · ${formatearDelta(resumen.datos.kpis.delta_semanal_pct)} semanal`,
                  positivo: resumen.datos.kpis.delta_diario_pct >= 0,
                }}
                icono={ICONO_GOTA}
                acento="var(--color-marca)"
                ayuda={AYUDAS.pctVolumenUtilNacional}
              />
              <KpiCard
                etiqueta="Aportes (% media histórica)"
                valor={formatearPorcentajeOpcional(resumen.datos.kpis.aportes_pct_media_nacional)}
                icono={ICONO_LLUVIA}
                acento="var(--chart-aportes)"
                ayuda={AYUDAS.aportes}
              />
              <KpiCard
                etiqueta="Capacidad guardada"
                valor={`${formatearNumero(resumen.datos.kpis.capacidad_guardada_gwh, 0)} GWh`}
                icono={ICONO_RAYO}
                acento="var(--color-alerta)"
                ayuda={AYUDAS.capacidadGuardada}
              />
              <SistemaRiesgoCard
                nivel={resumen.datos.kpis.nivel_riesgo_sistema}
                totalEmbalses={resumen.datos.kpis.total_embalses}
              />
            </>
          )}
        </section>

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <MainChart
              embalseId={embalseId}
              nombreEmbalse={embalseActual?.nombre ?? ""}
              fechaInicio={fechaInicio}
              fechaFin={fechaFin}
            />
          </div>
          <RegionBarChart regiones={resumen.datos?.regiones ?? []} cargando={resumen.cargando} />
        </section>

        <section>
          <SendaVolumenPanel embalses={embalses} />
        </section>

        <section>
          <EmbalsesTable
            embalses={embalses}
            cargando={resumen.cargando}
            onSeleccionar={setEmbalseId}
            embalseSeleccionado={embalseId}
          />
        </section>
      </main>

      <footer className="border-t border-border px-4 py-4 text-center text-xs text-foreground-muted sm:px-6">
        {fuente.datos ? (
          <>
            <strong style={{ color: fuente.datos.es_real ? "var(--color-optimo)" : "var(--color-alerta)" }}>
              {fuente.datos.es_real ? "Datos reales" : "Datos no reales"}
            </strong>{" "}
            · {fuente.datos.fuente}
            {fuente.datos.fecha_corte && ` · corte ${formatearFecha(fuente.datos.fecha_corte)}`}
          </>
        ) : (
          "Verificando procedencia de los datos…"
        )}
        {" · "}Plataforma de Monitoreo y Predicción de Embalses
      </footer>
    </div>
  );
}
