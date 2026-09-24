"use client";

import { obtenerFuenteDatos } from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

export function useFuenteDatos() {
  return useAsyncResource((signal) => obtenerFuenteDatos(signal), []);
}
