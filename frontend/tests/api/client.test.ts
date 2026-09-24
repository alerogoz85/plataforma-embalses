import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  obtenerDetalleEmbalse,
  obtenerFuenteDatos,
  obtenerPrediccion,
  obtenerRegiones,
  obtenerResumenNacional,
  obtenerSendaVolumen,
  urlReporte,
} from "@/lib/api/client";
import { FUENTE_REAL, crearDetalle, crearPrediccion, crearResumen, crearSenda } from "../fixtures";
import { simularFetch } from "../mocks/fetch";

const BASE = "http://localhost:8000";

describe("construccion de URLs", () => {
  it("resumen sin filtros no agrega query string", async () => {
    const { llamadas } = simularFetch({ "/api/v1/embalses/resumen": () => crearResumen() });
    await obtenerResumenNacional();
    expect(llamadas[0].href).toBe(`${BASE}/api/v1/embalses/resumen`);
  });

  it("repite los parametros de region y embalse", async () => {
    const { llamadas } = simularFetch({ "/api/v1/embalses/resumen": () => crearResumen() });
    await obtenerResumenNacional({ regiones: ["Caribe", "Centro"], embalses: ["GUAVIO"], fecha: "2026-09-01" });
    const q = llamadas[0].searchParams;
    expect(q.getAll("region")).toEqual(["Caribe", "Centro"]);
    expect(q.getAll("embalse")).toEqual(["GUAVIO"]);
    expect(q.get("fecha")).toBe("2026-09-01");
  });

  it("omite parametros indefinidos o vacios", async () => {
    const { llamadas } = simularFetch({ "/api/v1/embalses/GUAVIO": () => crearDetalle() });
    await obtenerDetalleEmbalse("GUAVIO", { fechaInicio: "2026-03-27", fechaFin: "" });
    expect(llamadas[0].search).toBe("?fecha_inicio=2026-03-27");
  });

  it("el detalle pasa el rango con los nombres que espera la API", async () => {
    const { llamadas } = simularFetch({ "/api/v1/embalses/PRADO": () => crearDetalle() });
    await obtenerDetalleEmbalse("PRADO", { fechaInicio: "2026-01-01", fechaFin: "2026-02-01" });
    expect(llamadas[0].searchParams.get("fecha_inicio")).toBe("2026-01-01");
    expect(llamadas[0].searchParams.get("fecha_fin")).toBe("2026-02-01");
  });

  it("codifica el id de un agregado regional (REGION:Centro) en la ruta", async () => {
    const { llamadas } = simularFetch({
      "/api/v1/embalses/REGION%3ACentro": () => crearDetalle(2),
      "/api/v1/embalses/REGION%3ACentro/prediccion": () => crearPrediccion(2),
    });
    await obtenerDetalleEmbalse("REGION:Centro");
    await obtenerPrediccion("REGION:Centro", 30);
    expect(llamadas.map((u) => u.pathname)).toEqual([
      "/api/v1/embalses/REGION%3ACentro",
      "/api/v1/embalses/REGION%3ACentro/prediccion",
    ]);
  });

  it("la prediccion lleva el horizonte", async () => {
    const { llamadas } = simularFetch({ "/api/v1/embalses/GUAVIO/prediccion": () => crearPrediccion() });
    await obtenerPrediccion("GUAVIO", 180);
    expect(llamadas[0].searchParams.get("horizonte")).toBe("180");
  });

  it("la senda lleva embalse y horizonte en meses", async () => {
    const { llamadas } = simularFetch({ "/api/v1/senda-volumen": () => crearSenda() });
    await obtenerSendaVolumen("TOTAL", 3);
    expect(llamadas[0].searchParams.get("embalse")).toBe("TOTAL");
    expect(llamadas[0].searchParams.get("horizonte_meses")).toBe("3");
  });

  it("consulta regiones y la procedencia de los datos", async () => {
    const { llamadas } = simularFetch({
      "/api/v1/regiones": () => [],
      "/api/v1/fuente-datos": () => FUENTE_REAL,
    });
    expect(await obtenerRegiones()).toEqual([]);
    expect(await obtenerFuenteDatos()).toEqual(FUENTE_REAL);
    expect(llamadas.map((u) => u.pathname)).toEqual(["/api/v1/regiones", "/api/v1/fuente-datos"]);
  });

  it("devuelve el JSON tal cual", async () => {
    const resumen = crearResumen();
    simularFetch({ "/api/v1/embalses/resumen": () => resumen });
    expect(await obtenerResumenNacional()).toEqual(resumen);
  });

  it("propaga la senal de cancelacion a fetch", async () => {
    const { fetch } = simularFetch({ "/api/v1/regiones": () => [] });
    const controlador = new AbortController();
    await obtenerRegiones(controlador.signal);
    expect(fetch.mock.calls[0][1]).toMatchObject({ signal: controlador.signal });
  });
});

describe("urlReporte", () => {
  it("arma la URL de descarga con formato y rango", () => {
    const url = new URL(urlReporte("GUAVIO", "csv", { fechaInicio: "2026-09-01" }));
    expect(url.origin + url.pathname).toBe(`${BASE}/api/v1/embalses/GUAVIO/reporte`);
    expect(url.searchParams.get("formato")).toBe("csv");
    expect(url.searchParams.get("fecha_inicio")).toBe("2026-09-01");
    expect(url.searchParams.has("fecha_fin")).toBe(false);
  });

  it("acepta json", () => {
    expect(new URL(urlReporte("PRADO", "json")).searchParams.get("formato")).toBe("json");
  });
});

describe("errores", () => {
  it("usa el 'detalle' de los errores de dominio de la API", async () => {
    simularFetch({
      "/api/v1/embalses/NOPE": () => ({ status: 404, cuerpo: { detalle: "No existe un embalse con identificador 'NOPE'" } }),
    });
    const error = await obtenerDetalleEmbalse("NOPE").catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.name).toBe("ApiError");
    expect(error.status).toBe(404);
    expect(error.message).toBe("No existe un embalse con identificador 'NOPE'");
  });

  it("usa el 'detail' de los errores de validacion de FastAPI", async () => {
    simularFetch({
      "/api/v1/embalses/GUAVIO/prediccion": () => ({ status: 422, cuerpo: { detail: "El horizonte debe ser 30, 90, 180 o 360 dias (1, 3, 6 o 12 meses)" } }),
    });
    const error = await obtenerPrediccion("GUAVIO", 45).catch((e) => e);
    expect(error.status).toBe(422);
    expect(error.message).toBe("El horizonte debe ser 30, 90, 180 o 360 dias (1, 3, 6 o 12 meses)");
  });

  it("cae al texto de estado si la respuesta no trae un mensaje utilizable", async () => {
    const respuesta = { ok: false, status: 500, statusText: "Internal Server Error", json: async () => { throw new Error("no json"); } };
    vi.stubGlobal("fetch", vi.fn(async () => respuesta));
    const error = await obtenerRegiones().catch((e) => e);
    expect(error.status).toBe(500);
    expect(error.message).toBe("Internal Server Error");
  });

  it("no oculta los fallos de red", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    await expect(obtenerRegiones()).rejects.toThrow("Failed to fetch");
  });
});

describe("URL base segun el entorno", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  async function cargarCliente(valor?: string) {
    if (valor === undefined) vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", undefined as unknown as string);
    else vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", valor);
    vi.resetModules();
    return import("@/lib/api/client");
  }

  it("sin variable apunta al backend local", async () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    vi.resetModules();
    const { BASE_URL } = await import("@/lib/api/client");
    expect(BASE_URL).toBe("http://localhost:8000");
  });

  it("con '/' usa rutas relativas al mismo sitio (produccion en Vercel)", async () => {
    const { BASE_URL, urlReporte } = await cargarCliente("/");
    expect(BASE_URL).toBe("");
    expect(urlReporte("GUAVIO", "csv")).toMatch(/^\/api\/v1\/embalses\/GUAVIO\/reporte\?/);
  });

  it("y las peticiones salen como rutas relativas", async () => {
    const { fetch } = simularFetch({ "/api/v1/regiones": () => [] });
    const { obtenerRegiones } = await cargarCliente("/");
    await obtenerRegiones().catch(() => {});
    expect(fetch.mock.calls[0][0]).toBe("/api/v1/regiones");
  });

  it("quita las barras finales de una URL absoluta", async () => {
    const { BASE_URL } = await cargarCliente("https://api.ejemplo.com//");
    expect(BASE_URL).toBe("https://api.ejemplo.com");
  });
});
