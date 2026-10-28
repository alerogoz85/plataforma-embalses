"use client";

import { useMemo } from "react";

import { KpiCard } from "@/components/dashboard/KpiCard";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { FichaPanel } from "@/components/modelos/FichaPanel";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { CatalogoEscenarios, FichaModelo, ModoOni } from "@/lib/api/types";
import { useEstadoUrl, type EsquemaUrl } from "@/lib/hooks/useEstadoUrl";
import { useEscenarioApagon } from "@/lib/hooks/useModelos";
import { kpisEscenario } from "@/lib/utils/gemelo";
import { enLista } from "@/lib/utils/url";
import { AYUDAS_APAGON } from "./ayudasApagon";
import { GraficoIndiceRiesgo, GraficoOfertaDemanda, GraficoProbabilidades, MapaCalorDeficit } from "./GraficosEscenario";
import { PanelControles, type EstadoControles } from "./PanelControles";
import { TablaMensualEscenario } from "./TablaMensualEscenario";

/** Los cuatro controles viven en la URL (`?modo=manual&oni=1.5&simulaciones=2000&horizonte=18`); un valor fuera de las opciones se ignora. */
function construirEsquema(c: CatalogoEscenarios): EsquemaUrl<EstadoControles> {
  const valoresOni = new Set(Array.from({ length: Math.round((c.oni_maximo - c.oni_minimo) / c.oni_paso) + 1 }, (_, i) => Math.round((c.oni_minimo + i * c.oni_paso) * 10) / 10));
  return {
    // «Manual» es el modo con el que abre el visor: es el único donde el ONI se mueve.
    modo: { param: "modo", defecto: () => "manual" as ModoOni, leer: enLista(c.modos) },
    oni: {
      param: "oni", defecto: () => c.oni_por_defecto,
      leer: (crudo) => (/^-?\d+(\.\d)?$/.test(crudo) && valoresOni.has(Number(crudo)) ? Number(crudo) : undefined),
      escribir: (v) => v.toFixed(1),
    },
    simulaciones: { param: "simulaciones", defecto: () => c.simulaciones_por_defecto, leer: (crudo) => c.simulaciones.find((s) => String(s) === crudo) },
    horizonte: { param: "horizonte", defecto: () => c.horizonte_por_defecto, leer: (crudo) => c.horizontes.find((h) => String(h) === crudo) },
  };
}

const porcentaje = (v: number) => `${Math.round(v * 100)} %`;

/**
 * Visor interactivo del riesgo de apagón: menú izquierdo con los controles del modelo (modo de ONI, ONI, simulaciones, horizonte) y, a la
 * derecha, indicadores, índice por mes, probabilidades, mapa de calor por franja horaria y oferta frente a demanda. Cada combinación
 * de controles tiene su corrida del modelo ya calculada: aquí solo se pide y se dibuja, no se recalcula nada.
 */
export function GemeloApagon({ catalogo, ficha }: { catalogo: CatalogoEscenarios; ficha: FichaModelo | null }) {
  const esquema = useMemo(() => construirEsquema(catalogo), [catalogo]);
  const [controles, { actualizar, restablecer }] = useEstadoUrl(esquema);
  const escenario = useEscenarioApagon(controles);
  const e = escenario.datos;
  const kpis = useMemo(() => (e ? kpisEscenario(e.meses) : null), [e]);
  const fuente = catalogo.fuente;

  return (
    <div className="flex min-h-full flex-col">
      <Header titulo="Riesgo de apagón condicionado por ENOS" subtitulo="Gemelo digital · escenarios del modelo Monte Carlo" />

      <main className="mx-auto grid w-full max-w-7xl flex-1 grid-cols-1 gap-5 px-4 py-6 sm:px-6 lg:grid-cols-[17rem_minmax(0,1fr)]">
        <PanelControles catalogo={catalogo} estado={controles} onCambio={actualizar} onRestablecer={restablecer} />

        <div className="flex min-w-0 flex-col gap-5">
          <div>
            <h1 className="text-2xl font-bold leading-tight text-foreground sm:text-3xl">Gemelo digital de riesgo de apagón — visor interactivo</h1>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-foreground-muted">
              Mueve el ONI y el visor muestra la corrida del modelo para ese escenario: el semáforo de riesgo, el mapa de calor de déficit por franja horaria y las bandas
              P10–P50–P90. Escenario analítico, <b>no</b> un pronóstico oficial del mercado.
            </p>
          </div>

          {escenario.error && <ErrorBloque que="el escenario del modelo" mensaje={escenario.error} />}
          {!e && !escenario.error && <SkeletonChart />}

          {e && kpis && (
            <>
              <section aria-label="Indicadores del escenario" className="grid grid-cols-2 gap-4 xl:grid-cols-4">
                <KpiCard etiqueta="Peor índice de riesgo" valor={`${Math.round(kpis.peorIndice)}/100`} ayuda={AYUDAS_APAGON.peorIndice} />
                <KpiCard etiqueta="Meses en ROJO" valor={String(kpis.mesesRojo)} ayuda={AYUDAS_APAGON.mesesRojo} />
                <KpiCard etiqueta="Máx. prob. de déficit" valor={porcentaje(kpis.maxProbDeficit)} />
                <KpiCard etiqueta="Máx. prob. apagón severo" valor={porcentaje(kpis.maxProbSevero)} />
              </section>

              <GraficoIndiceRiesgo meses={e.meses} />
              <GraficoProbabilidades meses={e.meses} />
              <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
                <MapaCalorDeficit meses={e.meses} franjas={catalogo.franjas} />
                <GraficoOfertaDemanda meses={e.meses} />
              </div>
              <TablaMensualEscenario meses={e.meses} />
            </>
          )}

          {fuente && (
            <p className="text-xs leading-relaxed text-foreground-muted">
              Fuente: modelo Monte Carlo <code>6. modelo_riesgo_apagon_montecarlo.py</code> sobre <code>base_modelo_riesgo_apagon_nacional.parquet</code>.
              {fuente.ultimo_oni_observado !== null && <> Último ONI observado: {fuente.ultimo_oni_observado.toFixed(1)}.</>}
              {fuente.ultimo_mes_demanda && <> Último mes de demanda: {fuente.ultimo_mes_demanda.slice(0, 7)}.</>}
              {e && <> {e.simulaciones.toLocaleString("es-CO")} simulaciones · horizonte {e.horizonte} meses.</>} Escenario analítico interno, no pronóstico oficial del
              mercado.
            </p>
          )}

          {ficha && <FichaPanel ficha={ficha} />}
        </div>
      </main>

      <Footer>Fuente: documentos y salidas del modelo (CRISP-DM) del Ministerio de Minas y Energía. La plataforma muestra solo lo que el modelo entregó.</Footer>
    </div>
  );
}
