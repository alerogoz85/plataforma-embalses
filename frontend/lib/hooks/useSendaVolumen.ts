"use client";

import { obtenerSendaVolumen } from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

export function useSendaVolumen(embalseId: string, horizonteMeses: number) {
  return useAsyncResource(
    (signal) => obtenerSendaVolumen(embalseId, horizonteMeses, signal),
    [embalseId, horizonteMeses],
  );
}
