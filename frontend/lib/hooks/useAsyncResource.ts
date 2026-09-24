"use client";

import { useEffect, useState } from "react";

interface Resultado<T> {
  datos: T | null;
  error: string | null;
  cargando: boolean;
}

export function useAsyncResource<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  deps: React.DependencyList,
) {
  const [resultado, setResultado] = useState<Resultado<T>>({
    datos: null,
    error: null,
    cargando: true,
  });

  useEffect(() => {
    const controlador = new AbortController();

    fetcher(controlador.signal)
      .then((datos) => setResultado({ datos, error: null, cargando: false }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const mensaje = error instanceof Error ? error.message : "Error desconocido";
        setResultado({ datos: null, error: mensaje, cargando: false });
      });

    return () => controlador.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return resultado;
}
