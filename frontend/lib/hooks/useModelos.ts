"use client";

import { obtenerFichaModelo, obtenerResultadosModelo } from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

/** Ficha documentada de un modelo analítico (gas, optimización o apagón). */
export const useFichaModelo = (modeloId: string) => useAsyncResource((s) => obtenerFichaModelo(modeloId, s), [modeloId]);

/** Resultados importados del modelo; `disponible = false` cuando aún no se han importado. */
export const useResultadosModelo = (modeloId: string) => useAsyncResource((s) => obtenerResultadosModelo(modeloId, s), [modeloId]);
