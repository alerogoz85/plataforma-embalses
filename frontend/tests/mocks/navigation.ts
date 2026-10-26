import { useMemo, useSyncExternalStore } from "react";

/**
 * Doble de `next/navigation` para las pruebas: la «URL» vive en memoria y `router.replace` la cambia y avisa a quien la
 * lee, como haría el navegador. `fijarUrl` deja la dirección inicial de una prueba; `urlActual` la inspecciona.
 */
let ruta = "/";
let consulta = "";
const oyentes = new Set<() => void>();

const avisar = () => oyentes.forEach((o) => o());
const suscribir = (o: () => void) => {
  oyentes.add(o);
  return () => oyentes.delete(o);
};

const reemplazarOriginal = typeof window !== "undefined" ? window.history.replaceState.bind(window.history) : null;

export function fijarUrl(url: string): void {
  const [r, q = ""] = url.split("?");
  ruta = r || "/";
  consulta = q;
  reemplazarOriginal?.(null, "", urlActual()); // mantiene `window.location` igual que la URL en memoria
  avisar();
}

export const urlActual = () => (consulta ? `${ruta}?${consulta}` : ruta);
export const parametrosActuales = () => new URLSearchParams(consulta);

export function useSearchParams(): URLSearchParams {
  const texto = useSyncExternalStore(suscribir, () => consulta, () => consulta);
  return useMemo(() => new URLSearchParams(texto), [texto]);
}

export function usePathname(): string {
  return useSyncExternalStore(suscribir, () => ruta, () => ruta);
}

// Los tableros escriben la URL con `window.history.replaceState` (como documenta Next): aquí esa llamada actualiza la URL en memoria.
if (typeof window !== "undefined") {
  window.history.replaceState = (_datos: unknown, _titulo: string, url?: string | URL | null) => {
    if (url) fijarUrl(String(url));
  };
}

const router = {
  replace: (url: string) => fijarUrl(url),
  push: (url: string) => fijarUrl(url),
  back: () => {},
  forward: () => {},
  refresh: () => {},
  prefetch: () => {},
};

export const useRouter = () => router;
export const notFound = () => {
  throw new Error("NEXT_HTTP_ERROR_FALLBACK;404");
};
