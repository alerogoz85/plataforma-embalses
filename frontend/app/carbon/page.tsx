"use client";

import { useState } from "react";

import { ComparacionXmChart } from "@/components/carbon/ComparacionXmChart";
import { FILTROS_CARBON_POR_DEFECTO, FiltrosCarbonPanel, type FiltrosCarbon } from "@/components/carbon/FiltrosCarbon";
import { InventarioChart } from "@/components/carbon/InventarioChart";
import { KpisCarbon } from "@/components/carbon/KpisCarbon";
import { SerieCarbonChart } from "@/components/carbon/SerieCarbonChart";
import { SupuestosCarbon } from "@/components/carbon/SupuestosCarbon";
import { TrimestresChart } from "@/components/carbon/TrimestresChart";
import { ValidacionCarbonPanel } from "@/components/carbon/ValidacionCarbonPanel";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { useResumenCarbon } from "@/lib/hooks/useCarbon";
import { etiquetaMesCarbon } from "@/lib/utils/carbon";

/**
 * Tablero «Modelo de carbón térmico». Misma estructura que el de embalses:
 * encabezado -> filtros globales -> tarjetas -> graficos -> detalle (validacion y supuestos).
 *
 * Los filtros viven aqui, en un solo estado, y se pasan a cada bloque: asi todos los graficos
 * responden al mismo tiempo. El resumen se consulta una vez y alimenta tarjetas y trimestres.
 */
export default function CarbonPage() {
  const [filtros, setFiltros] = useState<FiltrosCarbon>(FILTROS_CARBON_POR_DEFECTO);
  const resumen = useResumenCarbon(filtros.horizonte, filtros.dias);

  return (
    <div className="flex min-h-full flex-col">
      <Header
        titulo="Modelo de carbón térmico"
        subtitulo={
          resumen.datos
            ? `Último dato: ${etiquetaMesCarbon(resumen.datos.ultimo_observado.fecha)}${resumen.datos.ultimo_observado.mes_completo ? "" : " (mes en curso)"} · proyección a ${resumen.datos.horizonte_meses} ${resumen.datos.horizonte_meses === 1 ? "mes" : "meses"}`
            : "Cargando modelo…"
        }
      />

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 px-4 py-6 sm:px-6">
        <FiltrosCarbonPanel filtros={filtros} onCambiar={setFiltros} />

        <KpisCarbon resumen={resumen} unidad={filtros.unidad} dias={filtros.dias} />

        <SerieCarbonChart historia={filtros.historia} horizonte={filtros.horizonte} unidad={filtros.unidad} />

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <TrimestresChart resumen={resumen} />
          <InventarioChart horizonte={filtros.horizonte} dias={filtros.dias} />
        </div>

        <ComparacionXmChart horizonte={filtros.horizonte} unidad={filtros.unidad} poderCalorifico={resumen.datos?.poder_calorifico_mbtu_t ?? null} />

        <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-2">
          <ValidacionCarbonPanel />
          <SupuestosCarbon />
        </div>
      </main>

      <Footer>Fuente: modelo de carbón térmico (ENOS → aportes → uso del techo → consumo) · referencias de XM. Proyección con escenarios P10/P50/P90.</Footer>
    </div>
  );
}
