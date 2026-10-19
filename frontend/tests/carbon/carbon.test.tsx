import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import CarbonPage from "@/app/carbon/page";
import { ComparacionXmChart } from "@/components/carbon/ComparacionXmChart";
import { SerieCarbonChart } from "@/components/carbon/SerieCarbonChart";
import { ValidacionCarbonPanel } from "@/components/carbon/ValidacionCarbonPanel";
import { simularFetch } from "../mocks/fetch";
import { crearComparacionXm, crearInventario, crearResumenCarbon, crearSerieCarbon, crearValidacionCarbon } from "./fixturesCarbon";

vi.mock("recharts", () => import("../mocks/recharts"));

const R = "/api/v1/carbon";

function api(sobre: Record<string, (u: URL) => unknown> = {}) {
  return simularFetch({
    [`${R}/resumen`]: () => crearResumenCarbon(),
    [`${R}/serie`]: () => crearSerieCarbon(),
    [`${R}/inventario`]: () => crearInventario(),
    [`${R}/comparacion-xm`]: () => crearComparacionXm(),
    [`${R}/validacion`]: () => crearValidacionCarbon(),
    ...sobre,
  });
}

const kpi = (etiqueta: RegExp) => screen.getByText(etiqueta).closest("div")!.parentElement!;

describe("Tablero de carbon termico (pagina)", () => {
  it("consulta los 5 endpoints con los valores por defecto (36 meses, 9, 45 dias)", async () => {
    const { llamadas } = api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2 criterios/);
    const por = (ruta: string) => llamadas.find((u) => u.pathname === `${R}/${ruta}`)!.searchParams;
    expect(por("resumen").get("horizonte_meses")).toBe("9");
    expect(por("resumen").get("dias")).toBe("45");
    expect(por("serie").get("historia_meses")).toBe("36");
    expect(por("inventario").get("dias")).toBe("45");
    expect(por("comparacion-xm").get("horizonte_meses")).toBe("9");
  });

  it("pide el resumen una sola vez aunque lo usen tarjetas y trimestres", async () => {
    const { llamadas } = api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    expect(llamadas.filter((u) => u.pathname === `${R}/resumen`)).toHaveLength(1);
  });

  it("muestra las 4 tarjetas con el pico, el uso del techo, la probabilidad y el inventario", async () => {
    api();
    render(<CarbonPage />);
    const pico = await waitFor(() => kpi(/Pico esperado · feb de 2027/i));
    expect(pico).toHaveTextContent("350,0 GBTU/día");
    expect(pico).toHaveTextContent("P10–P90: 300,0 – 400,0");
    expect(kpi(/Uso del techo térmico/i)).toHaveTextContent("87.5%");
    expect(kpi(/Uso del techo térmico/i)).toHaveTextContent("Ajustado");
    expect(kpi(/Prob. de superar el récord/i)).toHaveTextContent("62%");
    expect(kpi(/Inventario de 45 días/i)).toHaveTextContent("630 kt");
    expect(kpi(/Inventario de 45 días/i)).toHaveTextContent("P90: 720 kt");
  });

  it("el encabezado indica que el ultimo mes esta en curso", async () => {
    api();
    render(<CarbonPage />);
    expect(await screen.findByText(/oct de 2026 \(mes en curso\) · proyección a 9 meses/)).toBeInTheDocument();
  });

  it("cambiar el horizonte vuelve a consultar TODOS los bloques que dependen de el", async () => {
    const { llamadas } = api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Horizonte" }), "3");
    await waitFor(() => {
      for (const ruta of ["resumen", "serie", "inventario", "comparacion-xm"]) {
        expect(llamadas.filter((u) => u.pathname === `${R}/${ruta}`).at(-1)!.searchParams.get("horizonte_meses")).toBe("3");
      }
    });
  });

  it("cambiar los dias de inventario afecta tarjeta e inventario, no la serie", async () => {
    const { llamadas } = api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    const serieAntes = llamadas.filter((u) => u.pathname === `${R}/serie`).length;
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Días de inventario" }), "60");
    await waitFor(() => expect(llamadas.filter((u) => u.pathname === `${R}/inventario`).at(-1)!.searchParams.get("dias")).toBe("60"));
    expect(llamadas.filter((u) => u.pathname === `${R}/resumen`).at(-1)!.searchParams.get("dias")).toBe("60");
    expect(llamadas.filter((u) => u.pathname === `${R}/serie`)).toHaveLength(serieAntes);
  });

  it("cambiar la historia solo vuelve a pedir la serie", async () => {
    const { llamadas } = api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    const antes = llamadas.length;
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Historia" }), "0");
    await waitFor(() => expect(llamadas.length).toBe(antes + 1));
    expect(llamadas.at(-1)!.pathname).toBe(`${R}/serie`);
    expect(llamadas.at(-1)!.searchParams.get("historia_meses")).toBe("0");
  });

  it("la unidad kt convierte tarjetas y grafico sin consultar de nuevo", async () => {
    const { llamadas } = api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    const antes = llamadas.length;
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Unidad" }), "kt");
    expect(llamadas.length).toBe(antes);
    expect(kpi(/Pico esperado/i)).toHaveTextContent("14,00 kt/día");
    const lineas = screen.getAllByTestId("reference-line").map((l) => l.dataset.y);
    expect(lineas).toContain("16"); // techo 400 GBTU/dia = 16 kt/dia
  });

  it("«Restablecer filtros» devuelve todos los filtros a sus valores por defecto", async () => {
    api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Horizonte" }), "1");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Unidad" }), "kt");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Historia" }), "12");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Días de inventario" }), "15");
    await userEvent.click(screen.getByRole("button", { name: /Restablecer filtros/ }));
    expect(screen.getByRole("combobox", { name: "Horizonte" })).toHaveValue("9");
    expect(screen.getByRole("combobox", { name: "Unidad" })).toHaveValue("gbtu");
    expect(screen.getByRole("combobox", { name: "Historia" })).toHaveValue("36");
    expect(screen.getByRole("combobox", { name: "Días de inventario" })).toHaveValue("45");
  });

  it("solo ofrece las opciones que la API acepta", async () => {
    api();
    render(<CarbonPage />);
    const valores = (n: string) => within(screen.getByRole("combobox", { name: n })).getAllByRole("option").map((o) => (o as HTMLOptionElement).value);
    expect(valores("Historia")).toEqual(["12", "36", "60", "0"]);
    expect(valores("Horizonte")).toEqual(["1", "3", "6", "9"]);
    expect(valores("Días de inventario")).toEqual(["15", "30", "45", "60"]);
    expect(valores("Unidad")).toEqual(["gbtu", "kt"]);
  });

  it("cada filtro y cada bloque tienen su boton de ayuda ⓘ", async () => {
    api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    for (const nombre of ["Filtro de historia", "Filtro de horizonte", "Unidad del consumo", "Días de inventario", "Pico esperado de consumo", "Uso del techo térmico", "Consumo por trimestre", "Inventario de carbón requerido", "Comparación con la proyección de XM", "Validación del modelo", "Supuestos y limitaciones"]) {
      expect(screen.getByRole("button", { name: `Ayuda: ${nombre}` })).toBeInTheDocument();
    }
  });

  it("muestra el error de un bloque sin tumbar el resto de la pagina", async () => {
    api({ [`${R}/inventario`]: () => ({ status: 404, cuerpo: { detalle: "modelo no cargado" } }) });
    render(<CarbonPage />);
    expect(await screen.findByText(/No fue posible cargar el inventario: modelo no cargado/)).toBeInTheDocument();
    expect(await screen.findByText(/Cumple 1 de 2/)).toBeInTheDocument();
    expect(kpi(/Prob. de superar el récord/i)).toBeInTheDocument();
  });

  it("si el resumen falla muestra el error en lugar de las tarjetas y de los trimestres", async () => {
    api({ [`${R}/resumen`]: () => ({ status: 404, cuerpo: { detalle: "sin modelo" } }) });
    render(<CarbonPage />);
    expect(await screen.findByText(/No fue posible cargar los indicadores: sin modelo/)).toBeInTheDocument();
    expect(screen.getByText(/No fue posible cargar los trimestres: sin modelo/)).toBeInTheDocument();
  });

  it("incluye el enlace de vuelta al panel y el pie institucional", async () => {
    api();
    render(<CarbonPage />);
    expect(screen.getByRole("link", { name: "Tableros" })).toHaveAttribute("href", "/");
    expect(screen.getByText(/Fuente: modelo de carbón térmico/)).toBeInTheDocument();
  });
});

describe("SerieCarbonChart", () => {
  it("dibuja la historia sin el mes en curso, la banda P10-P90 y el techo y el record", async () => {
    api();
    render(<SerieCarbonChart historia={36} horizonte={9} unidad="gbtu" />);
    const grafico = await screen.findByTestId("composed-chart");
    expect(JSON.parse(grafico.dataset.points!)).toHaveLength(4);
    expect(screen.getAllByTestId("area").map((a) => a.dataset.name)).toContain("Escenarios P10–P90");
    const refs = screen.getAllByTestId("reference-line");
    expect(refs.map((r) => r.dataset.y)).toEqual(["400", "340"]);
    expect(refs[0].dataset.label).toBe("Techo 400,0");
    expect(refs[1].dataset.label).toBe("Récord 340,0");
  });

  it("explica que el mes en curso no se dibuja y da lo observado hasta hoy", async () => {
    api();
    render(<SerieCarbonChart historia={36} horizonte={9} unidad="gbtu" />);
    expect(await screen.findByText(/oct de 2026 está en curso: lo observado hasta hoy es 213,0 GBTU\/día/)).toBeInTheDocument();
  });

  it("sin mes parcial no muestra la nota", async () => {
    api({ [`${R}/serie`]: () => crearSerieCarbon({ proyeccion: crearSerieCarbon().proyeccion.map((p) => ({ ...p, observado_parcial_gbtu_dia: null })) }) });
    render(<SerieCarbonChart historia={36} horizonte={9} unidad="gbtu" />);
    await screen.findByTestId("composed-chart");
    expect(screen.queryByText(/está en curso/)).not.toBeInTheDocument();
  });

  it("mientras carga muestra un esqueleto", () => {
    simularFetch({ [`${R}/serie`]: () => new Promise(() => {}) });
    const { container } = render(<SerieCarbonChart historia={36} horizonte={9} unidad="gbtu" />);
    expect(container.querySelector(".skeleton")).toBeInTheDocument();
  });
});

describe("TrimestresChart", () => {
  it("atenua los trimestres parciales y rotula el numero de meses", async () => {
    api();
    render(<CarbonPage />);
    await screen.findByText(/Cumple 1 de 2/);
    const fila = screen.getByRole("row", { name: /T2 2027/ });
    expect(fila).toHaveTextContent("parcial (1 mes)");
    expect(screen.getByRole("row", { name: /T4 2026/ })).not.toHaveTextContent("parcial");
    const celdas = screen.getAllByTestId("cell").map((c) => c.dataset.fill);
    expect(celdas).toHaveLength(3);
  });
});

describe("ComparacionXmChart", () => {
  it("avisa los meses en que XM supera el techo", async () => {
    api();
    render(<ComparacionXmChart horizonte={9} unidad="gbtu" poderCalorifico={25} />);
    expect(await screen.findByText(/En 1 mes el caso estocástico de XM supera el techo físico/)).toBeInTheDocument();
  });

  it("no avisa cuando XM queda por debajo del techo", async () => {
    api({ [`${R}/comparacion-xm`]: () => crearComparacionXm(390) });
    render(<ComparacionXmChart horizonte={9} unidad="gbtu" poderCalorifico={25} />);
    await screen.findByTestId("composed-chart");
    expect(screen.queryByText(/supera el techo físico/)).not.toBeInTheDocument();
  });
});

describe("ValidacionCarbonPanel", () => {
  it("lista cada criterio con su estado accesible (Cumple / No cumple)", async () => {
    api();
    render(<ValidacionCarbonPanel />);
    await screen.findByText(/Cumple 1 de 2 criterios de validez/);
    expect(screen.getAllByRole("img", { name: "Cumple" })).toHaveLength(1);
    expect(screen.getAllByRole("img", { name: "No cumple" })).toHaveLength(1);
  });

  it("pone primero los criterios que no cumplen y deja los que cumplen en un desplegable cerrado", async () => {
    api();
    const { container } = render(<ValidacionCarbonPanel />);
    await screen.findByText(/Cumple 1 de 2 criterios/);
    expect(screen.getByText("1 criterio no cumple: son las limitaciones que hay que conocer.")).toBeInTheDocument();
    const detalle = container.querySelector("details")!;
    expect(detalle).not.toHaveAttribute("open");
    expect(within(detalle).getByText("Ver el criterio que cumple")).toBeInTheDocument();
    expect(within(detalle).getByText(/RESET de Ramsey/)).toBeInTheDocument();
    expect(within(detalle).queryByText(/Breusch-Pagan/)).not.toBeInTheDocument();
  });

  it("muestra los errores por horizonte y los episodios criticos", async () => {
    api();
    render(<ValidacionCarbonPanel />);
    const tabla = await screen.findByRole("region", { name: "Error por horizonte" });
    expect(within(tabla).getByText("45,8")).toBeInTheDocument();
    expect(within(tabla).getByText("3 meses")).toBeInTheDocument();
    const episodios = screen.getByRole("region", { name: "Episodios críticos" });
    expect(episodios).toHaveTextContent("El Niño 2023-24");
    expect(episodios).toHaveTextContent("83%");
  });
});
