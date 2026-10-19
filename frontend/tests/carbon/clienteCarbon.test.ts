import { describe, expect, it } from "vitest";

import {
  ApiError,
  obtenerComparacionXm,
  obtenerInventarioCarbon,
  obtenerResumenCarbon,
  obtenerSerieCarbon,
  obtenerValidacionCarbon,
} from "@/lib/api/client";
import { simularFetch } from "../mocks/fetch";
import { crearResumenCarbon } from "./fixturesCarbon";

const R = "/api/v1/carbon";

describe("cliente del modelo de carbon", () => {
  it.each([
    ["resumen", () => obtenerResumenCarbon(6, 30), "horizonte_meses=6&dias=30"],
    ["serie", () => obtenerSerieCarbon(12, 3), "historia_meses=12&horizonte_meses=3"],
    ["inventario", () => obtenerInventarioCarbon(9, 60), "horizonte_meses=9&dias=60"],
    ["comparacion-xm", () => obtenerComparacionXm(1), "horizonte_meses=1"],
  ])("%s manda los parametros en la query", async (ruta, llamar, query) => {
    const { llamadas } = simularFetch({ [`${R}/${ruta}`]: () => ({}) });
    await llamar();
    expect(llamadas[0].search).toBe(`?${query}`);
  });

  it("la historia 0 (toda) se envia, no se descarta como vacia", async () => {
    const { llamadas } = simularFetch({ [`${R}/serie`]: () => ({}) });
    await obtenerSerieCarbon(0, 9);
    expect(llamadas[0].searchParams.get("historia_meses")).toBe("0");
  });

  it("la validacion no lleva parametros y devuelve el cuerpo", async () => {
    const { llamadas } = simularFetch({ [`${R}/validacion`]: () => ({ ok: true }) });
    await expect(obtenerValidacionCarbon()).resolves.toEqual({ ok: true });
    expect(llamadas[0].search).toBe("");
  });

  it("devuelve el JSON del resumen", async () => {
    simularFetch({ [`${R}/resumen`]: () => crearResumenCarbon() });
    expect((await obtenerResumenCarbon(9, 45)).criterios_total).toBe(38);
  });

  it("traduce el 404 de «modelo no cargado» y el 422 a ApiError con su mensaje", async () => {
    simularFetch({ [`${R}/resumen`]: () => ({ status: 404, cuerpo: { detalle: "ejecuta importar_modelo_carbon" } }) });
    await expect(obtenerResumenCarbon(9, 45)).rejects.toMatchObject({ status: 404, message: "ejecuta importar_modelo_carbon" });
    simularFetch({ [`${R}/serie`]: () => ({ status: 422, cuerpo: { detail: "El horizonte debe ser uno de: 1, 3, 6, 9" } }) });
    await expect(obtenerSerieCarbon(36, 2)).rejects.toBeInstanceOf(ApiError);
  });
});
