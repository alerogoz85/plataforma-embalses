import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ApagonPage from "@/app/apagon/page";
import GasPage from "@/app/gas/page";
import OptimizacionPage from "@/app/optimizacion/page";
import { ApiError, obtenerFichaModelo, obtenerResultadosModelo } from "@/lib/api/client";
import { simularFetch } from "../mocks/fetch";
import { conResultados, crearFichaModelo, crearResultadoModelo, sinResultados } from "./fixturesModelos";

vi.mock("recharts", () => import("../mocks/recharts"));

const M = "/api/v1/modelos";

function api(modelo = "apagon", { ficha = crearFichaModelo({ id: modelo as never }), resultados = sinResultados(modelo as never) as unknown } = {}) {
  return simularFetch({
    [`${M}/${modelo}/ficha`]: () => ficha,
    [`${M}/${modelo}/resultados`]: () => resultados,
  });
}

describe("cliente de los modelos analiticos", () => {
  it("pide la ficha y los resultados por id y codifica el id", async () => {
    const { llamadas } = simularFetch({ [`${M}/apagon/ficha`]: () => ({ ok: 1 }), [`${M}/a%20b/resultados`]: () => ({ ok: 2 }) });
    await expect(obtenerFichaModelo("apagon")).resolves.toEqual({ ok: 1 });
    await obtenerResultadosModelo("a b").catch(() => null);
    expect(llamadas[0].pathname).toBe(`${M}/apagon/ficha`);
    expect(llamadas[1].pathname).toBe(`${M}/a%20b/resultados`);
  });

  it("un modelo inexistente es un ApiError 404 con el mensaje", async () => {
    simularFetch({ [`${M}/otro/ficha`]: () => ({ status: 404, cuerpo: { detalle: "El modelo 'otro' no existe" } }) });
    await expect(obtenerFichaModelo("otro")).rejects.toMatchObject({ status: 404, message: "El modelo 'otro' no existe" });
    await expect(obtenerFichaModelo("otro")).rejects.toBeInstanceOf(ApiError);
  });
});

describe("Tablero de un modelo sin resultados", () => {
  it("muestra el estado documentado, las cifras documentadas y como cargar los resultados", async () => {
    api();
    render(<ApagonPage />);
    expect(await screen.findByText("Sin resultados publicados", { selector: "span" })).toBeInTheDocument();
    expect(screen.getByText(/no se dispone de una corrida final/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Riesgo de apagón condicionado por ENOS");
    const cifras = screen.getByRole("region", { name: "Cifras documentadas" });
    expect(cifras).toHaveTextContent("3.000");
    expect(cifras).toHaveTextContent("Actividad 5");
    expect(await screen.findByText("Aún no hay resultados cargados")).toBeInTheDocument();
    expect(screen.getByText("resultados_modelo_riesgo_apagon/resumen_mensual.csv")).toBeInTheDocument();
    expect(screen.getByLabelText("Comando de importación")).toHaveTextContent("importar_resultado_modelo --modelo apagon");
  });

  it("no inventa nada: sin filtros, graficos ni tablas de resultados", async () => {
    api();
    render(<ApagonPage />);
    await screen.findByText("Aún no hay resultados cargados");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByTestId("composed-chart")).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("la ficha lista la pregunta y sus secciones; solo la primera abierta", async () => {
    api();
    const { container } = render(<ApagonPage />);
    await screen.findByText("Ficha del modelo");
    expect(screen.getByText(/Pregunta que responde:/).closest("p")).toHaveTextContent("¿Qué probabilidad tiene el SIN de no cubrir la demanda?");
    const secciones = [...container.querySelectorAll("details")];
    expect(secciones.map((d) => d.querySelector("summary")!.textContent)).toEqual(["Método", "Limitaciones documentadas"]);
    expect(secciones.map((d) => d.open)).toEqual([true, false]);
  });

  it("cada tablero consulta su propio modelo", async () => {
    for (const [Pagina, id] of [[GasPage, "gas"], [OptimizacionPage, "optimizacion"], [ApagonPage, "apagon"]] as const) {
      const { llamadas } = api(id);
      const { unmount } = render(<Pagina />);
      await screen.findByText("Aún no hay resultados cargados");
      expect(llamadas.map((u) => u.pathname).sort()).toEqual([`${M}/${id}/ficha`, `${M}/${id}/resultados`]);
      unmount();
    }
  });

  it("la optimizacion en prueba tecnica se muestra en rojo y como no publicable", async () => {
    api("optimizacion", { ficha: crearFichaModelo({ id: "optimizacion", estado: "prueba_tecnica", estado_detalle: "INSUFFICIENT_RISK_SAMPLE y publishable = false." }) });
    render(<OptimizacionPage />);
    const etiqueta = await screen.findByText("Prueba técnica: no publicable", { selector: "span" });
    expect(etiqueta).toHaveStyle({ color: "var(--color-critico)" });
  });

  it("incluye el enlace de vuelta al panel y las ayudas ⓘ", async () => {
    api();
    render(<ApagonPage />);
    await screen.findByText("Aún no hay resultados cargados");
    expect(screen.getByRole("link", { name: "Tableros" })).toHaveAttribute("href", "/");
    for (const nombre of ["Estado del modelo", "Cifras documentadas", "Cómo cargar los resultados", "Ficha del modelo"]) {
      expect(screen.getByRole("button", { name: `Ayuda: ${nombre}` })).toBeInTheDocument();
    }
  });

  it("si falla la ficha muestra el error y no el contenido", async () => {
    simularFetch({ [`${M}/apagon/ficha`]: () => ({ status: 404, cuerpo: { detalle: "no existe" } }), [`${M}/apagon/resultados`]: () => sinResultados() });
    render(<ApagonPage />);
    expect(await screen.findByText(/No fue posible cargar la ficha del modelo: no existe/)).toBeInTheDocument();
    expect(screen.queryByText("Ficha del modelo")).not.toBeInTheDocument();
  });

  it("si fallan los resultados avisa pero deja ver la ficha", async () => {
    simularFetch({ [`${M}/apagon/ficha`]: () => crearFichaModelo(), [`${M}/apagon/resultados`]: () => ({ status: 422, cuerpo: { detalle: "mal" } }) });
    render(<ApagonPage />);
    expect(await screen.findByText(/No fue posible cargar los resultados: mal/)).toBeInTheDocument();
    expect(await screen.findByText("Ficha del modelo")).toBeInTheDocument();
  });
});

describe("Tablero de un modelo con resultados", () => {
  const montar = () => {
    const sim = api("apagon", { ficha: crearFichaModelo({ estado: "con_resultados" }), resultados: conResultados() });
    render(<ApagonPage />);
    return sim;
  };

  it("muestra los indicadores con su nivel, las advertencias y la procedencia", async () => {
    montar();
    const rojo = (await screen.findByText("Meses en rojo")).closest("div")!.parentElement!;
    expect(rojo).toHaveTextContent("1");
    expect(rojo).toHaveTextContent("de 3 meses");
    expect(screen.getByText("Mayor probabilidad de déficit").closest("div")!.parentElement!).toHaveTextContent("60,0 %");
    expect(screen.getByText("Mide adecuación de generación nacional agregada.")).toBeInTheDocument();
    expect(screen.getByText(/importada/)).toHaveTextContent("Modelo de riesgo de apagón (Monte Carlo)");
    expect(screen.getByText("Horizonte (meses)")).toBeInTheDocument();
    expect(screen.queryByText("Aún no hay resultados cargados")).not.toBeInTheDocument();
    expect(screen.getByText("Con resultados importados", { selector: "span" })).toBeInTheDocument();
  });

  it("dibuja un grafico por serie, con banda y barras segun corresponda", async () => {
    montar();
    await screen.findByText("Meses en rojo");
    expect(screen.getAllByTestId("composed-chart")).toHaveLength(2);
    expect(screen.getAllByTestId("bar-chart")).toHaveLength(1);
    expect(screen.getAllByTestId("area").map((a) => a.dataset.name)).toContain("Escenarios P10–P90");
    const puntosEmbalse = JSON.parse(screen.getAllByTestId("composed-chart")[1].dataset.points!);
    expect(puntosEmbalse[0]).toMatchObject({ valor: 55, bandaBase: 40, bandaRango: 30 });
  });

  it("la tabla muestra «—» para el dato vacio, nunca cero", async () => {
    montar();
    const tabla = await screen.findByRole("table", { name: "Semáforo y probabilidades por mes" });
    const filas = within(tabla).getAllByRole("row");
    expect(filas[3]).toHaveTextContent("Rojo");
    expect(filas[3]).toHaveTextContent("—");
    expect(filas[2]).toHaveTextContent("40,50");
    expect(screen.getByText("El déficit no incluye restricciones de red.")).toBeInTheDocument();
  });

  it("el filtro de periodo recorta TODAS las series a la vez y no vuelve a consultar", async () => {
    const { llamadas } = montar();
    await screen.findByText("Meses en rojo");
    const antes = llamadas.length;
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Desde" }), "2026-11");
    for (const g of [...screen.getAllByTestId("composed-chart"), ...screen.getAllByTestId("bar-chart")]) {
      expect(JSON.parse(g.dataset.points!).map((p: { x: string }) => p.x)).toEqual(["2026-11", "2026-12"]);
    }
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Hasta" }), "2026-11");
    for (const g of [...screen.getAllByTestId("composed-chart"), ...screen.getAllByTestId("bar-chart")]) {
      expect(JSON.parse(g.dataset.points!).map((p: { x: string }) => p.x)).toEqual(["2026-11"]);
    }
    expect(llamadas.length).toBe(antes);
  });

  it("Desde y Hasta se limitan entre si para no cruzarse", async () => {
    montar();
    await screen.findByText("Meses en rojo");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Desde" }), "2026-11");
    const hasta = within(screen.getByRole("combobox", { name: "Hasta" })).getAllByRole("option").map((o) => (o as HTMLOptionElement).value);
    expect(hasta).toEqual(["", "2026-11", "2026-12"]);
  });

  it("«Restablecer filtros» devuelve todas las series completas", async () => {
    montar();
    await screen.findByText("Meses en rojo");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Desde" }), "2026-12");
    await userEvent.click(screen.getByRole("button", { name: /Restablecer filtros/ }));
    expect(screen.getByRole("combobox", { name: "Desde" })).toHaveValue("");
    expect(JSON.parse(screen.getAllByTestId("composed-chart")[0].dataset.points!)).toHaveLength(3);
  });

  it("sin series mensuales no ofrece filtro de periodo", async () => {
    api("apagon", { resultados: conResultados(crearResultadoModelo({ series: [] })) });
    render(<ApagonPage />);
    await screen.findByText("Meses en rojo");
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Series del modelo" })).not.toBeInTheDocument();
  });

  it("una serie sin datos en el rango lo dice en su grafico (y las demas siguen)", async () => {
    const base = crearResultadoModelo();
    const soloOctubre = { ...base.series[0], id: "corta", titulo: "Serie corta", puntos: [base.series[0].puntos[0]] };
    api("apagon", { resultados: conResultados(crearResultadoModelo({ series: [soloOctubre, base.series[1]] })) });
    render(<ApagonPage />);
    await screen.findByText("Meses en rojo");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Desde" }), "2026-12");
    expect(screen.getByText("Sin datos en el período elegido.")).toBeInTheDocument();
    expect(screen.getAllByTestId("composed-chart")).toHaveLength(1);
  });

  it("los datos documentados se siguen mostrando junto a los resultados", async () => {
    montar();
    await screen.findByText("Meses en rojo");
    await waitFor(() => expect(screen.getByRole("region", { name: "Cifras documentadas" })).toHaveTextContent("317 meses"));
  });
});
