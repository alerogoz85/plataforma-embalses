"use client";

import { obtenerDetalleEmbalse } from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

export function useEmbalseDetalle(
  embalseId: string | null,
  rango: { fechaInicio?: string; fechaFin?: string } = {},
) {
  return useAsyncResource(
    (signal) => {
      if (!embalseId) return Promise.reject(new Error("Sin embalse seleccionado"));
      return obtenerDetalleEmbalse(embalseId, rango, signal);
    },
    [embalseId, rango.fechaInicio, rango.fechaFin],
  );
}
