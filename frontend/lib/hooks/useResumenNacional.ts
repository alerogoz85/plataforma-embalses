"use client";

import { obtenerResumenNacional, type FiltrosResumen } from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

export function useResumenNacional(filtros: FiltrosResumen) {
  return useAsyncResource(
    (signal) => obtenerResumenNacional(filtros, signal),
    [filtros.regiones?.join(","), filtros.embalses?.join(","), filtros.fecha],
  );
}
