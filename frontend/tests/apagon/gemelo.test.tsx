import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ApagonPage from "@/app/apagon/page";
import { crearFichaModelo } from "../modelos/fixturesModelos";
import { simularFetch } from "../mocks/fetch";
import { crearCatalogo, crearEscenario } from "./fixturesEscenario";

vi.mock("recharts", () => import("../mocks/recharts"));

const M = "/api/v1/modelos/apagon";

function api(catalogo = crearCatalogo()) {
  return simularFetch({
    [`${M}/escenarios`]: () => catalogo,
    [`${M}/ficha`]: () => crearFichaModelo({ estado: "con_resultados" }),
    [`${M}/escenario`]: (u) =>
      crearEscenario({
        modo: u.searchParams.get("modo") as "manual", oni: Number(u.searchParams.get("oni") ?? 1),
        simulaciones: Number(u.searchParams.get("simulaciones")), horizonte: Number(u.searchParams.get("horizonte")),
      }),
  });
}

const escenarios = (llamadas: URL[]) => llamadas.filter((u) => u.pathname === `${M}/escenario`);

describe("Visor de riesgo de apagón", () => {
  it("abre en modo manual con ONI 1,0, 2000 simulaciones y 18 meses, y muestra indicadores y gráficos", async () => {
    const { llamadas } = api();
    render(<ApagonPage />);
    expect(await screen.findByRole("heading", { level: 1, name: /Gemelo digital de riesgo de apagón/ })).toBeInTheDocument();
    await waitFor(() => expect(escenarios(llamadas)).toHaveLength(1));
    const q = escenarios(llamadas)[0].searchParams;
    expect([q.get("modo"), q.get("oni"), q.get("simulaciones"), q.get("horizonte")]).toEqual(["manual", "1", "2000", "18"]);
    expect(screen.getByLabelText("Fase ENOS")).toHaveTextContent("El Niño moderado");
    const kpis = await screen.findByRole("region", { name: "Indicadores del escenario" });
    expect(kpis).toHaveTextContent("Peor índice de riesgo");
    expect(kpis).toHaveTextContent("Meses en ROJO");
    expect(screen.getByRole("img", { name: /Índice de riesgo por mes/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Mapa de calor/ })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Demanda y oferta/ })).toBeInTheDocument();
    expect(screen.getByText(/Ver tabla mensual completa/)).toBeInTheDocument();
  });

  it("mover el ONI pide el escenario de ese ONI y lo guarda en la URL", async () => {
    const { llamadas } = api();
    render(<ApagonPage />);
    const oni = await screen.findByLabelText("ONI objetivo (°C)");
    fireEvent.change(oni, { target: { value: "1.2" } });
    await waitFor(() => expect(escenarios(llamadas).at(-1)?.searchParams.get("oni")).toBe("1.2"));
    expect(window.location.search).toContain("oni=1.2");
    expect(screen.getByLabelText("Fase ENOS")).toHaveTextContent("El Niño moderado");
  });

  it("en modo Pronóstico ENOS no hay ONI que mover y no se envía", async () => {
    const { llamadas } = api();
    render(<ApagonPage />);
    await screen.findByLabelText("ONI objetivo (°C)");
    await userEvent.click(screen.getByRole("radio", { name: /Pronóstico ENOS/ }));
    expect(screen.queryByLabelText("ONI objetivo (°C)")).not.toBeInTheDocument();
    expect(screen.getByText(/pronóstico probabilístico de ENOS vigente/)).toBeInTheDocument();
    await waitFor(() => expect(escenarios(llamadas).at(-1)?.searchParams.get("modo")).toBe("probabilistico"));
    expect(escenarios(llamadas).at(-1)?.searchParams.has("oni")).toBe(false);
  });

  it("los deslizadores de simulaciones y horizonte recorren sus opciones", async () => {
    const { llamadas } = api();
    render(<ApagonPage />);
    const sim = await screen.findByLabelText("Simulaciones Monte Carlo");
    fireEvent.change(sim, { target: { value: "2" } });
    await waitFor(() => expect(escenarios(llamadas).at(-1)?.searchParams.get("simulaciones")).toBe("5000"));
    fireEvent.change(screen.getByLabelText("Horizonte (meses)"), { target: { value: "2" } });
    await waitFor(() => expect(escenarios(llamadas).at(-1)?.searchParams.get("horizonte")).toBe("24"));
  });

  it("Restablecer controles vuelve a los valores iniciales", async () => {
    window.history.replaceState(null, "", "/apagon?modo=probabilistico&simulaciones=5000&horizonte=24");
    api();
    render(<ApagonPage />);
    await screen.findByText(/pronóstico probabilístico de ENOS vigente/);
    await userEvent.click(screen.getByRole("button", { name: /Restablecer controles/ }));
    expect(await screen.findByLabelText("ONI objetivo (°C)")).toHaveValue("1");
    expect(window.location.search).toBe("");
  });

  it("un parámetro fuera de las opciones de la URL se ignora", async () => {
    window.history.replaceState(null, "", "/apagon?oni=9&simulaciones=7&horizonte=5&modo=x");
    const { llamadas } = api();
    render(<ApagonPage />);
    await waitFor(() => expect(escenarios(llamadas)).toHaveLength(1));
    const q = escenarios(llamadas)[0].searchParams;
    expect([q.get("modo"), q.get("oni"), q.get("simulaciones"), q.get("horizonte")]).toEqual(["manual", "1", "2000", "18"]);
  });

  it("la tabla mensual completa trae una fila por mes con el semáforo en texto", async () => {
    window.history.replaceState(null, "", "/apagon?horizonte=12");
    api();
    render(<ApagonPage />);
    await screen.findByRole("region", { name: "Indicadores del escenario" });
    const tabla = screen.getByRole("table");
    expect(within(tabla).getAllByRole("row")).toHaveLength(13);
    expect(within(tabla).getAllByText("Rojo").length).toBeGreaterThan(0);
  });

  it("sin escenarios importados queda el tablero genérico, que dice qué falta", async () => {
    window.history.replaceState(null, "", "/apagon");
    simularFetch({
      [`${M}/escenarios`]: () => crearCatalogo({ disponible: false, fuente: null }),
      [`${M}/ficha`]: () => crearFichaModelo(),
      [`${M}/resultados`]: () => ({ modelo_id: "apagon", disponible: false, resultado: null }),
    });
    render(<ApagonPage />);
    expect(await screen.findByText("Aún no hay resultados cargados")).toBeInTheDocument();
    expect(screen.queryByLabelText("Controles del escenario")).not.toBeInTheDocument();
  });

  it("si el escenario falla muestra el error sin romper los controles", async () => {
    window.history.replaceState(null, "", "/apagon");
    simularFetch({ [`${M}/escenarios`]: () => crearCatalogo(), [`${M}/ficha`]: () => crearFichaModelo(), [`${M}/escenario`]: () => ({ status: 404, cuerpo: { detalle: "Aún no hay escenarios" } }) });
    render(<ApagonPage />);
    expect(await screen.findByText(/Aún no hay escenarios/)).toBeInTheDocument();
    expect(screen.getByLabelText("Controles del escenario")).toBeInTheDocument();
  });
});
