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
  OPTIMO: "Óptimo",
  ALERTA: "Alerta de sequía",
  CRITICO: "Crítico",
  REBOCE: "Reboce",
};

export function etiquetaRiesgo(nivel: NivelRiesgo): string {
  return ETIQUETAS_RIESGO[nivel];
}

export const COLOR_VAR_RIESGO: Record<NivelRiesgo, { texto: string; fondo: string; borde: string }> = {
  OPTIMO: { texto: "var(--color-optimo)", fondo: "var(--color-optimo-bg)", borde: "var(--color-optimo)" },
  ALERTA: { texto: "var(--color-alerta)", fondo: "var(--color-alerta-bg)", borde: "var(--color-alerta)" },
  CRITICO: { texto: "var(--color-critico)", fondo: "var(--color-critico-bg)", borde: "var(--color-critico)" },
  REBOCE: { texto: "var(--color-reboce)", fondo: "var(--color-reboce-bg)", borde: "var(--color-reboce)" },
};
