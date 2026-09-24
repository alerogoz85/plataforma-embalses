"use client";

import { obtenerPrediccion } from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

export function usePrediccion(embalseId: string | null, horizonte: number) {
  return useAsyncResource(
    (signal) => {
      if (!embalseId) return Promise.reject(new Error("Sin embalse seleccionado"));
      return obtenerPrediccion(embalseId, horizonte, signal);
    },
    [embalseId, horizonte],
  );
}
