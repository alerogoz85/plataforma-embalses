import { describe, expect, it } from "vitest";

import { colorCalor, faseEnso, formatearMillones, formatearOni, kpisEscenario, rotuloFranja, semaforoPorUmbral, UMBRALES_DEFICIT, UMBRALES_SEVERO } from "@/lib/utils/gemelo";
import { crearMes } from "../apagon/fixturesEscenario";

describe("gemelo digital: utilidades", () => {
  it.each([[2.5, "El Niño muy fuerte"], [1.5, "El Niño fuerte"], [1.0, "El Niño moderado"], [0.5, "El Niño débil"], [0, "Neutral"], [-0.5, "Neutral"], [-0.6, "La Niña débil"], [-1.2, "La Niña moderada"], [-1.9, "La Niña fuerte"], [-2.5, "La Niña muy fuerte"]])(
    "la fase de ONI %s es %s", (oni, fase) => expect(faseEnso(oni)).toBe(fase),
  );

  it("formatea el ONI con signo", () => {
    expect([formatearOni(1), formatearOni(-0.5), formatearOni(0)]).toEqual(["ONI +1.0", "ONI -0.5", "ONI 0.0"]);
  });

  it("el semáforo por umbral usa los límites de la leyenda (el límite ya pasa al siguiente nivel)", () => {
    expect([0.09, 0.1, 0.249, 0.25].map((p) => semaforoPorUmbral(p, UMBRALES_DEFICIT))).toEqual(["VERDE", "AMARILLO", "AMARILLO", "ROJO"]);
    expect([0.029, 0.03, 0.099, 0.1].map((p) => semaforoPorUmbral(p, UMBRALES_SEVERO))).toEqual(["VERDE", "AMARILLO", "AMARILLO", "ROJO"]);
  });

  it("los indicadores salen del peor mes", () => {
    const k = kpisEscenario([crearMes(0), crearMes(5), crearMes(2, { indice_riesgo: 30 })]);
    expect([k.peorIndice, k.mesesRojo]).toEqual([30, 2]);
    expect(k.maxProbDeficit).toBeCloseTo(0.3);
    expect(k.maxProbSevero).toBeCloseTo(0.12);
  });

  it("el mapa de calor va de claro (0) a oscuro (máximo) y sin máximo no falla", () => {
    expect(colorCalor(0, 100)).toBe("rgb(255, 245, 240)");
    expect(colorCalor(100, 100)).toBe("rgb(103, 0, 13)");
    expect(colorCalor(500, 100)).toBe(colorCalor(100, 100));
    expect(colorCalor(5, 0)).toBe("rgb(255, 245, 240)");
  });

  it("rotula franjas y millones", () => {
    expect(rotuloFranja("pico_noche_18_21")).toBe("Pico noche 18–21");
    expect(rotuloFranja("otra")).toBe("otra");
    expect(formatearMillones(7_000_000)).toBe("7M");
    expect(formatearMillones(6_500_000)).toBe("6.5M");
  });
});
