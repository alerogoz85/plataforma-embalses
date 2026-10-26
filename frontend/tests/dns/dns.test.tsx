import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import DnsPage from "@/app/dns/page";
import { simularFetch } from "../mocks/fetch";
import {
  crearCambiosDns, crearCatalogoDns, crearCausasDns, crearModeloDns, crearPatronesDns, crearResumenDns, crearSerieDns,
  crearZonasDns,
} from "./fixturesDns";

vi.mock("recharts", () => import("../mocks/recharts"));

const D = "/api/v1/dns";
const RUTAS = ["catalogo", "resumen", "serie", "zonas", "patrones", "causas", "cambios-reporte", "modelo"];

function api(sobre: Record<string, (u: URL) => unknown> = {}) {
  return simularFetch({
    [`${D}/catalogo`]: () => crearCatalogoDns(),
    [`${D}/resumen`]: () => crearResumenDns(),
    [`${D}/serie`]: () => crearSerieDns(),
    [`${D}/zonas`]: () => crearZonasDns(),
    [`${D}/patrones`]: () => crearPatronesDns(),
    [`${D}/causas`]: () => crearCausasDns(),
    [`${D}/cambios-reporte`]: () => crearCambiosDns(),
    [`${D}/modelo`]: () => crearModeloDns(),
    ...sobre,
  });
}

const kpi = (etiqueta: RegExp) => screen.getByText(etiqueta).closest("div")!.parentElement!;
const esperarCarga = () => screen.findByText(/Variables que más pesan/);
const ultima = (llamadas: URL[], ruta: string) => llamadas.filter((u) => u.pathname === `${D}/${ruta}`).at(-1)!;
const cantidad = (llamadas: URL[], ruta: string) => llamadas.filter((u) => u.pathname === `${D}/${ruta}`).length;

describe("Tablero DNS (pagina)", () => {
  it("consulta los 8 endpoints con el periodo por defecto de 36 meses y sin otros filtros", async () => {
    const { llamadas } = api();
    render(<DnsPage />);
    await esperarCarga();
    for (const ruta of RUTAS) expect(cantidad(llamadas, ruta)).toBeGreaterThan(0);
    for (const ruta of ["resumen", "serie", "patrones", "causas"]) {
      expect(ultima(llamadas, ruta).search).toBe("?periodo_meses=36");
    }
    for (const ruta of ["zonas", "cambios-reporte", "modelo"]) expect(ultima(llamadas, ruta).search).toBe("");
  });

  it("el encabezado informa el ultimo evento y que el mes esta en curso", async () => {
    api();
    render(<DnsPage />);
    expect(await screen.findByText(/Último evento: 11 de ago de 2026 \(mes en curso\) · 3 subáreas/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Demanda no atendida (DNS)");
  });

  it("muestra las 4 tarjetas con sus valores y el periodo", async () => {
    api();
    render(<DnsPage />);
    const eventos = await waitFor(() => kpi(/Eventos DNS · sept de 2023 a ago de 2026/i));
    expect(eventos).toHaveTextContent("5.963");
    expect(eventos).toHaveTextContent("Causa conocida más frecuente: mantenimiento (2.835)");
    expect(kpi(/^Energía no atendida$/i)).toHaveTextContent("214,1 GWh");
    expect(kpi(/Eventos críticos/i)).toHaveTextContent("9.3%");
    const noProg = kpi(/Eventos no programados/i);
    expect(noProg).toHaveTextContent("82.9%");
    expect(noProg).toHaveTextContent("Además, 14 eventos EDAC (no incluidos)");
  });

  it("una subida es desfavorable (rojo) y una bajada favorable (verde)", async () => {
    api();
    render(<DnsPage />);
    await esperarCarga();
    const sube = screen.getByText(/\+142,2 % frente al período anterior/);
    const baja = screen.getByText(/−39,3 % frente al período anterior/);
    expect(sube).toHaveStyle({ color: "var(--color-critico)" });
    expect(baja).toHaveStyle({ color: "var(--color-optimo)" });
  });

  it("todo el historico no se compara y lo dice", async () => {
    api({ [`${D}/resumen`]: () => crearResumenDns({ periodo_meses: 0, variacion_eventos_pct: null, variacion_energia_pct: null }) });
    render(<DnsPage />);
    await esperarCarga();
    expect(screen.queryByText(/frente al período anterior/)).not.toBeInTheDocument();
  });

  it("sin EDAC lo indica en lugar de un conteo", async () => {
    api({ [`${D}/resumen`]: () => crearResumenDns({ eventos_edac: 0 }) });
    render(<DnsPage />);
    expect(await screen.findByText("Sin eventos EDAC en el período")).toBeInTheDocument();
  });

  it("solo ofrece las opciones que la API acepta", async () => {
    api();
    render(<DnsPage />);
    await esperarCarga();
    const valores = (n: string) => within(screen.getByRole("combobox", { name: n })).getAllByRole("option").map((o) => (o as HTMLOptionElement).value);
    expect(valores("Período")).toEqual(["12", "36", "60", "0"]);
    expect(valores("Origen")).toEqual(["", "programada", "no_programada"]);
    expect(valores("Región")).toEqual(["", "Norte", "Sur", "Sin asignar"]);
    expect(valores("Subárea")).toEqual(["", "Are0002", "Are0003", "Are0001"]);
  });

  it("al elegir una region, la subarea se limita a esa region y vuelve a «Todas»", async () => {
    api();
    render(<DnsPage />);
    await esperarCarga();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Subárea" }), "Are0003");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Región" }), "Norte");
    const sub = screen.getByRole("combobox", { name: "Subárea" }) as HTMLSelectElement;
    expect(sub.value).toBe("");
    expect(within(sub).getAllByRole("option").map((o) => (o as HTMLOptionElement).value)).toEqual(["", "Are0002", "Are0001"]);
  });

  it("cambiar el periodo vuelve a consultar los 4 bloques de eventos y NO los resultados del modelo", async () => {
    const { llamadas } = api();
    render(<DnsPage />);
    await esperarCarga();
    const antes = Object.fromEntries(RUTAS.map((r) => [r, cantidad(llamadas, r)]));
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Período" }), "12");
    await waitFor(() => {
      for (const r of ["resumen", "serie", "patrones", "causas"]) expect(ultima(llamadas, r).searchParams.get("periodo_meses")).toBe("12");
    });
    for (const r of ["zonas", "cambios-reporte", "modelo", "catalogo"]) expect(cantidad(llamadas, r)).toBe(antes[r]);
  });

  it("el origen afecta a los bloques de eventos, no a zonas, cambios ni modelo", async () => {
    const { llamadas } = api();
    render(<DnsPage />);
    await esperarCarga();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Origen" }), "programada");
    await waitFor(() => expect(ultima(llamadas, "resumen").searchParams.get("origen")).toBe("programada"));
    for (const r of ["serie", "patrones", "causas"]) expect(ultima(llamadas, r).searchParams.get("origen")).toBe("programada");
    for (const r of ["zonas", "cambios-reporte", "modelo"]) expect(ultima(llamadas, r).searchParams.has("origen")).toBe(false);
  });

  it("la region llega a TODOS los bloques", async () => {
    const { llamadas } = api();
    render(<DnsPage />);
    await esperarCarga();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Región" }), "Norte");
    await waitFor(() => {
      for (const r of ["resumen", "serie", "patrones", "causas", "zonas", "cambios-reporte", "modelo"]) {
        expect(ultima(llamadas, r).searchParams.get("region")).toBe("Norte");
      }
    });
  });

  it("«Restablecer filtros» vuelve a los valores por defecto", async () => {
    api();
    render(<DnsPage />);
    await esperarCarga();
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Período" }), "0");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Región" }), "Sur");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Origen" }), "no_programada");
    await userEvent.click(screen.getByRole("button", { name: /Restablecer filtros/ }));
    expect(screen.getByRole("combobox", { name: "Período" })).toHaveValue("36");
    expect(screen.getByRole("combobox", { name: "Región" })).toHaveValue("");
    expect(screen.getByRole("combobox", { name: "Subárea" })).toHaveValue("");
    expect(screen.getByRole("combobox", { name: "Origen" })).toHaveValue("");
  });

  it("un clic en una zona del ranking filtra todo el tablero a esa subarea (y otro clic la quita)", async () => {
    const { llamadas } = api();
    render(<DnsPage />);
    await esperarCarga();
    await userEvent.click(screen.getByRole("button", { name: "SubArea Tres" }));
    await waitFor(() => expect(ultima(llamadas, "resumen").searchParams.get("subarea")).toBe("Are0003"));
    expect(ultima(llamadas, "resumen").searchParams.get("region")).toBe("Sur");
    expect(screen.getByRole("combobox", { name: "Subárea" })).toHaveValue("Are0003");
    expect(screen.getByRole("button", { name: "SubArea Tres" })).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(screen.getByRole("button", { name: "SubArea Tres" }));
    await waitFor(() => expect(ultima(llamadas, "resumen").searchParams.has("subarea")).toBe(false));
  });

  it("cada filtro y cada bloque tienen su boton de ayuda ⓘ", async () => {
    api();
    render(<DnsPage />);
    await esperarCarga();
    for (const nombre of [
      "Filtro de período", "Filtro de región", "Filtro de subárea", "Filtro de origen", "Eventos DNS", "Energía no atendida",
      "Eventos críticos", "Eventos no programados", "Serie mensual y pronóstico", "Priorización de zonas", "Patrones en el tiempo",
      "Causas de los eventos", "Cambios en la forma de reportar", "Modelo predictivo",
    ]) {
      expect(screen.getByRole("button", { name: `Ayuda: ${nombre}` })).toBeInTheDocument();
    }
  });

  it("si un bloque falla, muestra su error sin tumbar el resto", async () => {
    api({ [`${D}/causas`]: () => ({ status: 404, cuerpo: { detalle: "modelo no cargado" } }) });
    render(<DnsPage />);
    expect(await screen.findByText(/No fue posible cargar las causas: modelo no cargado/)).toBeInTheDocument();
    expect(await esperarCarga()).toBeInTheDocument();
    expect(kpi(/^Energía no atendida$/i)).toHaveTextContent("214,1 GWh");
  });

  it("si el resumen falla muestra el error en lugar de las tarjetas", async () => {
    api({ [`${D}/resumen`]: () => ({ status: 422, cuerpo: { detalle: "La region 'Marte' no existe" } }) });
    render(<DnsPage />);
    expect(await screen.findByText(/No fue posible cargar los indicadores: La region 'Marte' no existe/)).toBeInTheDocument();
  });

  it("si falla el catalogo avisa y deja los filtros sin regiones", async () => {
    api({ [`${D}/catalogo`]: () => ({ status: 404, cuerpo: { detalle: "sin modelo" } }) });
    render(<DnsPage />);
    expect(await screen.findByText(/No fue posible cargar el catálogo del modelo: sin modelo/)).toBeInTheDocument();
    expect(within(screen.getByRole("combobox", { name: "Región" })).getAllByRole("option")).toHaveLength(1);
  });

  it("incluye el enlace de vuelta al panel y el pie institucional", async () => {
    api();
    render(<DnsPage />);
    expect(screen.getByRole("link", { name: "Tableros" })).toHaveAttribute("href", "/");
    expect(screen.getByText(/Fuente: SIMEM \(eventos DNS y EDAC/)).toBeInTheDocument();
  });
});

describe("Serie mensual", () => {
  it("dibuja los meses con el pronostico en su mes y atenua el mes parcial", async () => {
    api();
    render(<DnsPage />);
    const grafico = (await screen.findAllByTestId("composed-chart"))[0];
    const puntos = JSON.parse(grafico.dataset.points!);
    expect(puntos).toHaveLength(3);
    expect(puntos[2]).toMatchObject({ valor: 40, parcial: true, pronostico: 311 });
    expect(screen.getByText("Pronóstico del modelo para 2026-08: 311 (19 subáreas)")).toBeInTheDocument();
    expect(screen.getByText(/El último mes está atenuado/)).toBeInTheDocument();
  });

  it("alternar a Energia cambia el titulo, los valores y el pronostico sin consultar de nuevo", async () => {
    const { llamadas } = api();
    render(<DnsPage />);
    await esperarCarga();
    const antes = llamadas.length;
    await userEvent.click(screen.getByRole("button", { name: "Energía" }));
    expect(llamadas.length).toBe(antes);
    expect(screen.getByText("Energía no atendida (GWh) por mes")).toBeInTheDocument();
    const puntos = JSON.parse(screen.getAllByTestId("composed-chart")[0].dataset.points!);
    expect(puntos[1].valor).toBe(6.0);
    expect(screen.getByText("Pronóstico del modelo para 2026-08: 3,5 (19 subáreas)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Energía" })).toHaveAttribute("aria-pressed", "true");
  });

  it("si no hay pronostico muestra la nota que explica por que", async () => {
    api({ [`${D}/serie`]: () => crearSerieDns({ pronostico: null, nota_pronostico: "El pronóstico no se separa por origen." }) });
    render(<DnsPage />);
    expect(await screen.findByText("El pronóstico no se separa por origen.")).toBeInTheDocument();
    expect(screen.getByText("Observado mensual")).toBeInTheDocument();
  });
});

describe("Zonas, patrones, causas, cambios y modelo", () => {
  it("el ranking muestra indice, energia y la tendencia con su color", async () => {
    api();
    render(<DnsPage />);
    const fila = (await screen.findByRole("button", { name: "SubArea Uno" })).closest("tr")!;
    expect(fila).toHaveTextContent("83,2");
    expect(fila).toHaveTextContent("164,5");
    expect(within(fila).getByText("−6,0 %")).toHaveStyle({ color: "var(--color-optimo)" });
    const peor = screen.getByRole("button", { name: "SubArea Tres" }).closest("tr")!;
    expect(within(peor).getByText("+2.081,2 %")).toHaveStyle({ color: "var(--color-critico)" });
  });

  it("un ambito sin zonas lo dice", async () => {
    api({ [`${D}/zonas`]: () => ({ zonas: [] }) });
    render(<DnsPage />);
    expect(await screen.findByText("El modelo no prioriza ninguna subárea de este ámbito.")).toBeInTheDocument();
  });

  it("patrones: tres graficos con sus datos y la nota de la hora desconocida", async () => {
    api();
    render(<DnsPage />);
    await esperarCarga();
    const graficos = screen.getAllByTestId("bar-chart").map((g) => JSON.parse(g.dataset.points!));
    const porHora = graficos.find((g) => g.length === 24)!;
    expect(porHora[7]).toEqual({ hora: "7h", eventos: 90 });
    const porDia = graficos.find((g) => g.length === 7)!;
    expect(porDia[6]).toEqual({ dia: "Dom", eventos: 30 });
    const franjas = graficos.find((g) => g.length === 4)!;
    expect(franjas[0]).toEqual({ franja: "Madrugada", noProgramada: 60, programada: 40 });
    expect(franjas[3]).toEqual({ franja: "Noche", noProgramada: 0, programada: 0 });
    expect(screen.getByText("Hora con más eventos: 7h · 105 eventos con hora conocida")).toBeInTheDocument();
    expect(screen.getByText(/Se excluyen 14 eventos con hora desconocida/)).toBeInTheDocument();
  });

  it("patrones sin eventos con hora lo dice", async () => {
    api({ [`${D}/patrones`]: () => crearPatronesDns({ eventos_usados: 0, por_hora: Array(24).fill(0) }) });
    render(<DnsPage />);
    expect(await screen.findByText("Sin eventos con hora conocida en este filtro")).toBeInTheDocument();
  });

  it("causas: porcentaje, energia y el aviso de que parte se infirio del texto", async () => {
    api();
    render(<DnsPage />);
    const lista = await screen.findByRole("list", { name: "Eventos por causa" });
    expect(within(lista).getByText("Mantenimiento")).toBeInTheDocument();
    expect(lista).toHaveTextContent("48 eventos · 48 % · 145,3 GWh");
    expect(screen.getByText("Sin clasificar")).toBeInTheDocument();
    expect(screen.getByText(/30 % de las causas se infirieron del texto/)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Tipos de evento" }).querySelectorAll("li")).toHaveLength(5);
  });

  it("causas sin eventos", async () => {
    api({ [`${D}/causas`]: () => crearCausasDns({ total: 0, causas: [], origen_de_la_causa: [], tipos_evento: [] }) });
    render(<DnsPage />);
    expect(await screen.findByText("No hay eventos con estos filtros.")).toBeInTheDocument();
  });

  it("cambios de reporte: el antes y el despues de cada subarea", async () => {
    api();
    render(<DnsPage />);
    const fila = (await screen.findByText("Cambios en la forma de reportar")).closest("div[class*=rounded-2xl]")!.querySelector("tbody tr")!;
    expect(fila).toHaveTextContent("SubArea Uno");
    expect(fila).toHaveTextContent("0 % → 83 %");
    expect(fila).toHaveTextContent("25 % → 3 %");
  });

  it("modelo: mejora frente a la persistencia, importancia y pronostico por subarea", async () => {
    api();
    render(<DnsPage />);
    const eventos = await screen.findByRole("region", { name: "Métricas de Número de eventos" });
    expect(within(eventos).getByText("referencia")).toBeInTheDocument();
    expect(within(eventos).getByText("21,5 %")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Métricas de Energía no atendida (kWh)" })).toHaveTextContent("238.279");
    expect(screen.getByRole("region", { name: "Variables más importantes" })).toHaveTextContent("56,7 %");
    const pron = screen.getByRole("region", { name: "Pronóstico por subárea" });
    expect(pron).toHaveTextContent("SubArea Uno");
    expect(pron).toHaveTextContent("64,8");
  });

  it("modelo sin subareas pronosticadas en el ambito", async () => {
    api({ [`${D}/modelo`]: () => crearModeloDns({ pronostico: [] }) });
    render(<DnsPage />);
    expect(await screen.findByText("El modelo no pronostica ninguna subárea de este ámbito.")).toBeInTheDocument();
  });
});
