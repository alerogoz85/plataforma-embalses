import { describe, expect, it } from "vitest";

import {
  construirPuntosSerie,
  construirPuntosXm,
  convertirBanda,
  convertirConsumo,
  decimalesUnidad,
  etiquetaMesCarbon,
  etiquetaTrimestre,
  nivelUsoTecho,
} from "@/lib/utils/carbon";
import { PODER, crearComparacionXm, crearSerieCarbon } from "../carbon/fixturesCarbon";

describe("conversion de unidades", () => {
  it("GBTU/dia se queda igual y kt/dia divide por el poder calorifico", () => {
    expect(convertirConsumo(100, "gbtu", PODER)).toBe(100);
    expect(convertirConsumo(100, "kt", PODER)).toBe(4);
  });

  it("con el poder calorifico real, 26.27 GBTU/dia son 1 kt/dia", () => {
    expect(convertirConsumo(26.27, "kt", 26.27)).toBeCloseTo(1, 10);
  });

  it("convierte las tres posiciones de la banda y conserva el orden P10<=P50<=P90", () => {
    const b = convertirBanda({ p10: 50, p50: 100, p90: 150 }, "kt", PODER);
    expect(b).toEqual({ p10: 2, p50: 4, p90: 6 });
  });

  it("decimales: 1 para GBTU y 2 para kt", () => {
    expect(decimalesUnidad("gbtu")).toBe(1);
    expect(decimalesUnidad("kt")).toBe(2);
  });
});

describe("semaforo del uso del techo", () => {
  it.each([
    [0, "optimo"],
    [84.9, "optimo"],
    [85, "alerta"],
    [100, "alerta"],
    [100.1, "critico"],
    [130, "critico"],
  ] as const)("%s %% -> %s", (uso, nivel) => {
    expect(nivelUsoTecho(uso)).toBe(nivel);
  });
});

describe("etiquetas", () => {
  it("trimestre con y sin guion, y formato desconocido sin tocar", () => {
    expect(etiquetaTrimestre("2026Q4")).toBe("T4 2026");
    expect(etiquetaTrimestre("2027-Q1")).toBe("T1 2027");
    expect(etiquetaTrimestre("raro")).toBe("raro");
  });

  it("mes en espanol sin punto", () => {
    expect(etiquetaMesCarbon("2026-10-01")).toBe("oct de 2026");
  });
});

describe("construirPuntosSerie", () => {
  it("omite el mes en curso del historico y une con un punto puente", () => {
    const pts = construirPuntosSerie(crearSerieCarbon(), "gbtu");
    // 2 historicos completos (el 3.o esta en curso) -> el ultimo se convierte en puente + 2 proyectados
    expect(pts.map((p) => p.fecha)).toEqual(["2026-08-01", "2026-09-01", "2026-10-01", "2026-11-01"]);
    expect(pts[1]).toMatchObject({ observado: 250, p50: 250, bandaBase: 250, bandaRango: 0 });
    expect(pts[2]).toMatchObject({ p50: 300, bandaBase: 250, bandaRango: 100 });
    expect(pts[2].observado).toBeUndefined();
  });

  it("convierte todo a la unidad elegida", () => {
    const pts = construirPuntosSerie(crearSerieCarbon(), "kt");
    expect(pts[0].observado).toBe(8);
    expect(pts[3]).toMatchObject({ p50: 12.4, bandaBase: 10.4 });
    expect(pts[3].bandaRango).toBeCloseTo(4.4, 10);
  });

  it("sin proyeccion devuelve solo el historico; sin historico, solo la proyeccion", () => {
    expect(construirPuntosSerie(crearSerieCarbon({ proyeccion: [] }), "gbtu")).toHaveLength(2);
    const solo = construirPuntosSerie(crearSerieCarbon({ historico: [] }), "gbtu");
    expect(solo).toHaveLength(2);
    expect(solo.every((p) => p.observado === undefined)).toBe(true);
  });
});

describe("construirPuntosXm", () => {
  it("convierte modelo y XM; un XM ausente deja hueco", () => {
    const pts = construirPuntosXm(crearComparacionXm(null), "kt", PODER);
    expect(pts[0]).toMatchObject({ p50: 12, bandaBase: 10 });
    expect(pts[0].xm).toBeUndefined();
    expect(pts[1].xm).toBeCloseTo(15.2, 10);
  });
});
