import type { BandaCarbon, ComparacionXm, SerieCarbon, UnidadCarbon } from "@/lib/api/types";

/**
 * Utilidades del tablero de carbon termico (funciones puras, sin React).
 *
 * El modelo trabaja en GBTU/dia (energia del carbon por dia). Para verlo en masa se divide por el
 * poder calorifico: kt/dia = GBTU/dia / (MBTU/t), porque 1 GBTU = 1000 MBTU y 1 kt = 1000 t.
 */

export const ETIQUETA_UNIDAD: Record<UnidadCarbon, string> = {
  gbtu: "GBTU/día",
  kt: "kt/día",
};

/** Convierte un consumo diario de GBTU/dia a la unidad elegida. */
export function convertirConsumo(gbtuDia: number, unidad: UnidadCarbon, poderCalorifico: number): number {
  return unidad === "gbtu" ? gbtuDia : gbtuDia / poderCalorifico;
}

export function convertirBanda(banda: BandaCarbon, unidad: UnidadCarbon, poderCalorifico: number): BandaCarbon {
  return {
    p10: convertirConsumo(banda.p10, unidad, poderCalorifico),
    p50: convertirConsumo(banda.p50, unidad, poderCalorifico),
    p90: convertirConsumo(banda.p90, unidad, poderCalorifico),
  };
}

/** Decimales utiles segun la unidad (la masa por dia es un numero pequeno). */
export const decimalesUnidad = (unidad: UnidadCarbon) => (unidad === "gbtu" ? 1 : 2);

export type NivelUsoTecho = "optimo" | "alerta" | "critico";

/**
 * Semaforo del uso del techo termico: menos de 85 % holgado, de 85 a 100 % ajustado,
 * mas de 100 % supera el techo. Se aplica al P50 (escenario central).
 */
export function nivelUsoTecho(usoPct: number): NivelUsoTecho {
  if (usoPct > 100) return "critico";
  if (usoPct >= 85) return "alerta";
  return "optimo";
}

export const COLOR_NIVEL: Record<NivelUsoTecho, string> = {
  optimo: "var(--color-optimo)",
  alerta: "var(--color-alerta)",
  critico: "var(--color-critico)",
};

export const ETIQUETA_NIVEL: Record<NivelUsoTecho, string> = {
  optimo: "Holgado",
  alerta: "Ajustado",
  critico: "Supera el techo",
};

/** Etiqueta de trimestre «2026Q4» (o «2026-Q4») -> «T4 2026». Otro formato se muestra tal cual. */
export function etiquetaTrimestre(trimestre: string): string {
  const m = /^(\d{4})-?Q([1-4])$/.exec(trimestre);
  return m ? `T${m[2]} ${m[1]}` : trimestre;
}

/** «2026-10-01» -> «oct 2026» (eje mensual). */
export function etiquetaMesCarbon(fechaISO: string): string {
  const fecha = new Date(`${fechaISO}T00:00:00`);
  return new Intl.DateTimeFormat("es-CO", { month: "short", year: "numeric" }).format(fecha).replace(".", "");
}

/** Punto del grafico principal. Los campos opcionales dejan huecos (no ceros) donde no hay dato. */
export interface PuntoSerieCarbon {
  fecha: string;
  mesLabel: string;
  observado?: number;
  p50?: number;
  /** Base y alto de la banda P10-P90 apilada (la base es transparente). */
  bandaBase?: number;
  bandaRango?: number;
}

/**
 * Une la historia mensual (solo meses completos: un mes en curso no es comparable) con la
 * proyeccion P50 y su banda P10-P90, convertidos a la unidad elegida. Entre ambas se inserta
 * un punto puente en el ultimo mes observado para que la linea proyectada nazca de la historica.
 */
export function construirPuntosSerie(serie: SerieCarbon, unidad: UnidadCarbon): PuntoSerieCarbon[] {
  const pc = serie.poder_calorifico_mbtu_t;
  const conv = (v: number) => convertirConsumo(v, unidad, pc);

  const historicos: PuntoSerieCarbon[] = serie.historico
    .filter((h) => h.mes_completo)
    .map((h) => ({ fecha: h.fecha, mesLabel: etiquetaMesCarbon(h.fecha), observado: conv(h.carbon_gbtu_dia) }));

  const proyectados: PuntoSerieCarbon[] = serie.proyeccion.map((p) => {
    const banda = convertirBanda(p.carbon_gbtu_dia, unidad, pc);
    return {
      fecha: p.fecha,
      mesLabel: etiquetaMesCarbon(p.fecha),
      p50: banda.p50,
      bandaBase: banda.p10,
      bandaRango: Math.max(0, banda.p90 - banda.p10),
    };
  });

  if (historicos.length === 0 || proyectados.length === 0) return [...historicos, ...proyectados];
  const ultimo = historicos[historicos.length - 1];
  const puente = { ...ultimo, p50: ultimo.observado, bandaBase: ultimo.observado, bandaRango: 0 };
  return [...historicos.slice(0, -1), puente, ...proyectados];
}

/** Punto del grafico de comparacion con XM (modelo P50 y banda frente al caso estocastico de XM). */
export interface PuntoComparacionXm {
  fecha: string;
  mesLabel: string;
  p50: number;
  bandaBase: number;
  bandaRango: number;
  xm?: number;
}

export function construirPuntosXm(filas: ComparacionXm[], unidad: UnidadCarbon, poderCalorifico: number): PuntoComparacionXm[] {
  const conv = (v: number) => convertirConsumo(v, unidad, poderCalorifico);
  return filas.map((f) => {
    const banda = convertirBanda(f.modelo, unidad, poderCalorifico);
    return {
      fecha: f.fecha,
      mesLabel: etiquetaMesCarbon(f.fecha),
      p50: banda.p50,
      bandaBase: banda.p10,
      bandaRango: Math.max(0, banda.p90 - banda.p10),
      xm: f.xm_estocastico_gbtu_dia === null ? undefined : conv(f.xm_estocastico_gbtu_dia),
    };
  });
}
