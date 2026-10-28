"use client";

import {
  obtenerCatalogoEscenariosApagon,
  obtenerEscenarioApagon,
  obtenerFichaModelo,
  obtenerResultadosModelo,
  type ParametrosEscenario,
} from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

/** Ficha documentada de un modelo analítico (gas, optimización o apagón). */
export const useFichaModelo = (modeloId: string) => useAsyncResource((s) => obtenerFichaModelo(modeloId, s), [modeloId]);

/** Resultados importados del modelo; `disponible = false` cuando aún no se han importado. */
export const useResultadosModelo = (modeloId: string) => useAsyncResource((s) => obtenerResultadosModelo(modeloId, s), [modeloId]);

/** Opciones de los controles del visor de apagón; `disponible = false` mientras no se importen los escenarios. */
export const useCatalogoEscenariosApagon = () => useAsyncResource((s) => obtenerCatalogoEscenariosApagon(s), []);

/** Escenario del modelo para una combinación de controles (el modelo ya lo calculó; aquí solo se pide). */
export const useEscenarioApagon = (p: ParametrosEscenario) =>
  useAsyncResource((s) => obtenerEscenarioApagon(p, s), [p.modo, p.modo === "manual" ? p.oni : null, p.simulaciones, p.horizonte]);
