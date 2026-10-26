import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ApagonPage from "@/app/apagon/page";
import CarbonPage from "@/app/carbon/page";
import DnsPage from "@/app/dns/page";
import EmbalsesPage from "@/app/embalses/page";
import { simularFetch } from "../mocks/fetch";
import { fijarUrl, parametrosActuales, urlActual } from "../mocks/navigation";
import { simularApi as simularApiEmbalses } from "../app/rutas";
import { crearCambiosDns, crearCatalogoDns, crearCausasDns, crearModeloDns, crearPatronesDns, crearResumenDns, crearSerieDns, crearZonasDns } from "../dns/fixturesDns";
import { crearComparacionXm, crearInventario, crearResumenCarbon, crearSerieCarbon, crearValidacionCarbon } from "../carbon/fixturesCarbon";
import { conResultados, crearFichaModelo, crearResultadoModelo } from "../modelos/fixturesModelos";

vi.mock("recharts", () => import("../mocks/recharts"));

const hoy = () => new Date().toISOString().slice(0, 10);

// ---------------------------------------------------------------------------------------------- DNS
function apiDns() {
  const D = "/api/v1/dns";
  return simularFetch({
    [`${D}/catalogo`]: () => crearCatalogoDns(), [`${D}/resumen`]: () => crearResumenDns(), [`${D}/serie`]: () => crearSerieDns(),
    [`${D}/zonas`]: () => crearZonasDns(), [`${D}/patrones`]: () => crearPatronesDns(), [`${D}/causas`]: () => crearCausasDns(),
    [`${D}/cambios-reporte`]: () => crearCambiosDns(), [`${D}/modelo`]: () => crearModeloDns(),
  });
}
const ultima = (llamadas: URL[], ruta: string) => llamadas.filter((u) => u.pathname.endsWith(`/${ruta}`)).at(-1)!;

describe("DNS: los filtros viven en la URL", () => {
  it("una direccion con filtros abre el tablero ya filtrado y consulta la API con ellos", async () => {
    fijarUrl("/dns?periodo=12&region=Norte&origen=programada");
    const { llamadas } = apiDns();
    render(<DnsPage />);
    await screen.findByText(/Variables que más pesan/);
    expect(screen.getByRole("combobox", { name: "Período" })).toHaveValue("12");
    expect(screen.getByRole("combobox", { name: "Región" })).toHaveValue("Norte");
    expect(screen.getByRole("combobox", { name: "Origen" })).toHaveValue("programada");
    expect(ultima(llamadas, "resumen").search).toBe("?periodo_meses=12&origen=programada&region=Norte");
  });

  it("cambiar un filtro actualiza la URL (solo lo que no es el defecto)", async () => {
    fijarUrl("/dns");
    apiDns();
    render(<DnsPage />);
    await screen.findByText(/Variables que más pesan/);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Período" }), "12");
    expect(urlActual()).toBe("/dns?periodo=12");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Región" }), "Norte");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Origen" }), "no_programada");
    expect(parametrosActuales().toString()).toBe("periodo=12&region=Norte&origen=no_programada");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Período" }), "36");
    expect(parametrosActuales().has("periodo")).toBe(false);
  });

  it("cambiar de region limpia la subarea en la URL en un solo paso", async () => {
    fijarUrl("/dns?region=Sur&subarea=Are0003");
    apiDns();
    render(<DnsPage />);
    await screen.findByText(/Variables que más pesan/);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Región" }), "Norte");
    expect(parametrosActuales().get("region")).toBe("Norte");
    expect(parametrosActuales().has("subarea")).toBe(false);
  });

  it("un clic en una zona del ranking pone region y subarea en la URL", async () => {
    apiDns();
    render(<DnsPage />);
    await userEvent.click(await screen.findByRole("button", { name: "SubArea Tres" }));
    expect(parametrosActuales().get("subarea")).toBe("Are0003");
    expect(parametrosActuales().get("region")).toBe("Sur");
  });

  it("«Restablecer filtros» deja la URL limpia", async () => {
    fijarUrl("/dns?periodo=60&region=Norte&origen=programada");
    apiDns();
    render(<DnsPage />);
    await screen.findByText(/Variables que más pesan/);
    await userEvent.click(screen.getByRole("button", { name: /Restablecer filtros/ }));
    expect(urlActual()).toBe("/dns");
  });

  it("valores invalidos en la URL se ignoran: no llegan a la API ni rompen la pagina", async () => {
    fijarUrl("/dns?periodo=7&origen=otro&region=<b>&subarea=Are0003;--");
    const { llamadas } = apiDns();
    render(<DnsPage />);
    await screen.findByText(/Variables que más pesan/);
    expect(ultima(llamadas, "resumen").search).toBe("?periodo_meses=36");
    expect(screen.getByRole("combobox", { name: "Período" })).toHaveValue("36");
  });

  it("una region que no existe en el catalogo se descarta una vez cargado el catalogo", async () => {
    fijarUrl("/dns?region=Marte&subarea=Are9999");
    const { llamadas } = apiDns();
    render(<DnsPage />);
    await screen.findByText(/Variables que más pesan/);
    expect(screen.getByRole("combobox", { name: "Región" })).toHaveValue("");
    expect(ultima(llamadas, "resumen").search).toBe("?periodo_meses=36");
  });

  it("una subarea de otra region que la elegida se descarta", async () => {
    fijarUrl("/dns?region=Norte&subarea=Are0003");
    apiDns();
    render(<DnsPage />);
    await screen.findByText(/Variables que más pesan/);
    expect(screen.getByRole("combobox", { name: "Subárea" })).toHaveValue("");
  });

  it("la medida de la serie (Eventos / Energia) tambien tiene su parametro", async () => {
    fijarUrl("/dns?medida=energia");
    apiDns();
    render(<DnsPage />);
    expect(await screen.findByText("Energía no atendida (GWh) por mes")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Eventos" }));
    expect(parametrosActuales().has("medida")).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: "Energía" }));
    expect(parametrosActuales().get("medida")).toBe("energia");
  });
});

// ---------------------------------------------------------------------------------------------- Carbon
function apiCarbon() {
  const R = "/api/v1/carbon";
  return simularFetch({
    [`${R}/resumen`]: () => crearResumenCarbon(), [`${R}/serie`]: () => crearSerieCarbon(), [`${R}/inventario`]: () => crearInventario(),
    [`${R}/comparacion-xm`]: () => crearComparacionXm(), [`${R}/validacion`]: () => crearValidacionCarbon(),
  });
}

describe("Carbon: los filtros viven en la URL", () => {
  it("abre con los filtros de la direccion y los envia a la API", async () => {
    fijarUrl("/carbon?horizonte=3&unidad=kt&dias=60&historia=0");
    const { llamadas } = apiCarbon();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    expect(screen.getByRole("combobox", { name: "Horizonte" })).toHaveValue("3");
    expect(screen.getByRole("combobox", { name: "Unidad" })).toHaveValue("kt");
    expect(ultima(llamadas, "resumen").search).toBe("?horizonte_meses=3&dias=60");
    expect(ultima(llamadas, "serie").search).toBe("?historia_meses=0&horizonte_meses=3");
  });

  it("cambiar filtros escribe la URL y restablecer la limpia", async () => {
    fijarUrl("/carbon");
    apiCarbon();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Horizonte" }), "6");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Unidad" }), "kt");
    expect(parametrosActuales().toString()).toBe("horizonte=6&unidad=kt");
    await userEvent.click(screen.getByRole("button", { name: /Restablecer filtros/ }));
    expect(urlActual()).toBe("/carbon");
  });

  it("valores fuera de las listas cerradas de la API se ignoran (nunca provocan un 422)", async () => {
    fijarUrl("/carbon?horizonte=2&historia=5&dias=99&unidad=lb");
    const { llamadas } = apiCarbon();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    expect(ultima(llamadas, "resumen").search).toBe("?horizonte_meses=9&dias=45");
    expect(ultima(llamadas, "serie").search).toBe("?historia_meses=36&horizonte_meses=9");
  });
});

// ---------------------------------------------------------------------------------------------- Modelos
function apiModelo(resultados: unknown) {
  return simularFetch({
    "/api/v1/modelos/apagon/ficha": () => crearFichaModelo({ estado: "con_resultados" }),
    "/api/v1/modelos/apagon/resultados": () => resultados,
  });
}

describe("Modelos: el periodo de las series vive en la URL", () => {
  it("abre con el rango de la direccion y recorta todas las series", async () => {
    fijarUrl("/apagon?desde=2026-11&hasta=2026-12");
    apiModelo(conResultados());
    render(<ApagonPage />);
    await screen.findByText("Meses en rojo");
    expect(screen.getByRole("combobox", { name: "Desde" })).toHaveValue("2026-11");
    expect(JSON.parse(screen.getAllByTestId("composed-chart")[0].dataset.points!).map((p: { x: string }) => p.x)).toEqual(["2026-11", "2026-12"]);
  });

  it("elegir un mes escribe la URL; restablecer la limpia", async () => {
    fijarUrl("/apagon");
    apiModelo(conResultados());
    render(<ApagonPage />);
    await screen.findByText("Meses en rojo");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Desde" }), "2026-12");
    expect(urlActual()).toBe("/apagon?desde=2026-12");
    await userEvent.click(screen.getByRole("button", { name: /Restablecer filtros/ }));
    expect(urlActual()).toBe("/apagon");
  });

  it("un mes que no esta en las series se ignora en lugar de dejar los graficos vacios", async () => {
    fijarUrl("/apagon?desde=2030-01&hasta=2031-01");
    apiModelo(conResultados(crearResultadoModelo()));
    render(<ApagonPage />);
    await screen.findByText("Meses en rojo");
    expect(screen.getByRole("combobox", { name: "Desde" })).toHaveValue("");
    expect(JSON.parse(screen.getAllByTestId("composed-chart")[0].dataset.points!)).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------------------------- Embalses
describe("Embalses: filtros, horizontes y tabla viven en la URL", () => {
  it("abre con region, embalse y horizontes de la direccion", async () => {
    fijarUrl("/embalses?region=Centro&embalse=EMBALSE_B&h=90&hs=6");
    const { llamadas } = simularApiEmbalses();
    render(<EmbalsesPage />);
    await screen.findByText("Embalses");
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Región" })).toHaveValue("Centro"));
    await waitFor(() => expect(llamadas.some((u) => u.pathname.endsWith("/prediccion") && u.searchParams.get("horizonte") === "90")).toBe(true));
    expect(llamadas.some((u) => u.pathname.endsWith("/senda-volumen") && u.searchParams.get("horizonte_meses") === "6")).toBe(true);
  });

  it("cambiar de region limpia el embalse en la URL; los horizontes escriben h y hs", async () => {
    fijarUrl("/embalses?region=Antioquia&embalse=EMBALSE_A");
    simularApiEmbalses();
    render(<EmbalsesPage />);
    await screen.findByText("Embalses");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Región" }), "Centro");
    expect(parametrosActuales().get("region")).toBe("Centro");
    expect(parametrosActuales().has("embalse")).toBe(false);
    await userEvent.click(screen.getAllByRole("button", { name: "3m" })[0]);
    expect(parametrosActuales().get("h")).toBe("90");
    await userEvent.click(screen.getAllByRole("button", { name: "6m" }).at(-1)!);
    expect(parametrosActuales().get("hs")).toBe("6");
  });

  it("la busqueda y el orden de la tabla se guardan en la URL", async () => {
    fijarUrl("/embalses");
    simularApiEmbalses();
    render(<EmbalsesPage />);
    await screen.findByText("Embalses");
    await userEvent.type(screen.getByPlaceholderText("Buscar embalse o región…"), "guav");
    expect(parametrosActuales().get("q")).toBe("guav");
    await userEvent.click(screen.getByRole("columnheader", { name: /^Embalse/ }));
    expect(parametrosActuales().get("orden")).toBe("nombre");
    await userEvent.click(screen.getByRole("columnheader", { name: /^Embalse/ }));
    expect(parametrosActuales().get("dir")).toBe("desc");
  });

  it("fechas al reves o invalidas no rompen: se ordenan o se ignoran", async () => {
    fijarUrl(`/embalses?desde=${hoy()}&hasta=2020-01-01`);
    const { llamadas } = simularApiEmbalses();
    render(<EmbalsesPage />);
    await screen.findByText("Embalses");
    const detalle = llamadas.find((u) => /\/embalses\/[^/]+$/.test(u.pathname) && u.searchParams.has("fecha_inicio"));
    expect(detalle!.searchParams.get("fecha_inicio")! <= detalle!.searchParams.get("fecha_fin")!).toBe(true);
  });

  it("una region inexistente y una fecha invalida en la URL se ignoran", async () => {
    fijarUrl("/embalses?desde=ayer&region=Marte");
    simularApiEmbalses();
    render(<EmbalsesPage />);
    await screen.findByText("Embalses");
    const region = screen.getAllByRole("combobox", { name: "Región" })[0];
    expect(region).toHaveValue("");
    expect(within(region).getAllByRole("option").length).toBeGreaterThan(1);
  });
});
