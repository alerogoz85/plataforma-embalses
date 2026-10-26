import { describe, expect, it } from "vitest";

import type { SerieModelo } from "@/lib/api/types";
import { construirPuntosModelo, etiquetaX, filtrarSeries, opcionesPeriodo, tieneBanda } from "@/lib/utils/modelos";
import { crearResultadoModelo } from "../modelos/fixturesModelos";

const series = crearResultadoModelo().series;

describe("etiquetaX", () => {
  it.each([
    ["2026-10", "oct 26"],
    ["2026-09", "sept 26"],
    ["2026-10-05", "5 de oct"],
    ["Pico de la noche", "Pico de la noche"],
  ])("%s -> %s", (x, texto) => expect(etiquetaX(x)).toBe(texto));
});

describe("opcionesPeriodo", () => {
  it("une los meses de todas las series, sin repetir y ordenados", () => {
    const extra: SerieModelo = { id: "x", titulo: "x", unidad: "u", tipo: "linea", puntos: [{ x: "2026-09", y: 1, p10: null, p90: null }, { x: "2026-11", y: 1, p10: null, p90: null }] };
    expect(opcionesPeriodo([...series, extra])).toEqual(["2026-09", "2026-10", "2026-11", "2026-12"]);
  });

  it("ignora etiquetas que no son meses", () => {
    const franja: SerieModelo = { id: "f", titulo: "f", unidad: "u", tipo: "barras", puntos: [{ x: "Madrugada", y: 1, p10: null, p90: null }] };
    expect(opcionesPeriodo([franja])).toEqual([]);
  });
});

describe("filtrarSeries", () => {
  it("recorta todas las series al rango, extremos incluidos", () => {
    const f = filtrarSeries(series, "2026-11", "2026-12");
    expect(f.map((s) => s.puntos.map((p) => p.x))).toEqual([["2026-11", "2026-12"], ["2026-11", "2026-12"], ["2026-11", "2026-12"]]);
  });

  it("un extremo vacío deja ese lado abierto", () => {
    expect(filtrarSeries(series, "2026-12", "")[0].puntos).toHaveLength(1);
    expect(filtrarSeries(series, "", "2026-10")[0].puntos).toHaveLength(1);
    expect(filtrarSeries(series, "", "")[0].puntos).toHaveLength(3);
  });

  it("un rango sin datos deja series vacías pero no las quita ni cambia la entrada", () => {
    const f = filtrarSeries(series, "2030-01", "");
    expect(f).toHaveLength(3);
    expect(f.every((s) => s.puntos.length === 0)).toBe(true);
    expect(series[0].puntos).toHaveLength(3);
  });
});

describe("construirPuntosModelo", () => {
  it("la banda se apila como base + rango y solo existe si hay p10 y p90", () => {
    const [con] = construirPuntosModelo(series[1].puntos);
    expect(con).toMatchObject({ x: "2026-10", etiqueta: "oct 26", valor: 55, bandaBase: 40, bandaRango: 30 });
    const [sin] = construirPuntosModelo(series[0].puntos);
    expect(sin.bandaBase).toBeUndefined();
  });

  it("tieneBanda", () => {
    expect(tieneBanda(series[1].puntos)).toBe(true);
    expect(tieneBanda(series[0].puntos)).toBe(false);
  });
});
