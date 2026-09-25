import type { NivelRiesgo } from "@/lib/api/types";

export function formatearPorcentaje(valor: number, decimales = 1): string {
  return `${valor.toFixed(decimales)}%`;
}

export const SIN_DATO = "—";

export function formatearNumeroOpcional(valor: number | null, decimales = 1): string {
  return valor === null ? SIN_DATO : formatearNumero(valor, decimales);
}

export function formatearPorcentajeOpcional(valor: number | null, decimales = 1): string {
  return valor === null ? SIN_DATO : formatearPorcentaje(valor, decimales);
}

export function formatearNumero(valor: number, decimales = 1): string {
  return new Intl.NumberFormat("es-CO", {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(valor);
}

export function formatearDelta(valor: number, decimales = 2): string {
  const signo = valor > 0 ? "+" : "";
  return `${signo}${valor.toFixed(decimales)} p.p.`;
}

export function formatearFecha(iso: string): string {
  const fecha = new Date(`${iso}T00:00:00`);
  return new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "short", year: "numeric" }).format(
    fecha,
  );
}

export function formatearFechaCorta(iso: string): string {
  const fecha = new Date(`${iso}T00:00:00`);
  return new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "short" }).format(fecha);
}

export function formatearMes(mes: string): string {
  const fecha = new Date(`${mes}-01T00:00:00`);
  return new Intl.DateTimeFormat("es-CO", { month: "short", year: "numeric" }).format(fecha);
}

const ETIQUETAS_RIESGO: Record<NivelRiesgo, string> = {
  NORMAL: "Normal",
  ESTABLE: "Estable",
  ALERTA_TEMPRANA: "Alerta temprana",
  SITUACION_DELICADA: "Situación delicada",
  CRITICO: "Crítico",
};

/** Rango de %V. util de cada nivel, tal como se muestra en las ayudas y en la guia. */
export const RANGO_RIESGO: Record<NivelRiesgo, string> = {
  NORMAL: "> 80 %",
  ESTABLE: "70 – 80 %",
  ALERTA_TEMPRANA: "60 – 70 %",
  SITUACION_DELICADA: "50 – 60 %",
  CRITICO: "< 50 %",
};

export function etiquetaRiesgo(nivel: NivelRiesgo): string {
  return ETIQUETAS_RIESGO[nivel];
}

export const COLOR_VAR_RIESGO: Record<NivelRiesgo, { texto: string; fondo: string; borde: string }> = {
  NORMAL: { texto: "var(--riesgo-normal)", fondo: "var(--riesgo-normal-bg)", borde: "var(--riesgo-normal)" },
  ESTABLE: { texto: "var(--riesgo-estable)", fondo: "var(--riesgo-estable-bg)", borde: "var(--riesgo-estable)" },
  ALERTA_TEMPRANA: { texto: "var(--riesgo-alerta-temprana)", fondo: "var(--riesgo-alerta-temprana-bg)", borde: "var(--riesgo-alerta-temprana)" },
  SITUACION_DELICADA: { texto: "var(--riesgo-delicada)", fondo: "var(--riesgo-delicada-bg)", borde: "var(--riesgo-delicada)" },
  CRITICO: { texto: "var(--riesgo-critico)", fondo: "var(--riesgo-critico-bg)", borde: "var(--riesgo-critico)" },
};
