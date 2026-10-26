import type { EstadoModelo, GraficoModelo, NivelIndicador, PuntoSerieModelo, SerieModelo, TablaModelo } from "@/lib/api/types";
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

/** Meses (AAAA-MM) presentes en alguna serie o línea de gráfico, ordenados: son las opciones de los filtros Desde y Hasta. */
export function opcionesPeriodo(series: SerieModelo[], graficos: GraficoModelo[] = []): string[] {
  const todos = new Set<string>();
  for (const s of series) for (const p of s.puntos) if (MESES.test(p.x)) todos.add(p.x);
  for (const g of graficos) for (const l of g.lineas) for (const p of l.puntos) if (MESES.test(p.x)) todos.add(p.x);
  return [...todos].sort();
}

const dentro = (x: string, desde: string, hasta: string) => (!desde || x >= desde) && (!hasta || x <= hasta);

/** Recorta cada serie al rango [desde, hasta] (inclusive). Una cadena vacía deja ese extremo abierto. */
export function filtrarSeries(series: SerieModelo[], desde: string, hasta: string): SerieModelo[] {
  return series.map((s) => ({ ...s, puntos: s.puntos.filter((p) => dentro(p.x, desde, hasta)) }));
}

/** Recorta las líneas de cada gráfico al rango; una línea sin puntos en el rango se quita (el gráfico se conserva para avisar «sin datos»). */
export function recortarGraficos(graficos: GraficoModelo[], desde: string, hasta: string): GraficoModelo[] {
  return graficos.map((g) => ({
    ...g,
    lineas: g.lineas.map((l) => ({ ...l, puntos: l.puntos.filter((p) => dentro(p.x, desde, hasta)) })).filter((l) => l.puntos.length > 0),
  }));
}

/** Gráficos que corresponden a las opciones elegidas: uno sin etiquetas se muestra siempre; uno con etiquetas solo si todas coinciden. */
export function graficosVisibles(graficos: GraficoModelo[], seleccion: Record<string, string>): GraficoModelo[] {
  return graficos.filter((g) => Object.entries(g.etiquetas).every(([dimension, valor]) => !(dimension in seleccion) || seleccion[dimension] === valor));
}

/** Filas de una tabla que corresponden a las opciones elegidas (según las columnas que la tabla declara como filtro). */
export function filasVisibles(tabla: TablaModelo, seleccion: Record<string, string>): TablaModelo["filas"] {
  const filtros = Object.entries(tabla.filtros_columna)
    .filter(([dimension]) => dimension in seleccion)
    .map(([dimension, columna]) => [tabla.columnas.indexOf(columna), seleccion[dimension]] as const)
    .filter(([indice]) => indice >= 0);
  return filtros.length === 0 ? tabla.filas : tabla.filas.filter((fila) => filtros.every(([indice, valor]) => String(fila[indice]) === valor));
}

export interface LineaDatos {
  clave: string;
  nombre: string;
  estilo: "continua" | "punteada";
  /** Tiene banda P10-P90 (se dibujan `${clave}_base` y `${clave}_rango`). */
  banda: boolean;
}

/**
 * Convierte un gráfico de varias líneas al formato de Recharts: una fila por mes (unión de todas las líneas) y una columna por línea.
 * Donde una línea no tiene dato la columna queda vacía (hueco), nunca cero.
 */
export function construirDatosGrafico(grafico: GraficoModelo): { datos: Record<string, number | string>[]; lineas: LineaDatos[] } {
  const lineas: LineaDatos[] = grafico.lineas.map((l, i) => ({
    clave: `l${i}`,
    nombre: l.nombre,
    estilo: l.estilo,
    banda: l.puntos.some((p) => p.p10 !== null && p.p90 !== null),
  }));
  const porX = new Map<string, Record<string, number | string>>();
  grafico.lineas.forEach((l, i) => {
    for (const p of l.puntos) {
      const fila = porX.get(p.x) ?? { x: p.x, etiqueta: etiquetaX(p.x) };
      fila[`l${i}`] = p.y;
      if (p.p10 !== null && p.p90 !== null) {
        fila[`l${i}_base`] = p.p10;
        fila[`l${i}_rango`] = Math.max(0, p.p90 - p.p10);
      }
      porX.set(p.x, fila);
    }
  });
  return { datos: [...porX.values()].sort((a, b) => String(a.x).localeCompare(String(b.x))), lineas };
}

/** Un valor de semáforo («Verde», «Amarillo», «Rojo») en una tabla: se pinta como insignia con su texto (no solo color). */
export const SEMAFOROS: Record<string, { color: string; fondo: string }> = {
  Verde: { color: "var(--color-optimo)", fondo: "var(--color-optimo-bg)" },
  Amarillo: { color: "var(--color-alerta)", fondo: "var(--color-alerta-bg)" },
  Rojo: { color: "var(--color-critico)", fondo: "var(--color-critico-bg)" },
};

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
