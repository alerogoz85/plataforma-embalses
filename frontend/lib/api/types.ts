// Clasificacion del %V. util: Normal >80, Estable 70-80, Alerta temprana 60-70, Situacion delicada 50-60, Critico <50.
export type NivelRiesgo = "NORMAL" | "ESTABLE" | "ALERTA_TEMPRANA" | "SITUACION_DELICADA" | "CRITICO";

export interface EmbalseResumen {
  id: string;
  nombre: string;
  region: string;
  es_agregado: boolean;
  fecha: string;
  pct_volumen_util: number;
  nivel_riesgo: NivelRiesgo;
  volumen_util_mm3: number;
  capacidad_util_mm3: number;
  energia_util_gwh: number | null;
  aportes_m3s: number | null;
  aportes_pct_media: number | null;
  vertimientos_m3s: number | null;
  turbinado_m3s: number | null;
  dias_autonomia: number | null;
  delta_diario_pct: number;
  delta_semanal_pct: number;
}

export interface RegionResumen {
  region: string;
  pct_volumen_util: number;
  aportes_pct_media: number | null;
  nivel_riesgo: NivelRiesgo;
  num_embalses: number;
  energia_util_gwh: number;
}

export interface KpiNacional {
  fecha_corte: string;
  pct_volumen_util_nacional: number;
  delta_diario_pct: number;
  delta_semanal_pct: number;
  aportes_pct_media_nacional: number | null;
  capacidad_guardada_gwh: number;
  nivel_riesgo_sistema: NivelRiesgo;
  total_embalses: number;
}

export interface ResumenNacional {
  kpis: KpiNacional;
  regiones: RegionResumen[];
  embalses: EmbalseResumen[];
}

export interface SeriePunto {
  fecha: string;
  pct_volumen_util: number;
  energia_util_gwh: number | null;
  aportes_m3s: number | null;
  aportes_pct_media: number | null;
  vertimientos_m3s: number | null;
  turbinado_m3s: number | null;
}

export interface EmbalseDetalle {
  resumen: EmbalseResumen;
  serie_historica: SeriePunto[];
}

export interface PrediccionPunto {
  fecha: string;
  valor_esperado: number;
  limite_inferior: number;
  limite_superior: number;
}

export interface Prediccion {
  embalse_id: string;
  horizonte_dias: number;
  /** null cuando la proyección es la de Outputs: sus límites son escenarios P10/P90, no un IC. */
  nivel_confianza: number | null;
  generado_en: string;
  metodo: string;
  puntos: PrediccionPunto[];
  /** "outputs": modelo de largo plazo interpolado a diario; "holt_winters": respaldo estadístico. */
  origen: OrigenProyeccion;
}

export const REGIONES: string[] = ["Antioquia", "Caldas", "Caribe", "Centro", "Oriente", "Valle"];
// 1, 3, 6 y 12 meses, con el mes comercial de 30 dias (lo que espera la API).
export const HORIZONTES_PREDICCION = [30, 90, 180, 360] as const;
export type HorizontePrediccion = (typeof HORIZONTES_PREDICCION)[number];

export interface PuntoMensual {
  mes: string; // "YYYY-MM"
  pct_volumen_util: number;
}

export interface PuntoProyeccionMensual {
  mes: string; // "YYYY-MM"
  valor_esperado: number;
  limite_inferior: number;
  limite_superior: number;
}

export interface MetricaValidacion {
  modelo: string;
  mae: number;
  r2: number;
}

export interface SendaVolumen {
  embalse_id: string;
  nombre: string;
  metodo: string;
  generado_en: string;
  ultimo_observado: PuntoMensual;
  minimo_proyectado: PuntoProyeccionMensual;
  historico: PuntoMensual[];
  proyeccion: PuntoProyeccionMensual[];
  validacion: MetricaValidacion[];
  /** "outputs": modelo de largo plazo (limites = escenarios P10/P90); "holt_winters": respaldo estadístico (IC 95%). */
  origen_proyeccion: OrigenProyeccion;
  /** Meses proyectados de verdad: una corrida de Outputs puede publicar menos de los pedidos. */
  horizonte_efectivo_meses: number;
}

export type OrigenProyeccion = "outputs" | "holt_winters";

export const ID_TOTAL_NACIONAL = "TOTAL";
/** Id del agregado de una región ("Todos los embalses" con una región elegida). */
export const idAgregadoRegion = (region: string) => `REGION:${region}`;
export const HORIZONTES_SENDA_VOLUMEN = [1, 3, 6, 12] as const;
export type HorizonteSendaVolumen = (typeof HORIZONTES_SENDA_VOLUMEN)[number];

export interface FuenteDatos {
  fuente: string;
  descripcion: string;
  es_real: boolean;
  fecha_corte: string | null;
  actualizado_en: string | null;
}
