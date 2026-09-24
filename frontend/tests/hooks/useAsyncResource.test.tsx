import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useAsyncResource } from "@/lib/hooks/useAsyncResource";

function pendiente<T>() {
  let resolver!: (valor: T) => void;
  let rechazar!: (error: unknown) => void;
  const promesa = new Promise<T>((res, rej) => {
    resolver = res;
    rechazar = rej;
  });
  return { promesa, resolver, rechazar };
}

/** Fetcher que, como fetch real, rechaza con AbortError si se cancela. */
function fetcherCancelable<T>(promesa: Promise<T>) {
  return (signal: AbortSignal) =>
    new Promise<T>((resolver, rechazar) => {
      signal.addEventListener("abort", () => rechazar(new DOMException("Aborted", "AbortError")));
      promesa.then(resolver, rechazar);
    });
}

describe("useAsyncResource", () => {
  it("empieza cargando y sin datos ni error", () => {
    const { result } = renderHook(() => useAsyncResource(() => new Promise<string>(() => {}), []));
    expect(result.current).toEqual({ datos: null, error: null, cargando: true });
  });

  it("entrega los datos cuando la promesa se resuelve", async () => {
    const { result } = renderHook(() => useAsyncResource(async () => "listo", []));
    await waitFor(() => expect(result.current.cargando).toBe(false));
    expect(result.current).toEqual({ datos: "listo", error: null, cargando: false });
  });

  it("expone el mensaje del error cuando la promesa falla", async () => {
    const { result } = renderHook(() =>
      useAsyncResource(async () => {
        throw new Error("API caida");
      }, []),
    );
    await waitFor(() => expect(result.current.cargando).toBe(false));
    expect(result.current).toEqual({ datos: null, error: "API caida", cargando: false });
  });

  it("usa un mensaje generico si lo lanzado no es un Error", async () => {
    const { result } = renderHook(() =>
      useAsyncResource(async () => {
        throw "texto suelto";
      }, []),
    );
    await waitFor(() => expect(result.current.error).toBe("Error desconocido"));
  });

  it("pasa una senal de cancelacion al fetcher", async () => {
    const senales: AbortSignal[] = [];
    renderHook(() => useAsyncResource(async (senal) => { senales.push(senal); return 1; }, []));
    await waitFor(() => expect(senales).toHaveLength(1));
    expect(senales[0]).toBeInstanceOf(AbortSignal);
  });

  it("cancela la peticion pendiente al desmontar y no actualiza el estado", async () => {
    const { promesa, resolver } = pendiente<string>();
    let senal!: AbortSignal;
    const { result, unmount } = renderHook(() =>
      useAsyncResource((s) => {
        senal = s;
        return fetcherCancelable(promesa)(s);
      }, []),
    );
    unmount();
    expect(senal.aborted).toBe(true);
    resolver("tarde");
    await Promise.resolve();
    expect(result.current.datos).toBeNull();
  });

  it("no trata una cancelacion como error", async () => {
    const { promesa } = pendiente<string>();
    const { result, rerender } = renderHook(({ id }) => useAsyncResource(fetcherCancelable(promesa), [id]), {
      initialProps: { id: 1 },
    });
    rerender({ id: 2 }); // cancela la primera peticion
    await Promise.resolve();
    expect(result.current.error).toBeNull();
  });

  it("vuelve a pedir cuando cambian las dependencias y gana la ultima respuesta", async () => {
    const primera = pendiente<string>();
    const segunda = pendiente<string>();
    const { result, rerender } = renderHook(
      ({ id }) => useAsyncResource(fetcherCancelable(id === 1 ? primera.promesa : segunda.promesa), [id]),
      { initialProps: { id: 1 } },
    );

    rerender({ id: 2 });
    await act(async () => {
      segunda.resolver("segunda");
    });
    await waitFor(() => expect(result.current.datos).toBe("segunda"));

    await act(async () => {
      primera.resolver("primera (tardia)");
    });
    expect(result.current.datos).toBe("segunda");
  });

  it("no repite la peticion si las dependencias no cambian", async () => {
    const fetcher = vi.fn(async () => "x");
    const { rerender } = renderHook(({ id }) => useAsyncResource(fetcher, [id]), { initialProps: { id: 1 } });
    await waitFor(() => expect(fetcher).toHaveBeenCalledTimes(1));
    rerender({ id: 1 });
    rerender({ id: 1 });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("conserva los datos anteriores mientras recarga (sin parpadeo de esqueleto)", async () => {
    const segunda = pendiente<string>();
    const { result, rerender } = renderHook(
      ({ id }) => useAsyncResource((s) => (id === 1 ? Promise.resolve("uno") : fetcherCancelable(segunda.promesa)(s)), [id]),
      { initialProps: { id: 1 } },
    );
    await waitFor(() => expect(result.current.datos).toBe("uno"));
    rerender({ id: 2 });
    expect(result.current.datos).toBe("uno");
    expect(result.current.cargando).toBe(false);
  });
});
