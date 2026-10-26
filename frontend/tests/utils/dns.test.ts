import { describe, expect, it } from "vitest";

import {
  colorTendenciaZona, construirPuntosSerieDns, esMejora, etiquetaMesDns, formatearVariacionPct, nombreCausa,
} from "@/lib/utils/dns";
import { crearSerieDns } from "../dns/fixturesDns";

describe("formatearVariacionPct", () => {
  it.each([
    [17.86, "+17,9 %"],
    [-39.3, "−39,3 %"],
    [0, "0,0 %"],
    [2081.2, "+2.081,2 %"],
    [null, "—"],
  ])("%s -> %s", (v, texto) => expect(formatearVariacionPct(v)).toBe(texto));
});

describe("esMejora: en DNS subir es malo", () => {
  it("baja o igual es mejora; sube o sin base no lo es", () => {
    expect(esMejora(-1)).toBe(true);
    expect(esMejora(0)).toBe(true);
    expect(esMejora(0.1)).toBe(false);
    expect(esMejora(null)).toBe(false);
  });
});

describe("etiquetas", () => {
  it("mes corto en español sin punto ni «de»", () => {
    expect(etiquetaMesDns("2026-08")).toBe("ago 26");
    expect(etiquetaMesDns("2026-09")).toBe("sept 26");
  });

  it("causas con nombre legible y las desconocidas tal cual capitalizadas", () => {
    expect(nombreCausa("atmosferica")).toBe("Atmosférica");
    expect(nombreCausa("desconocido")).toBe("Desconocida");
    expect(nombreCausa("rara")).toBe("Rara");
  });

  it("color de tendencia: rojo si empeora, azul si no", () => {
    expect(colorTendenciaZona(0.1)).toBe("var(--color-critico)");
    expect(colorTendenciaZona(0)).toBe("var(--chart-volumen)");
    expect(colorTendenciaZona(-20)).toBe("var(--chart-volumen)");
  });
});

describe("construirPuntosSerieDns", () => {
  it("eventos: observado, no programados y el pronostico en su mes", () => {
    const pts = construirPuntosSerieDns(crearSerieDns(), "eventos");
    expect(pts.map((p) => p.mes)).toEqual(["2026-06", "2026-07", "2026-08"]);
    expect(pts[1]).toMatchObject({ valor: 120, noProgramados: 90, parcial: false });
    expect(pts[2]).toMatchObject({ valor: 40, parcial: true, pronostico: 311 });
    expect(pts[0].pronostico).toBeUndefined();
  });

  it("energia: usa GWh y no separa por origen", () => {
    const pts = construirPuntosSerieDns(crearSerieDns(), "energia");
    expect(pts[1].valor).toBe(6.0);
    expect(pts[1].noProgramados).toBeUndefined();
    expect(pts[2].pronostico).toBe(3.5);
  });

  it("si el mes pronosticado no esta en la ventana se agrega al final sin valor observado", () => {
    const serie = crearSerieDns({ pronostico: { mes: "2026-09", eventos: 50, energia_gwh: 1, subareas: 3 } });
    const pts = construirPuntosSerieDns(serie, "eventos");
    expect(pts).toHaveLength(4);
    expect(pts[3]).toMatchObject({ mes: "2026-09", pronostico: 50 });
    expect(pts[3].valor).toBeUndefined();
  });

  it("sin pronostico no hay punto de pronostico", () => {
    const pts = construirPuntosSerieDns(crearSerieDns({ pronostico: null }), "eventos");
    expect(pts.every((p) => p.pronostico === undefined)).toBe(true);
  });
});
