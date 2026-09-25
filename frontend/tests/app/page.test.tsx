import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import DashboardPage from "@/app/page";
import { fechaHaceDias, hoyISO } from "@/lib/utils/dates";
import { EMBALSES_EJEMPLO, FUENTE_REAL, crearEmbalse } from "../fixtures";
import { simularFetch } from "../mocks/fetch";
import { simularApi } from "./rutas";

vi.mock("recharts", () => import("../mocks/recharts"));

const tituloGrafico = () => screen.getByRole("heading", { name: /%V\. útil vs\. aportes y proyección ML/ });
const selectorEmbalse = () => screen.getByRole("combobox", { name: /^Embalse/ });
const selectorRegion = () => screen.getByRole("combobox", { name: /Región/ });
// Filas de la tabla de embalses (la pagina tiene otra tabla: la de validacion de la senda).
const filasTabla = () =>
  within(screen.getByRole("columnheader", { name: /Autonomía/ }).closest("table")!).getAllByRole("row");
const tarjeta = (etiqueta: string) => screen.getByText(etiqueta).closest(".rounded-2xl") as HTMLElement;

async function pagina() {
  const api = simularApi();
  render(<DashboardPage />);
  await screen.findByText("77.5%");
  await waitFor(() => expect(tituloGrafico()).toHaveTextContent("Total nacional"));
  return api;
}

afterEach(() => {
  vi.useRealTimers();
});

describe("DashboardPage indicadores", () => {
  it("muestra los KPIs nacionales", async () => {
    await pagina();
    const kpis = screen.getByText("% Volumen útil nacional").closest("section")!;
    expect(kpis).toHaveTextContent("77.5%");
    expect(kpis).toHaveTextContent("-0.34 p.p. diario");
    expect(kpis).toHaveTextContent("-1.47 p.p. semanal");
    expect(kpis).toHaveTextContent("46.3%");
    expect(kpis).toHaveTextContent("13.553 GWh");
    expect(kpis).toHaveTextContent("Estable");
    expect(kpis).toHaveTextContent("4 embalses monitoreados"); // los 4 del fixture
  });

  it("muestra la fecha de corte en el encabezado", async () => {
    await pagina();
    expect(screen.getByRole("banner")).toHaveTextContent("Corte al 22 de sept de 2026");
  });

  it("muestra una raya si no hay aportes nacionales publicados, no 0%", async () => {
    simularApi({ kpis: { aportes_pct_media_nacional: null } });
    render(<DashboardPage />);
    await screen.findByText("77.5%");
    const aportes = tarjeta("Aportes (% media histórica)");
    expect(aportes).toHaveTextContent("—");
    expect(aportes).not.toHaveTextContent("0.0%");
  });

  it("muestra esqueletos mientras carga y ningun valor inventado", () => {
    simularFetch({ "/api/v1/embalses/resumen": () => new Promise(() => {}), "/api/v1/fuente-datos": () => new Promise(() => {}) });
    const { container } = render(<DashboardPage />);
    expect(container.querySelectorAll("section")[0].querySelectorAll(".skeleton").length).toBeGreaterThanOrEqual(4);
    expect(screen.queryByText("77.5%")).not.toBeInTheDocument();
    expect(screen.getByRole("banner")).toHaveTextContent("Cargando corte de información…");
  });

  it("si la API no responde avisa con un mensaje claro", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    render(<DashboardPage />);
    expect(await screen.findByText(/No fue posible conectar con la API/)).toHaveTextContent("Failed to fetch");
    expect(screen.queryByText("77.5%")).not.toBeInTheDocument();
  });
});

describe("DashboardPage procedencia de los datos", () => {
  it("declara que los datos son reales, su fuente y la fecha de corte", async () => {
    await pagina();
    const pie = screen.getByRole("contentinfo");
    await waitFor(() => expect(pie).toHaveTextContent("Datos reales"));
    expect(pie).toHaveTextContent("SIMEM / XM");
    expect(pie).toHaveTextContent("corte 22 de sept de 2026");
  });

  it("si la fuente no es real lo dice explicitamente", async () => {
    simularApi({ fuente: { ...FUENTE_REAL, fuente: "Datos sintéticos (simulación)", es_real: false } });
    render(<DashboardPage />);
    const pie = screen.getByRole("contentinfo");
    await waitFor(() => expect(pie).toHaveTextContent("Datos no reales"));
    expect(pie).not.toHaveTextContent("Datos reales");
    expect(pie).toHaveTextContent("Datos sintéticos");
  });

  it("mientras verifica no afirma que sean reales", () => {
    simularFetch({ "/api/v1/embalses/resumen": () => new Promise(() => {}), "/api/v1/fuente-datos": () => new Promise(() => {}) });
    render(<DashboardPage />);
    expect(screen.getByRole("contentinfo")).toHaveTextContent("Verificando procedencia de los datos…");
    expect(screen.getByRole("contentinfo")).not.toHaveTextContent("Datos reales");
  });
});

describe("DashboardPage seleccion de embalse", () => {
  it("al cargar, los filtros quedan en Todas las regiones y Todos los embalses, y todo en el total nacional", async () => {
    const { llamadas } = await pagina();
    expect(selectorRegion()).toHaveValue("");
    expect(selectorEmbalse()).toHaveValue("");
    // el selector de la senda tambien abre en "Total nacional"
    const selectores = screen.getAllByRole("combobox");
    expect(selectores[selectores.length - 1]).toHaveValue("TOTAL");
    expect(llamadas.some((u) => u.pathname === "/api/v1/embalses/TOTAL")).toBe(true);
    expect(llamadas.some((u) => u.pathname === "/api/v1/embalses/TOTAL/prediccion")).toBe(true);
    expect(llamadas.some((u) => u.pathname === "/api/v1/senda-volumen" && u.searchParams.get("embalse") === "TOTAL")).toBe(true);
    // no se pidio ningun embalse individual
    expect(llamadas.some((u) => /\/api\/v1\/embalses\/[A-Z0-9_]+$/.test(u.pathname) && !u.pathname.endsWith("/TOTAL") && !u.pathname.endsWith("/resumen"))).toBe(false);
  });

  it("pide por defecto los ultimos 180 dias hasta hoy (calendario local)", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 8, 23, 21, 30)); // 21:30 hora local
    const { llamadas } = await pagina();
    const detalle = llamadas.find((u) => u.pathname === "/api/v1/embalses/TOTAL")!;
    expect(detalle.searchParams.get("fecha_fin")).toBe(hoyISO());
    expect(detalle.searchParams.get("fecha_fin")).toBe("2026-09-23");
    expect(detalle.searchParams.get("fecha_inicio")).toBe(fechaHaceDias(180));
    expect(detalle.searchParams.get("fecha_inicio")).toBe("2026-03-27");
  });

  it("un clic en una fila de la tabla cambia el embalse del grafico", async () => {
    const { llamadas } = await pagina();
    await userEvent.click(screen.getByRole("row", { name: /Muna/ }));
    await waitFor(() => expect(tituloGrafico()).toHaveTextContent("Muna"));
    expect(selectorEmbalse()).toHaveValue("MUNA");
    expect(llamadas.some((u) => u.pathname === "/api/v1/embalses/MUNA")).toBe(true);
  });

  it("elegir un embalse en el filtro cambia el grafico", async () => {
    await pagina();
    await userEvent.selectOptions(selectorEmbalse(), "Prado");
    await waitFor(() => expect(tituloGrafico()).toHaveTextContent("Prado"));
  });
});

describe("DashboardPage filtro de region", () => {
  it("vuelve a pedir el resumen filtrado y actualiza la tabla", async () => {
    const { llamadas } = await pagina();
    await userEvent.selectOptions(selectorRegion(), "Centro");

    await waitFor(() => {
      const ultimo = llamadas.filter((u) => u.pathname === "/api/v1/embalses/resumen").at(-1)!;
      expect(ultimo.searchParams.getAll("region")).toEqual(["Centro"]);
    });
    await waitFor(() => expect(filasTabla()).toHaveLength(1 + 3));
    expect(screen.queryByRole("row", { name: /Guavio/ })).not.toBeInTheDocument();
  });

  it("no deja seleccionado un embalse de otra region: pasa al primero de la region", async () => {
    await pagina();
    await userEvent.selectOptions(selectorEmbalse(), "GUAVIO");
    await waitFor(() => expect(tituloGrafico()).toHaveTextContent("Guavio"));

    await userEvent.selectOptions(selectorRegion(), "Centro");

    await waitFor(() => expect(selectorEmbalse()).toHaveValue("PRADO"));
    await waitFor(() => expect(tituloGrafico()).toHaveTextContent("Prado"));
    const opciones = within(selectorEmbalse()).getAllByRole("option").map((o) => o.textContent);
    expect(opciones).not.toContain("Guavio");
  });

  it("'Todas las regiones' + 'Todos los embalses' dibuja el grafico del total nacional", async () => {
    const { llamadas } = await pagina();
    await userEvent.selectOptions(selectorEmbalse(), "Todos los embalses");
    expect(selectorEmbalse()).toHaveValue("");
    await waitFor(() => expect(tituloGrafico()).toHaveTextContent("Total nacional"));
    expect(screen.queryByText(/Selecciona un embalse en los filtros/)).not.toBeInTheDocument();
    await waitFor(() => expect(llamadas.some((u) => u.pathname === "/api/v1/embalses/TOTAL")).toBe(true));
    expect(llamadas.some((u) => u.pathname === "/api/v1/embalses/TOTAL/prediccion")).toBe(true);
    expect(screen.getAllByTestId("composed-chart")).toHaveLength(2); // el principal y la senda
  });

  it("con una region elegida, 'Todos los embalses' dibuja el agregado de esa region", async () => {
    const { llamadas } = await pagina();
    await userEvent.selectOptions(selectorRegion(), "Centro");
    await waitFor(() => expect(selectorEmbalse()).toHaveValue("PRADO"));
    await userEvent.selectOptions(selectorEmbalse(), "Todos los embalses");
    await waitFor(() => expect(tituloGrafico()).toHaveTextContent("Región Centro"));
    await waitFor(() =>
      expect(llamadas.some((u) => u.pathname === "/api/v1/embalses/REGION%3ACentro")).toBe(true),
    );
  });

  it("al elegir una region el grafico pasa al primer embalse de la region, sin pedir el agregado regional", async () => {
    const { llamadas } = await pagina();
    await userEvent.selectOptions(selectorRegion(), "Centro");
    await waitFor(() => expect(selectorEmbalse()).toHaveValue("PRADO"));
    expect(llamadas.some((u) => u.pathname === "/api/v1/embalses/REGION%3ACentro")).toBe(false);
  });

  it("'Restablecer filtros' devuelve region, embalse y fechas a Todos / valores por defecto", async () => {
    await pagina();
    await userEvent.selectOptions(selectorRegion(), "Centro");
    await waitFor(() => expect(selectorEmbalse()).toHaveValue("PRADO"));
    const desde = screen.getByLabelText(/Desde/) as HTMLInputElement;
    const porDefecto = desde.value;
    fireEvent.change(desde, { target: { value: "2026-05-01" } });
    expect(desde.value).toBe("2026-05-01");

    await userEvent.click(screen.getByRole("button", { name: "Restablecer filtros" }));

    expect(selectorRegion()).toHaveValue("");
    expect(selectorEmbalse()).toHaveValue("");
    expect(desde.value).toBe(porDefecto);
    await waitFor(() => expect(filasTabla()).toHaveLength(1 + EMBALSES_EJEMPLO.length));
  });

  it("tras restablecer, cambiar de region vuelve a elegir automaticamente el primer embalse", async () => {
    await pagina();
    await userEvent.click(screen.getByRole("button", { name: "Restablecer filtros" }));
    expect(selectorEmbalse()).toHaveValue("");
    await userEvent.selectOptions(selectorRegion(), "Centro");
    await waitFor(() => expect(selectorEmbalse()).toHaveValue("PRADO"));
  });

  it("volver a todas las regiones restablece la lista completa", async () => {
    await pagina();
    await userEvent.selectOptions(selectorRegion(), "Centro");
    await waitFor(() => expect(filasTabla()).toHaveLength(4));
    await userEvent.selectOptions(selectorRegion(), "Todas las regiones");
    await waitFor(() => expect(filasTabla()).toHaveLength(1 + EMBALSES_EJEMPLO.length));
  });

  it("una region sin embalses no rompe la pagina", async () => {
    simularApi({ embalses: [crearEmbalse()] });
    render(<DashboardPage />);
    await screen.findByText("77.5%");
    await userEvent.selectOptions(selectorRegion(), "Caldas");
    expect(await screen.findByText(/No hay embalses que coincidan/)).toBeInTheDocument();
  });
});

describe("DashboardPage senda de largo plazo", () => {
  it("sus opciones de embalse siguen el filtro de region", async () => {
    await pagina();
    await userEvent.selectOptions(selectorRegion(), "Centro");
    await waitFor(() => expect(filasTabla()).toHaveLength(4));
    const selectorSenda = screen.getAllByRole("combobox").find((c) => within(c).queryByText("Total nacional"))!;
    const opciones = within(selectorSenda).getAllByRole("option").map((o) => o.textContent);
    expect(opciones).toEqual(["Total nacional", "Prado", "Muna", "Agregado Bogotá"]);
  });
});
