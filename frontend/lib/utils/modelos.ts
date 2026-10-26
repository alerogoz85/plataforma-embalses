import type { EstadoModelo, NivelIndicador, PuntoSerieModelo, SerieModelo } from "@/lib/api/types";
import { formatearFechaCorta } from "@/lib/utils/formatters";

/** Utilidades de los tableros de modelos analíticos (gas, optimización, apagón): funciones puras, sin React. */

export const ETIQUETA_ESTADO: Record<EstadoModelo, string> = {
  sin_resultados: "Sin resultados publicados",
  prueba_tecnica: "Prueba técnica: no publicable",
  con_resultados: "Con resultados importados",
};

/** Color del estado: ámbar cuando falta algo, rojo si la corrida está marcada como no publicable, verde si hay resultados. */
export const COLOR_ESTADO: Record<EstadoModelo, string> = {
  sin_resultados: "var(--color-alerta)",
  prueba_tecnica: "var(--color-critico)",
  con_resultados: "var(--color-optimo)",
};

export const COLOR_NIVEL_INDICADOR: Record<NivelIndicador, string> = {
  ok: "var(--color-optimo)",
  alerta: "var(--color-alerta)",
  critico: "var(--color-critico)",
};

const MESES = /^\d{4}-\d{2}$/;
const DIAS = /^\d{4}-\d{2}-\d{2}$/;

/** «2026-10» -> «oct 26»; «2026-10-05» -> «05 oct»; otra cosa se muestra tal cual. */
export function etiquetaX(x: string): string {
  if (MESES.test(x)) {
    return new Intl.DateTimeFormat("es-CO", { month: "short", year: "2-digit" }).format(new Date(`${x}-01T00:00:00`)).replace(".", "").replace(" de ", " ");
  }
  return DIAS.test(x) ? formatearFechaCorta(x) : x;
}

/** Meses (AAAA-MM) presentes en alguna serie, ordenados: son las opciones de los filtros Desde y Hasta. */
export function opcionesPeriodo(series: SerieModelo[]): string[] {
  const todos = new Set<string>();
  for (const s of series) for (const p of s.puntos) if (MESES.test(p.x)) todos.add(p.x);
  return [...todos].sort();
}

/** Recorta cada serie al rango [desde, hasta] (inclusive). Una cadena vacía deja ese extremo abierto. */
export function filtrarSeries(series: SerieModelo[], desde: string, hasta: string): SerieModelo[] {
  return series.map((s) => ({
    ...s,
    puntos: s.puntos.filter((p) => (!desde || p.x >= desde) && (!hasta || p.x <= hasta)),
  }));
}

export interface PuntoGraficoModelo {
  x: string;
  etiqueta: string;
  valor: number;
  /** Banda P10-P90 apilada: base transparente + rango. */
  bandaBase?: number;
  bandaRango?: number;
}

export function construirPuntosModelo(puntos: PuntoSerieModelo[]): PuntoGraficoModelo[] {
  return puntos.map((p) => ({
    x: p.x,
    etiqueta: etiquetaX(p.x),
    valor: p.y,
    ...(p.p10 !== null && p.p90 !== null ? { bandaBase: p.p10, bandaRango: Math.max(0, p.p90 - p.p10) } : {}),
  }));
}

export const tieneBanda = (puntos: PuntoSerieModelo[]) => puntos.some((p) => p.p10 !== null && p.p90 !== null);
