import { describe, expect, it } from "vitest";

import {
  COLOR_VAR_RIESGO,
  SIN_DATO,
  etiquetaRiesgo,
  formatearDelta,
  formatearFecha,
  formatearFechaCorta,
  formatearMes,
  formatearNumero,
  formatearNumeroOpcional,
  formatearPorcentaje,
  formatearPorcentajeOpcional,
} from "@/lib/utils/formatters";

describe("formatearPorcentaje", () => {
  it("usa un decimal por defecto y permite cambiarlo", () => {
    expect(formatearPorcentaje(77.52)).toBe("77.5%");
    expect(formatearPorcentaje(77.52, 2)).toBe("77.52%");
    expect(formatearPorcentaje(100, 0)).toBe("100%");
  });

  it("muestra valores sobre 100% sin acotarlos", () => {
    expect(formatearPorcentaje(111.8)).toBe("111.8%");
  });
});

describe("formatearNumero (es-CO)", () => {
  it("usa punto de miles y coma decimal", () => {
    expect(formatearNumero(13553.35, 0)).toBe("13.553");
    expect(formatearNumero(0.4)).toBe("0,4");
    expect(formatearNumero(1234.5, 2)).toBe("1.234,50");
  });
});

describe("formatearDelta", () => {
  it("antepone + a las subidas y deja el - de las bajadas", () => {
    expect(formatearDelta(0.06)).toBe("+0.06 p.p.");
    expect(formatearDelta(-1.47)).toBe("-1.47 p.p.");
  });

  it("no pone signo a cero", () => {
    expect(formatearDelta(0)).toBe("0.00 p.p.");
  });
});

describe("valores opcionales", () => {
  it("muestran una raya cuando el dato no esta publicado, nunca un cero", () => {
    expect(SIN_DATO).toBe("—");
    expect(formatearNumeroOpcional(null)).toBe("—");
    expect(formatearPorcentajeOpcional(null)).toBe("—");
  });

  it("un cero real se muestra como cero, no como dato faltante", () => {
    expect(formatearNumeroOpcional(0)).toBe("0,0");
    expect(formatearPorcentajeOpcional(0)).toBe("0.0%");
  });

  it("formatean normalmente cuando hay dato", () => {
    expect(formatearNumeroOpcional(26.5)).toBe("26,5");
    expect(formatearNumeroOpcional(2400, 0)).toBe("2.400");
    expect(formatearPorcentajeOpcional(46.3)).toBe("46.3%");
  });
});

describe("fechas", () => {
  it("formatea fechas completas, cortas y meses en espanol de Colombia", () => {
    expect(formatearFecha("2026-09-22")).toBe("22 de sept de 2026");
    expect(formatearFechaCorta("2026-09-22")).toBe("22 de sept");
    expect(formatearMes("2027-04")).toBe("abr de 2027");
  });

  it("no corre el dia por zona horaria (se interpreta como fecha local)", () => {
    expect(formatearFecha("2026-01-01")).toContain("1 de ene");
    expect(formatearFecha("2026-12-31")).toContain("31 de dic");
  });
});

describe("riesgo", () => {
  it("tiene una etiqueta legible para cada nivel", () => {
    expect(etiquetaRiesgo("OPTIMO")).toBe("Óptimo");
    expect(etiquetaRiesgo("ALERTA")).toBe("Alerta de sequía");
    expect(etiquetaRiesgo("CRITICO")).toBe("Crítico");
    expect(etiquetaRiesgo("REBOCE")).toBe("Reboce");
  });

  it("tiene una paleta semantica distinta para cada nivel", () => {
    const textos = Object.values(COLOR_VAR_RIESGO).map((c) => c.texto);
    expect(new Set(textos).size).toBe(4);
    expect(COLOR_VAR_RIESGO.OPTIMO.texto).toBe("var(--color-optimo)");
    expect(COLOR_VAR_RIESGO.ALERTA.texto).toBe("var(--color-alerta)");
    expect(COLOR_VAR_RIESGO.CRITICO.texto).toBe("var(--color-critico)");
    expect(COLOR_VAR_RIESGO.REBOCE.texto).toBe("var(--color-reboce)");
  });
});
