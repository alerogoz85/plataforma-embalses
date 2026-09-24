import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SendaVolumenPanel } from "@/components/dashboard/SendaVolumenPanel";
import { EMBALSES_EJEMPLO, crearSenda } from "../fixtures";
import { simularFetch } from "../mocks/fetch";

vi.mock("recharts", () => import("../mocks/recharts"));

const RUTA = "/api/v1/senda-volumen";
const puntos = () => JSON.parse(screen.getByTestId("composed-chart").dataset.points!);

function montar(senda = crearSenda()) {
  const simulacion = simularFetch({ [RUTA]: (url) => ({ ...senda, embalse_id: url.searchParams.get("embalse")! }) });
  render(<SendaVolumenPanel embalses={EMBALSES_EJEMPLO} />);
  return simulacion;
}

async function esperarDatos() {
  await screen.findByTestId("composed-chart");
}

describe("SendaVolumenPanel", () => {
  it("pide por defecto el total nacional a 12 meses", async () => {
    const { llamadas } = montar();
    await esperarDatos();
    expect(llamadas[0].searchParams.get("embalse")).toBe("TOTAL");
    expect(llamadas[0].searchParams.get("horizonte_meses")).toBe("12");
  });

  it("muestra el nombre y el metodo del modelo", async () => {
    montar();
    expect(await screen.findByText("Total nacional · Holt-Winters estacional de prueba")).toBeInTheDocument();
  });

  it("muestra el ultimo observado y el minimo proyectado con su mes", async () => {
    montar();
    await esperarDatos();
    const observado = screen.getByText("Último observado").closest("div")!.parentElement!;
    expect(observado).toHaveTextContent("79.0%");
    expect(observado).toHaveTextContent("sept de 2026");
    const minimo = screen.getByText("Mínimo proyectado").closest("div")!.parentElement!;
    expect(minimo).toHaveTextContent("60.0%");
    expect(minimo).toHaveTextContent("abr de 2027");
  });

  describe("semaforo del minimo proyectado (rojo <55, ambar <65, verde >=65)", () => {
    it.each([
      [40, "var(--color-critico)"],
      [54.9, "var(--color-critico)"],
      [55, "var(--color-alerta)"],
      [64.9, "var(--color-alerta)"],
      [65, "var(--color-optimo)"],
      [90, "var(--color-optimo)"],
    ])("valor %s se pinta con %s", async (valor, color) => {
      montar(crearSenda({ minimo_proyectado: { mes: "2027-04", valor_esperado: valor, limite_inferior: 0, limite_superior: 100 } }));
      await esperarDatos();
      expect(screen.getByText(`${valor.toFixed(1)}%`, { selector: "p" })).toHaveStyle({ color });
    });

    it("explica los umbrales en pantalla", async () => {
      montar();
      await esperarDatos();
      expect(screen.getByText(/rojo <55% · ámbar <65% · verde ≥65%/)).toBeInTheDocument();
    });
  });

  describe("datos del grafico", () => {
    it("une historico y proyeccion con un punto puente", async () => {
      montar();
      await esperarDatos();
      const datos = puntos();
      expect(datos).toHaveLength(5); // 2 historicos + puente + 2 proyectados
      expect(datos[2]).toMatchObject({ observado: 79, proyeccion: 79, bandaBase: 79, bandaRango: 0 });
      expect(datos[3]).toMatchObject({ proyeccion: 78, bandaBase: 70, bandaRango: 16 });
      expect(datos[3].observado).toBeUndefined();
    });

    it("etiqueta los meses en espanol", async () => {
      montar();
      await esperarDatos();
      expect(puntos()[0].mesLabel).toBe("jul de 2026");
    });

    it("sin proyeccion muestra solo el historico", async () => {
      montar(crearSenda({ proyeccion: [] }));
      await esperarDatos();
      expect(puntos()).toHaveLength(3);
      expect(puntos().every((p: { proyeccion?: number }) => p.proyeccion === undefined)).toBe(true);
    });

    it("el eje Y crece si un embalse supera el 100% (no recorta la serie)", async () => {
      montar();
      await esperarDatos();
      const eje = screen.getByTestId("y-axis");
      expect(eje.dataset.maxBajo).toBe("100");
      expect(eje.dataset.maxAlto).toBe("131");
    });
  });

  describe("validacion walk-forward", () => {
    it("lista cada modelo con MAE y R2 a tres decimales", async () => {
      montar();
      await esperarDatos();
      const filas = screen.getAllByRole("row").slice(1);
      expect(filas).toHaveLength(2);
      expect(filas[0]).toHaveTextContent("Persistencia (ultimo valor)");
      expect(filas[0]).toHaveTextContent("3.570");
      expect(filas[0]).toHaveTextContent("0.537");
      expect(filas[1]).toHaveTextContent("2.217");
      expect(filas[1]).toHaveTextContent("0.828");
    });

    it("advierte con honestidad que la senda no es un pronostico puntual superior", async () => {
      montar();
      await esperarDatos();
      expect(screen.getByText(/Nota de honestidad/)).toBeInTheDocument();
      expect(screen.getByText(/forma estacional esperada/)).toBeInTheDocument();
    });

    it("cada encabezado de la tabla tiene su ayuda", async () => {
      montar();
      await esperarDatos();
      for (const nombre of ["Modelo", "MAE", "R²"]) {
        await userEvent.click(screen.getByRole("button", { name: `Ayuda: ${nombre}` }));
        expect(screen.getByRole("note")).toHaveTextContent(nombre);
      }
    });
  });

  describe("selectores", () => {
    it("ofrece 'Total nacional' y los embalses recibidos", async () => {
      montar();
      await esperarDatos();
      const opciones = within(screen.getByRole("combobox")).getAllByRole("option").map((o) => o.textContent);
      expect(opciones).toEqual(["Total nacional", "Guavio", "Prado", "Muna", "Agregado Bogotá"]);
    });

    it("cambiar de embalse vuelve a consultar con su id", async () => {
      const { llamadas } = montar();
      await esperarDatos();
      await userEvent.selectOptions(screen.getByRole("combobox"), "Prado");
      await waitFor(() => expect(llamadas.at(-1)!.searchParams.get("embalse")).toBe("PRADO"));
      expect(llamadas.at(-1)!.searchParams.get("horizonte_meses")).toBe("12");
    });

    it("cambiar el horizonte consulta con esos meses y marca el boton", async () => {
      const { llamadas } = montar();
      await esperarDatos();
      await userEvent.click(screen.getByRole("button", { name: "3m" }));
      await waitFor(() => expect(llamadas.at(-1)!.searchParams.get("horizonte_meses")).toBe("3"));
      expect(screen.getByRole("button", { name: "3m" })).toHaveStyle({ backgroundColor: "var(--color-marca)" });
      expect(screen.getByRole("button", { name: "12m" })).not.toHaveStyle({ backgroundColor: "var(--color-marca)" });
    });

    it("ofrece exactamente los horizontes 1, 3, 6 y 12 meses", async () => {
      montar();
      await esperarDatos();
      for (const h of ["1m", "3m", "6m", "12m"]) expect(screen.getByRole("button", { name: h })).toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "24m" })).not.toBeInTheDocument();
    });
  });

  describe("estados", () => {
    it("muestra un esqueleto mientras carga", () => {
      simularFetch({ [RUTA]: () => new Promise(() => {}) });
      const { container } = render(<SendaVolumenPanel embalses={EMBALSES_EJEMPLO} />);
      expect(container.querySelector(".skeleton")).toBeInTheDocument();
      expect(screen.queryByTestId("composed-chart")).not.toBeInTheDocument();
    });

    it("muestra el error de la API (p. ej. historia insuficiente)", async () => {
      simularFetch({ [RUTA]: () => ({ status: 422, cuerpo: { detalle: "requiere al menos 9 registros" } }) });
      render(<SendaVolumenPanel embalses={EMBALSES_EJEMPLO} />);
      expect(await screen.findByText(/No fue posible cargar la senda/)).toHaveTextContent("requiere al menos 9 registros");
      expect(screen.queryByTestId("composed-chart")).not.toBeInTheDocument();
    });
  });

  describe("proyeccion del modelo de Outputs", () => {
    const outputs = () =>
      crearSenda({
        metodo: "Prophet + XGBoost con escenarios ENSO de prueba",
        origen_proyeccion: "outputs",
        horizonte_efectivo_meses: 12,
        validacion: [],
      });

    it("nombra la banda como escenarios P10-P90 y no como intervalo de confianza", async () => {
      montar(outputs());
      await esperarDatos();
      const nombres = screen.getAllByTestId("area").map((a) => a.dataset.name);
      expect(nombres).toContain("Escenarios P10–P90 (ENSO)");
      expect(nombres).not.toContain("Intervalo de confianza 95%");
    });

    it("con el respaldo Holt-Winters mantiene el intervalo de confianza 95%", async () => {
      montar();
      await esperarDatos();
      expect(screen.getAllByTestId("area").map((a) => a.dataset.name)).toContain("Intervalo de confianza 95%");
    });

    it("muestra el metodo publicado y una nota en lugar de la tabla walk-forward", async () => {
      montar(outputs());
      expect(await screen.findByText(/Prophet \+ XGBoost con escenarios ENSO de prueba/)).toBeInTheDocument();
      expect(screen.getByText(/Sobre esta proyección/)).toBeInTheDocument();
      expect(screen.getByText(/no incluyen validación fuera de muestra/)).toBeInTheDocument();
      expect(screen.queryByRole("table")).not.toBeInTheDocument();
      expect(screen.queryByText(/Nota de honestidad/)).not.toBeInTheDocument();
    });

    it("avisa cuando se piden mas meses de los que publica la corrida del modelo", async () => {
      montar({ ...outputs(), horizonte_efectivo_meses: 6 });
      expect(await screen.findByText(/El modelo publica 6 meses de proyección: se muestran 6 aunque se pidieron 12/)).toBeInTheDocument();
    });

    it("no avisa cuando la corrida cubre lo pedido", async () => {
      montar(outputs());
      await esperarDatos();
      expect(screen.queryByText(/El modelo publica/)).not.toBeInTheDocument();
    });

    it("el respaldo no muestra el aviso de horizonte cuando cubre lo pedido", async () => {
      montar(crearSenda({ horizonte_efectivo_meses: 12 }));
      await esperarDatos();
      expect(screen.queryByText(/El modelo publica/)).not.toBeInTheDocument();
    });
  });
});
