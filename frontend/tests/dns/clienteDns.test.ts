import { describe, expect, it } from "vitest";

import {
  ApiError, obtenerCambiosReporteDns, obtenerCatalogoDns, obtenerCausasDns, obtenerModeloDns, obtenerPatronesDns,
  obtenerResumenDns, obtenerSerieDns, obtenerZonasDns,
} from "@/lib/api/client";
import { simularFetch } from "../mocks/fetch";

const D = "/api/v1/dns";
const F = { periodoMeses: 12, region: "Norte", subarea: "Are0001", origen: "programada" };

describe("cliente del modelo DNS", () => {
  it.each([
    ["resumen", () => obtenerResumenDns(F), "?periodo_meses=12&origen=programada&region=Norte&subarea=Are0001"],
    ["serie", () => obtenerSerieDns(F), "?periodo_meses=12&origen=programada&region=Norte&subarea=Are0001"],
    ["patrones", () => obtenerPatronesDns(F), "?periodo_meses=12&origen=programada&region=Norte&subarea=Are0001"],
    ["causas", () => obtenerCausasDns(F), "?periodo_meses=12&origen=programada&region=Norte&subarea=Are0001"],
  ])("%s manda periodo, origen, region y subarea", async (ruta, llamar, query) => {
    const { llamadas } = simularFetch({ [`${D}/${ruta}`]: () => ({}) });
    await llamar();
    expect(llamadas[0].search).toBe(query);
  });

  it.each([
    ["zonas", () => obtenerZonasDns(F)],
    ["cambios-reporte", () => obtenerCambiosReporteDns(F)],
    ["modelo", () => obtenerModeloDns(F)],
  ])("%s (resultado del modelo) solo manda region y subarea, no periodo ni origen", async (ruta, llamar) => {
    const { llamadas } = simularFetch({ [`${D}/${ruta}`]: () => ({}) });
    await llamar();
    expect(llamadas[0].search).toBe("?region=Norte&subarea=Are0001");
  });

  it("sin region, subarea ni origen no los envia", async () => {
    const { llamadas } = simularFetch({ [`${D}/resumen`]: () => ({}) });
    await obtenerResumenDns({ periodoMeses: 0, region: null, subarea: null, origen: null });
    expect(llamadas[0].search).toBe("?periodo_meses=0");  // el periodo 0 (todo) se envia
  });

  it("el catalogo no lleva parametros", async () => {
    const { llamadas } = simularFetch({ [`${D}/catalogo`]: () => ({ ok: 1 }) });
    await expect(obtenerCatalogoDns()).resolves.toEqual({ ok: 1 });
    expect(llamadas[0].search).toBe("");
  });

  it("traduce el 404 de «modelo no cargado» y el 422 a ApiError con su mensaje", async () => {
    simularFetch({ [`${D}/resumen`]: () => ({ status: 404, cuerpo: { detalle: "ejecuta importar_modelo_dns" } }) });
    await expect(obtenerResumenDns(F)).rejects.toMatchObject({ status: 404, message: "ejecuta importar_modelo_dns" });
    simularFetch({ [`${D}/serie`]: () => ({ status: 422, cuerpo: { detalle: "La region 'Marte' no existe" } }) });
    await expect(obtenerSerieDns(F)).rejects.toBeInstanceOf(ApiError);
  });
});
