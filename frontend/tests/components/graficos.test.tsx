import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { MainChart } from "@/components/dashboard/MainChart";
import { RegionBarChart } from "@/components/dashboard/RegionBarChart";
import { REGIONES_EJEMPLO, crearDetalle, crearPrediccion } from "../fixtures";
import { simularFetch } from "../mocks/fetch";

vi.mock("recharts", () => import("../mocks/recharts"));

const puntos = (id: string) => JSON.parse(screen.getByTestId(id).dataset.points!);

describe("RegionBarChart", () => {
  it("ordena las regiones de menor a mayor %V. util", () => {
    render(<RegionBarChart regiones={REGIONES_EJEMPLO} cargando={false} />);
    expect(puntos("bar-chart").map((r: { region: string }) => r.region)).toEqual(["Caldas", "Centro", "Oriente"]);
  });

  it("no modifica el arreglo recibido al ordenarlo", () => {
    const original = [...REGIONES_EJEMPLO];
    render(<RegionBarChart regiones={REGIONES_EJEMPLO} cargando={false} />);
    expect(REGIONES_EJEMPLO).toEqual(original);
  });

  it("colorea cada barra segun el riesgo de su region", () => {
    render(<RegionBarChart regiones={REGIONES_EJEMPLO} cargando={false} />);
    const colores = screen.getAllByTestId("cell").map((c) => c.dataset.fill);
    expect(colores).toEqual(["var(--color-critico)", "var(--color-optimo)", "var(--color-reboce)"]);
  });

  it("el eje se ajusta si una region supera el 100% (no recorta barras)", () => {
    render(<RegionBarChart regiones={REGIONES_EJEMPLO} cargando={false} />);
    const eje = screen.getByTestId("x-axis");
    expect(eje.dataset.maxBajo).toBe("100");
    expect(eje.dataset.maxAlto).toBe("131");
  });

  it("muestra un esqueleto mientras carga sin datos", () => {
    const { container } = render(<RegionBarChart regiones={[]} cargando />);
    expect(screen.queryByTestId("bar-chart")).not.toBeInTheDocument();
    expect(container.querySelector(".skeleton")).toBeInTheDocument();
  });

  it("con datos ya cargados no vuelve al esqueleto al recargar", () => {
    render(<RegionBarChart regiones={REGIONES_EJEMPLO} cargando />);
    expect(screen.getByTestId("bar-chart")).toBeInTheDocument();
  });

  it("tiene titulo y ayuda", async () => {
    render(<RegionBarChart regiones={REGIONES_EJEMPLO} cargando={false} />);
    expect(screen.getByRole("heading", { name: /Distribución regional/ })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Ayuda: Distribución regional/ }));
    expect(screen.getByRole("note")).toHaveTextContent("Caldas");
  });
});

function rutasMainChart(opciones: { prediccion?: () => unknown; detalle?: () => unknown } = {}) {
  return simularFetch({
    "/api/v1/embalses/GUAVIO": opciones.detalle ?? (() => crearDetalle(5)),
    "/api/v1/embalses/GUAVIO/prediccion": opciones.prediccion ?? (() => crearPrediccion(3)),
  });
}

function montarChart(props: Partial<React.ComponentProps<typeof MainChart>> = {}) {
  return render(
    <MainChart embalseId="GUAVIO" nombreEmbalse="Guavio" fechaInicio="2026-03-27" fechaFin="2026-09-23" {...props} />,
  );
}

describe("MainChart", () => {
  it("sin embalse pide seleccionar uno y no consulta la API", () => {
    const { fetch } = rutasMainChart();
    montarChart({ embalseId: null });
    expect(screen.getByText(/Selecciona un embalse/)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it("muestra un esqueleto mientras carga", () => {
    rutasMainChart();
    const { container } = montarChart();
    expect(container.querySelector(".skeleton")).toBeInTheDocument();
  });

  it("consulta el detalle con el rango elegido y la prediccion a 30 dias", async () => {
    const { llamadas } = rutasMainChart();
    montarChart();
    await screen.findByTestId("composed-chart");
    const detalle = llamadas.find((u) => u.pathname === "/api/v1/embalses/GUAVIO")!;
    expect(detalle.searchParams.get("fecha_inicio")).toBe("2026-03-27");
    expect(detalle.searchParams.get("fecha_fin")).toBe("2026-09-23");
    const prediccion = llamadas.find((u) => u.pathname.endsWith("/prediccion"))!;
    expect(prediccion.searchParams.get("horizonte")).toBe("30");
  });

  it("une la serie historica y la proyeccion con un punto puente", async () => {
    rutasMainChart();
    montarChart();
    await waitFor(() => expect(puntos("composed-chart")).toHaveLength(8));
    const datos = puntos("composed-chart");

    // 4 historicos + puente (ultimo historico) + 3 proyectados.
    expect(datos.slice(0, 4).every((p: { prediccion?: number }) => p.prediccion === undefined)).toBe(true);
    const puente = datos[4];
    expect(puente.pctVolumenUtil).toBe(94);
    expect(puente.prediccion).toBe(94);
    expect(puente.bandaBase).toBe(94);
    expect(puente.bandaRango).toBe(0);

    const primeraProyeccion = datos[5];
    expect(primeraProyeccion.pctVolumenUtil).toBeUndefined();
    expect(primeraProyeccion.prediccion).toBe(90);
    expect(primeraProyeccion.bandaBase).toBe(85);
    expect(primeraProyeccion.bandaRango).toBe(10); // 95 - 85
  });

  it("conserva los huecos de aportes (null) en lugar de convertirlos en ceros", async () => {
    rutasMainChart();
    montarChart();
    await waitFor(() => expect(puntos("composed-chart").length).toBeGreaterThan(0));
    const aportes = puntos("composed-chart").slice(0, 4).map((p: { aportesPctMedia: number | null }) => p.aportesPctMedia);
    expect(aportes).toEqual([50, null, 50, null]);
  });

  it("etiqueta las fechas en formato corto", async () => {
    rutasMainChart();
    montarChart();
    await waitFor(() => expect(puntos("composed-chart").length).toBeGreaterThan(0));
    expect(puntos("composed-chart")[0].fechaLabel).toBe("18 de sept");
  });

  it("dibuja las tres series y solo la proyeccion va punteada", async () => {
    rutasMainChart();
    montarChart();
    await screen.findByTestId("composed-chart");
    const lineas = screen.getAllByTestId("line");
    expect(lineas.map((l) => l.dataset.name)).toEqual([
      "% Volumen útil",
      "Aportes (% media histórica)",
      "Proyección %V. útil",
    ]);
    expect(lineas.map((l) => l.dataset.dashed)).toEqual(["false", "false", "true"]);
    const areas = screen.getAllByTestId("area");
    expect(areas.map((a) => a.dataset.stack)).toEqual(["banda", "banda"]);
  });

  it("muestra el metodo y el nivel de confianza del pronostico", async () => {
    rutasMainChart();
    montarChart();
    expect(await screen.findByText(/Holt-Winters de prueba · IC 95%/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Guavio — %V\. útil vs\. aportes/ })).toBeInTheDocument();
  });

  describe("proyeccion del modelo de Outputs", () => {
    const outputs = () =>
      crearPrediccion(3, {
        origen: "outputs",
        nivel_confianza: null,
        metodo: "Prophet + XGBoost de prueba · interpolación diaria",
      });

    it("la subtitula como escenarios P10-P90 y no como intervalo de confianza", async () => {
      rutasMainChart({ prediccion: outputs });
      montarChart();
      expect(await screen.findByText("Prophet + XGBoost de prueba · interpolación diaria · escenarios P10–P90")).toBeInTheDocument();
      expect(screen.queryByText(/IC \d+%/)).not.toBeInTheDocument();
    });

    it("nombra la banda como escenarios y no como intervalo de confianza 95%", async () => {
      rutasMainChart({ prediccion: outputs });
      montarChart();
      await screen.findByTestId("composed-chart");
      await waitFor(() =>
        expect(screen.getAllByTestId("area").map((a) => a.dataset.name)).toContain("Escenarios P10–P90 (ENSO)"),
      );
      expect(screen.getAllByTestId("area").map((a) => a.dataset.name)).not.toContain("Intervalo de confianza 95%");
    });

    it("con el respaldo Holt-Winters mantiene el intervalo de confianza 95%", async () => {
      rutasMainChart();
      montarChart();
      await screen.findByTestId("composed-chart");
      expect(screen.getAllByTestId("area").map((a) => a.dataset.name)).toContain("Intervalo de confianza 95%");
    });

    it("ofrece los horizontes 1, 3, 6 y 12 meses", async () => {
      rutasMainChart();
      montarChart();
      await screen.findByTestId("composed-chart");
      for (const h of ["1m", "3m", "6m", "12m"]) expect(screen.getByRole("button", { name: h })).toBeInTheDocument();
      await userEvent.click(screen.getByRole("button", { name: "12m" }));
      await waitFor(() => expect(screen.getByRole("button", { name: "12m" })).toHaveStyle({ backgroundColor: "var(--color-marca)" }));
    });
  });

  it("cambiar el horizonte vuelve a pedir la prediccion y marca el boton", async () => {
    const { llamadas } = rutasMainChart();
    montarChart();
    await screen.findByTestId("composed-chart");

    await userEvent.click(screen.getByRole("button", { name: "3m" }));

    await waitFor(() =>
      expect(llamadas.some((u) => u.pathname.endsWith("/prediccion") && u.searchParams.get("horizonte") === "90")).toBe(true),
    );
    expect(screen.getByRole("button", { name: "3m" })).toHaveStyle({ backgroundColor: "var(--color-marca)" });
    expect(screen.getByRole("button", { name: "1m" })).not.toHaveStyle({ backgroundColor: "var(--color-marca)" });
  });

  it("si falla la prediccion igual muestra la serie historica", async () => {
    rutasMainChart({ prediccion: () => ({ status: 500, cuerpo: { detalle: "modelo caido" } }) });
    montarChart();
    await waitFor(() => expect(puntos("composed-chart")).toHaveLength(5));
    expect(screen.getByText("Cargando modelo de pronóstico…")).toBeInTheDocument();
  });

  it("si falla la serie historica muestra el error de la API", async () => {
    rutasMainChart({ detalle: () => ({ status: 404, cuerpo: { detalle: "No existe un embalse con identificador 'GUAVIO'" } }) });
    montarChart();
    expect(await screen.findByText(/No fue posible cargar la serie histórica/)).toHaveTextContent("No existe un embalse");
    expect(screen.queryByTestId("composed-chart")).not.toBeInTheDocument();
  });

  it("tiene ayuda para el grafico y para el horizonte", async () => {
    rutasMainChart();
    montarChart();
    await screen.findByTestId("composed-chart");
    await userEvent.click(screen.getByRole("button", { name: "Ayuda: Horizonte del pronóstico" }));
    expect(within(screen.getByRole("note")).getByText(/1, 3, 6 o 12/)).toBeInTheDocument();
  });
});
