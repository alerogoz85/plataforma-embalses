"use client";

import { useMemo } from "react";

import { Footer } from "@/components/layout/Footer";
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
import { useEstadoUrl, type EsquemaUrl } from "@/lib/hooks/useEstadoUrl";
import { codigo, enLista, fechaIso } from "@/lib/utils/url";
import { ID_TOTAL_NACIONAL, REGIONES, idAgregadoRegion, type EmbalseResumen, type KpiNacional } from "@/lib/api/types";

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

/** Las tarjetas de un solo embalse salen de su propia fila (mismos campos que los KPI agregados). */
function kpisDeEmbalse(e: EmbalseResumen): KpiVista {
  return {
    pct_volumen_util_nacional: e.pct_volumen_util,
    delta_diario_pct: e.delta_diario_pct,
    delta_semanal_pct: e.delta_semanal_pct,
    aportes_pct_media_nacional: e.aportes_pct_media,
    capacidad_guardada_gwh: e.energia_util_gwh,
    nivel_riesgo_sistema: e.nivel_riesgo,
    total_embalses: 1,
  };
}

type KpiVista = Omit<KpiNacional, "fecha_corte" | "capacidad_guardada_gwh"> & {
  capacidad_guardada_gwh: number | null;
};

/**
 * Filtros globales del tablero, guardados en la URL (`/embalses?region=Centro&embalse=GUAVIO&desde=2026-05-01`).
 * Por defecto abre en «Todas las regiones» + «Todos los embalses» y los últimos 180 días; lo que vale el defecto no aparece en la URL.
 */
const ESQUEMA_FILTROS: EsquemaUrl<{ region: string | null; embalse: string | null; desde: string; hasta: string }> = {
  region: { param: "region", defecto: () => null, leer: enLista(REGIONES) },
  embalse: { param: "embalse", defecto: () => null, leer: codigo(40) },
  desde: { param: "desde", defecto: () => fechaHaceDias(180), leer: fechaIso },
  hasta: { param: "hasta", defecto: () => hoyISO(), leer: fechaIso },
};

export function TableroEmbalses() {
  const [{ region, embalse: embalseId, desde, hasta }, { actualizar, restablecer }] = useEstadoUrl(ESQUEMA_FILTROS);
  // Una dirección escrita a mano puede traer las fechas al revés: se ordenan en lugar de pedirle a la API un rango imposible.
  const [fechaInicio, fechaFin] = desde <= hasta ? [desde, hasta] : [hasta, desde];
  const setEmbalseId = (id: string | null) => actualizar({ embalse: id });
  const setFechaInicio = (f: string) => actualizar({ desde: f });
  const setFechaFin = (f: string) => actualizar({ hasta: f });

  const filtros = useMemo(
    () => ({ regiones: region ? [region] : undefined }),
    [region],
  );
  const resumen = useResumenNacional(filtros);
  const fuente = useFuenteDatos();

  const embalses = resumen.datos?.embalses ?? [];
  // Embalse elegido, solo si pertenece a la region vigente.
  const embalseActual = embalseId ? embalses.find((e) => e.id === embalseId) : undefined;

  // Un unico "ambito" gobierna todo el tablero (tarjetas, graficos, senda y tabla):
  // el embalse elegido; si no hay, la region elegida; si tampoco, el total nacional.
  const ambitoId = embalseActual
    ? embalseActual.id
    : region
      ? idAgregadoRegion(region)
      : ID_TOTAL_NACIONAL;
  const ambitoNombre = embalseActual ? embalseActual.nombre : region ? `Región ${region}` : "Total nacional";

  const kpis = resumen.datos ? (embalseActual ? kpisDeEmbalse(embalseActual) : resumen.datos.kpis) : null;
  const regiones = resumen.datos?.regiones ?? [];
  const regionesVisibles = embalseActual ? regiones.filter((r) => r.region === embalseActual.region) : regiones;
  const embalsesVisibles = embalseActual ? [embalseActual] : embalses;
  const etiquetaVolumen = embalseActual
    ? `% Volumen útil · ${embalseActual.nombre}`
    : region
      ? `% Volumen útil · Región ${region}`
      : "% Volumen útil nacional";

  // Al cambiar de región el embalse vuelve a «Todos»: ambos cambios van en una sola navegación.
  function cambiarRegion(nueva: string | null) {
    actualizar({ region: nueva, embalse: null });
  }

  return (
    <div className="flex min-h-full flex-col">
      <Header fechaCorte={resumen.datos ? formatearFecha(resumen.datos.kpis.fecha_corte) : undefined} />

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 px-4 py-6 sm:px-6">
        <FiltersPanel
          regionSeleccionada={region}
          onCambiarRegion={cambiarRegion}
          embalseSeleccionado={embalseId}
          onCambiarEmbalse={setEmbalseId}
          onRestablecer={restablecer}
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
          {!kpis ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonKpiCard key={i} />)
          ) : (
            <>
              <KpiCard
                etiqueta={etiquetaVolumen}
                valor={formatearPorcentaje(kpis.pct_volumen_util_nacional)}
                delta={{
                  texto: `${formatearDelta(kpis.delta_diario_pct)} diario · ${formatearDelta(kpis.delta_semanal_pct)} semanal`,
                  positivo: kpis.delta_diario_pct >= 0,
                }}
                icono={ICONO_GOTA}
                acento="var(--color-marca)"
                ayuda={AYUDAS.pctVolumenUtilNacional}
              />
              <KpiCard
                etiqueta="Aportes (% media histórica)"
                valor={formatearPorcentajeOpcional(kpis.aportes_pct_media_nacional)}
                icono={ICONO_LLUVIA}
                acento="var(--chart-aportes)"
                ayuda={AYUDAS.aportes}
              />
              <KpiCard
                etiqueta="Capacidad guardada"
                valor={kpis.capacidad_guardada_gwh === null ? "—" : `${formatearNumero(kpis.capacidad_guardada_gwh, 0)} GWh`}
                icono={ICONO_RAYO}
                acento="var(--color-alerta)"
                ayuda={AYUDAS.capacidadGuardada}
              />
              <SistemaRiesgoCard nivel={kpis.nivel_riesgo_sistema} totalEmbalses={kpis.total_embalses} />
            </>
          )}
        </section>

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <MainChart
              embalseId={ambitoId}
              nombreEmbalse={ambitoNombre}
              fechaInicio={fechaInicio}
              fechaFin={fechaFin}
            />
          </div>
          <RegionBarChart regiones={regionesVisibles} cargando={resumen.cargando} />
        </section>

        <section>
          <SendaVolumenPanel embalseId={ambitoId} />
        </section>

        <section>
          <EmbalsesTable
            embalses={embalsesVisibles}
            cargando={resumen.cargando}
            onSeleccionar={setEmbalseId}
            embalseSeleccionado={embalseId}
          />
        </section>
      </main>

      <Footer>
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
      </Footer>
    </div>
  );
}
