"use client";

import { useMemo } from "react";

import { CambiosReporteDnsPanel } from "@/components/dns/CambiosReporteDnsPanel";
import { CausasDnsPanel } from "@/components/dns/CausasDnsPanel";
import { ESQUEMA_DNS, FiltrosDnsPanel, type FiltrosDnsEstado } from "@/components/dns/FiltrosDns";
import { KpisDns } from "@/components/dns/KpisDns";
import { ModeloDnsPanel } from "@/components/dns/ModeloDnsPanel";
import { PatronesDnsChart } from "@/components/dns/PatronesDnsChart";
import { SerieDnsChart } from "@/components/dns/SerieDnsChart";
import { ZonasDnsPanel } from "@/components/dns/ZonasDnsPanel";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import type { FiltrosDnsApi } from "@/lib/api/client";
import type { ZonaDns } from "@/lib/api/types";
import {
  useCambiosReporteDns,
  useCatalogoDns,
  useCausasDns,
  useModeloDns,
  usePatronesDns,
  useResumenDns,
  useSerieDns,
  useZonasDns,
} from "@/lib/hooks/useDns";
import { useEstadoUrl } from "@/lib/hooks/useEstadoUrl";
import { formatearFecha } from "@/lib/utils/formatters";

/**
 * Tablero «Demanda no atendida (DNS)». Misma estructura que embalses y carbón:
 * encabezado -> filtros globales -> tarjetas -> gráficos -> detalle (causas, cambios de reporte y modelo).
 *
 * Los filtros viven en la URL (un solo estado) y llegan a cada bloque: todos responden a la vez. Los bloques
 * que son resultado del modelo sobre todo el histórico (zonas, cambios, modelo) solo usan región y subárea.
 */
export function TableroDns() {
  const [enUrl, { actualizar }] = useEstadoUrl(ESQUEMA_DNS);
  const catalogo = useCatalogoDns();

  // Una región o subárea escrita a mano en la URL que no existe en el catálogo se ignora (la API la rechazaría con 422);
  // y una subárea de otra región que la elegida tampoco vale. Mientras el catálogo carga se usa lo que trae la URL.
  const c0 = catalogo.datos;
  const filtros = useMemo<FiltrosDnsEstado>(() => {
    if (!c0) return enUrl;
    const region = enUrl.region && c0.regiones.includes(enUrl.region) ? enUrl.region : null;
    const sub = c0.subareas.find((s) => s.codigo === enUrl.subarea);
    const subarea = sub && (!region || sub.region === region) ? sub.codigo : null;
    return { ...enUrl, region, subarea };
  }, [enUrl, c0]);
  const setFiltros = (f: FiltrosDnsEstado) => actualizar(f);

  const api = useMemo<FiltrosDnsApi>(
    () => ({ periodoMeses: filtros.periodo, region: filtros.region, subarea: filtros.subarea, origen: filtros.origen }),
    [filtros],
  );

  const resumen = useResumenDns(api);
  const serie = useSerieDns(api);
  const patrones = usePatronesDns(api);
  const causas = useCausasDns(api);
  const zonas = useZonasDns(api);
  const cambios = useCambiosReporteDns(api);
  const modelo = useModeloDns(api);

  const seleccionarZona = (zona: ZonaDns) =>
    setFiltros(filtros.subarea === zona.codigo ? { ...filtros, subarea: null } : { ...filtros, region: zona.region, subarea: zona.codigo });

  const c = catalogo.datos;
  return (
    <div className="flex min-h-full flex-col">
      <Header
        titulo="Demanda no atendida (DNS)"
        subtitulo={
          c
            ? `Último evento: ${formatearFecha(c.fecha_corte)}${c.mes_corte_parcial ? " (mes en curso)" : ""} · ${c.subareas.length} subáreas`
            : "Cargando modelo…"
        }
      />

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 px-4 py-6 sm:px-6">
        {catalogo.error && (
          <div className="rounded-2xl border p-4 text-sm" style={{ borderColor: "var(--color-critico)", color: "var(--color-critico)" }}>
            No fue posible cargar el catálogo del modelo: {catalogo.error}
          </div>
        )}
        <FiltrosDnsPanel filtros={filtros} catalogo={c} onCambiar={setFiltros} />

        <KpisDns resumen={resumen} />

        <SerieDnsChart serie={serie} />

        <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-2">
          <ZonasDnsPanel zonas={zonas} subareaSeleccionada={filtros.subarea} onSeleccionar={seleccionarZona} />
          <CausasDnsPanel causas={causas} />
        </div>

        <PatronesDnsChart patrones={patrones} />

        <div className="grid grid-cols-1 items-start gap-5 xl:grid-cols-2">
          <CambiosReporteDnsPanel cambios={cambios} />
          <ModeloDnsPanel modelo={modelo} />
        </div>
      </main>

      <Footer>
        Fuente: SIMEM (eventos DNS y EDAC por subárea operativa) · modelo de priorización, patrones y pronóstico del Ministerio. Datos al último evento reportado.
      </Footer>
    </div>
  );
}
