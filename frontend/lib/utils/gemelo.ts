import type { MesEscenario, SemaforoApagon } from "@/lib/api/types";
import { formatearMes } from "./formatters";

/** Categorías del ONI, las mismas que usa el modelo (`CATEGORIAS_ONI`): son los rótulos de «Fase ENOS». */
const FASES: [number, string][] = [
  [2.0, "El Niño muy fuerte"], [1.5, "El Niño fuerte"], [1.0, "El Niño moderado"], [0.5, "El Niño débil"],
  [-0.5, "Neutral"], [-1.0, "La Niña débil"], [-1.5, "La Niña moderada"], [-2.0, "La Niña fuerte"],
];

export function faseEnso(oni: number): string {
  return FASES.find(([minimo]) => oni >= minimo)?.[1] ?? "La Niña muy fuerte";
}

export function formatearOni(oni: number): string {
  return `ONI ${oni > 0 ? "+" : ""}${oni.toFixed(1)}`;
}

export const COLOR_SEMAFORO: Record<SemaforoApagon, string> = {
  VERDE: "var(--color-optimo)",
  AMARILLO: "var(--color-alerta)",
  ROJO: "var(--color-critico)",
};

/** Umbrales de la leyenda del visor: déficit (verde < 10 %, amarillo 10-25 %, rojo ≥ 25 %) y apagón severo (< 3 %, 3-10 %, ≥ 10 %). */
export const UMBRALES_DEFICIT = [0.1, 0.25] as const;
export const UMBRALES_SEVERO = [0.03, 0.1] as const;

export function semaforoPorUmbral(probabilidad: number, [amarillo, rojo]: readonly [number, number]): SemaforoApagon {
  return probabilidad >= rojo ? "ROJO" : probabilidad >= amarillo ? "AMARILLO" : "VERDE";
}

export interface KpisEscenario {
  peorIndice: number;
  mesesRojo: number;
  maxProbDeficit: number;
  maxProbSevero: number;
}

export function kpisEscenario(meses: MesEscenario[]): KpisEscenario {
  return {
    peorIndice: Math.max(...meses.map((m) => m.indice_riesgo)),
    mesesRojo: meses.filter((m) => m.semaforo === "ROJO").length,
    maxProbDeficit: Math.max(...meses.map((m) => m.probabilidad_deficit)),
    maxProbSevero: Math.max(...meses.map((m) => m.probabilidad_apagon_severo)),
  };
}

const ROTULOS_FRANJA: Record<string, string> = {
  madrugada_00_05: "Madrugada 00–05",
  manana_06_11: "Mañana 06–11",
  tarde_12_17: "Tarde 12–17",
  pico_noche_18_21: "Pico noche 18–21",
  noche_22_23: "Noche 22–23",
};

export const rotuloFranja = (franja: string) => ROTULOS_FRANJA[franja] ?? franja;

/** «2026-10» -> «oct 2026» (como en los ejes del visor). */
export const rotuloMes = (mes: string) => formatearMes(mes).replace(".", "");

/** Color de una celda del mapa de calor: de blanco (0) a rojo oscuro (máximo), como la escala «Reds» del visor. */
export function colorCalor(valor: number, maximo: number): string {
  const t = maximo > 0 ? Math.min(1, Math.max(0, valor / maximo)) : 0;
  const [r0, g0, b0] = [255, 245, 240];
  const [r1, g1, b1] = [103, 0, 13];
  const mezclar = (a: number, b: number) => Math.round(a + (b - a) * t);
  return `rgb(${mezclar(r0, r1)}, ${mezclar(g0, g1)}, ${mezclar(b0, b1)})`;
}

/** Millones con un decimal: 7 000 000 -> «7M» (ejes de oferta y demanda). */
export const formatearMillones = (v: number) => `${Number((v / 1e6).toFixed(2))}M`;
