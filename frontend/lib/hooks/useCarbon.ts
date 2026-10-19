"use client";

import {
  obtenerComparacionXm,
  obtenerInventarioCarbon,
  obtenerResumenCarbon,
  obtenerSerieCarbon,
  obtenerValidacionCarbon,
} from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

/** Un hook por endpoint del tablero de carbon; cada uno vuelve a consultar cuando cambia un filtro del que depende. */
export const useResumenCarbon = (horizonte: number, dias: number) =>
  useAsyncResource((s) => obtenerResumenCarbon(horizonte, dias, s), [horizonte, dias]);

export const useSerieCarbon = (historia: number, horizonte: number) =>
  useAsyncResource((s) => obtenerSerieCarbon(historia, horizonte, s), [historia, horizonte]);

export const useInventarioCarbon = (horizonte: number, dias: number) =>
  useAsyncResource((s) => obtenerInventarioCarbon(horizonte, dias, s), [horizonte, dias]);

export const useComparacionXm = (horizonte: number) =>
  useAsyncResource((s) => obtenerComparacionXm(horizonte, s), [horizonte]);

/** La validacion no depende de los filtros: es la evaluacion historica del modelo. */
export const useValidacionCarbon = () => useAsyncResource((s) => obtenerValidacionCarbon(s), []);
