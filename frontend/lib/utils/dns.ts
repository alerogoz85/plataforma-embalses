import type { MesDns, SerieDns } from "@/lib/api/types";

/** Utilidades del tablero de demanda no atendida (DNS): funciones puras, sin React. */

export type MedidaDns = "eventos" | "energia";

export const ETIQUETA_MEDIDA: Record<MedidaDns, string> = {
  eventos: "Eventos",
  energia: "Energía no atendida (GWh)",
};

/** «2026-08» -> «ago 2026» (eje mensual; sin el «de» que pone Intl para que quepa en el eje). */
export function etiquetaMesDns(mes: string): string {
  const fecha = new Date(`${mes}-01T00:00:00`);
  return new Intl.DateTimeFormat("es-CO", { month: "short", year: "2-digit" }).format(fecha).replace(".", "").replace(" de ", " ");
}

/** Variación con signo y un decimal («+17,9 %»); «—» cuando no hay base de comparación. */
export function formatearVariacionPct(valor: number | null): string {
  if (valor === null) return "—";
  const signo = valor > 0 ? "+" : valor < 0 ? "−" : "";
  return `${signo}${Math.abs(valor).toLocaleString("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %`;
}

/** En DNS, más eventos o más energía es peor: la variación «buena» es la que no sube. */
export const esMejora = (variacionPct: number | null) => variacionPct !== null && variacionPct <= 0;

export interface PuntoSerieDns {
  mes: string;
  mesLabel: string;
  valor?: number;
  noProgramados?: number;
  parcial?: boolean;
  pronostico?: number;
}

/**
 * Puntos del gráfico mensual para la medida elegida. El pronóstico del modelo se pone en su mes
 * (si el mes no está en la ventana elegida se agrega al final) como un punto aparte, nunca mezclado
 * con lo observado.
 */
export function construirPuntosSerieDns(serie: SerieDns, medida: MedidaDns): PuntoSerieDns[] {
  const valorDe = (m: MesDns) => (medida === "eventos" ? m.eventos : m.energia_gwh);
  const puntos: PuntoSerieDns[] = serie.meses.map((m) => ({
    mes: m.mes,
    mesLabel: etiquetaMesDns(m.mes),
    valor: valorDe(m),
    noProgramados: medida === "eventos" ? m.eventos_no_programados : undefined,
    parcial: m.parcial,
  }));
  const p = serie.pronostico;
  if (p) {
    const valor = medida === "eventos" ? p.eventos : p.energia_gwh;
    const existente = puntos.find((x) => x.mes === p.mes);
    if (existente) existente.pronostico = valor;
    else puntos.push({ mes: p.mes, mesLabel: etiquetaMesDns(p.mes), pronostico: valor });
  }
  return puntos;
}

/** Color de una zona: rojo si su energía de los últimos 24 meses empeoró frente a los 24 previos, azul si no. */
export const colorTendenciaZona = (variacionPct: number) => (variacionPct > 0 ? "var(--color-critico)" : "var(--chart-volumen)");

/** Nombre legible de una causa («atmosferica» -> «Atmosférica»). */
const NOMBRES_CAUSA: Record<string, string> = {
  mantenimiento: "Mantenimiento",
  fallas: "Fallas",
  atmosferica: "Atmosférica",
  desconocido: "Desconocida",
};
export const nombreCausa = (causa: string) => NOMBRES_CAUSA[causa] ?? causa.charAt(0).toUpperCase() + causa.slice(1);

export const COLOR_CAUSA: Record<string, string> = {
  mantenimiento: "var(--chart-volumen)",
  fallas: "var(--color-critico)",
  atmosferica: "var(--color-alerta)",
  desconocido: "var(--foreground-muted)",
};

export const NOMBRES_ORIGEN_CAUSA: Record<string, string> = {
  reportada: "Reportada por el operador",
  "inferida (TF-IDF)": "Inferida del texto (modelo de lenguaje TF-IDF)",
  "inferida (regex)": "Inferida del texto (reglas)",
  "sin clasificar": "Sin clasificar",
};
