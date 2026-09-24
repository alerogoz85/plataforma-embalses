import { vi } from "vitest";

type Manejador = (url: URL) => unknown | Promise<unknown>;

export interface RespuestaError {
  status: number;
  cuerpo?: unknown;
}

export function esError(valor: unknown): valor is RespuestaError {
  return typeof valor === "object" && valor !== null && "status" in valor;
}

/**
 * Simula fetch: enruta por `pathname` (coincidencia exacta) y devuelve el JSON
 * del manejador. Un manejador puede devolver `{ status, cuerpo }` para
 * simular una respuesta HTTP de error. Rutas sin manejador responden 404.
 */
export function simularFetch(rutas: Record<string, Manejador>) {
  const llamadas: URL[] = [];
  const doble = vi.fn(async (entrada: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(entrada));
    llamadas.push(url);
    if (init?.signal?.aborted) throw new DOMException("Aborted", "AbortError");
    const manejador = rutas[url.pathname];
    if (!manejador) return respuesta(404, { detalle: `sin ruta ${url.pathname}` }, "Not Found");
    const resultado = await manejador(url);
    if (esError(resultado)) return respuesta(resultado.status, resultado.cuerpo ?? null, "Error");
    return respuesta(200, resultado, "OK");
  });
  vi.stubGlobal("fetch", doble);
  return { fetch: doble, llamadas };
}

function respuesta(status: number, cuerpo: unknown, statusText: string) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    json: async () => cuerpo,
  } as Response;
}
