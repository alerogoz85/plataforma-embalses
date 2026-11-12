import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { BarraCelda } from "@/components/ui/BarraCelda";
import { BarraFiltrosActivos } from "@/components/ui/BarraFiltrosActivos";
import { RangosRapidos } from "@/components/ui/RangosRapidos";
import { ChipFiltro } from "@/components/ui/ChipFiltro";
import { EstadoVacio } from "@/components/ui/EstadoVacio";
import { Sparkline } from "@/components/ui/Sparkline";

vi.mock("recharts", () => import("../mocks/recharts"));

describe("Sparkline", () => {
  it("dibuja la serie y la describe para lectores de pantalla", () => {
    render(<Sparkline datos={[10, 12, 15]} etiqueta="Volumen util" />);
    expect(screen.getByRole("img", { name: "Volumen util: de 10 a 15" })).toBeInTheDocument();
    expect(JSON.parse(screen.getByTestId("area-chart").dataset.points ?? "[]")).toEqual([
      { i: 0, v: 10 },
      { i: 1, v: 12 },
      { i: 2, v: 15 },
    ]);
  });

  it("omite los valores no numericos", () => {
    render(<Sparkline datos={[1, Number.NaN, 3]} etiqueta="x" />);
    expect(JSON.parse(screen.getByTestId("area-chart").dataset.points ?? "[]")).toHaveLength(2);
  });

  it("no dibuja nada con menos de dos puntos", () => {
    const { container } = render(<Sparkline datos={[5]} etiqueta="x" />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("EstadoVacio", () => {
  it("anuncia el estado y ofrece la accion de salida", async () => {
    const restablecer = vi.fn();
    render(
      <EstadoVacio titulo="No hay datos para estos filtros" descripcion="Prueba con otro rango." accion={{ texto: "Restablecer filtros", onClick: restablecer }} />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("No hay datos para estos filtros");
    expect(screen.getByText("Prueba con otro rango.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Restablecer filtros" }));
    expect(restablecer).toHaveBeenCalledOnce();
  });

  it("sin accion ni descripcion solo muestra el titulo", () => {
    render(<EstadoVacio titulo="Sin datos" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});

describe("ChipFiltro", () => {
  it("quita el filtro con un clic y se nombra de forma accesible", async () => {
    const quitar = vi.fn();
    render(<ChipFiltro etiqueta="Caribe" onQuitar={quitar} />);
    await userEvent.click(screen.getByRole("button", { name: "Quitar filtro: Caribe" }));
    expect(quitar).toHaveBeenCalledOnce();
  });
});

describe("BarraCelda", () => {
  it("expone el valor como barra de progreso y lo escribe junto a la barra", () => {
    render(<BarraCelda valor={74.3} etiqueta="Volumen util" />);
    const barra = screen.getByRole("progressbar", { name: "Volumen util" });
    expect(barra).toHaveAttribute("aria-valuenow", "74.3");
    expect(barra).toHaveAttribute("aria-valuemax", "100");
    expect(screen.getByText("74,3 %")).toBeInTheDocument();
  });

  it("acota la barra entre 0 y el maximo", () => {
    render(<BarraCelda valor={140} etiqueta="Uso" />);
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "100");
    expect((screen.getByRole("progressbar").firstElementChild as HTMLElement).style.width).toBe("100%");
  });

  it("acepta otro maximo y un formato propio", () => {
    render(<BarraCelda valor={50} maximo={200} etiqueta="Caudal" formato={(v) => `${v} m³/s`} />);
    expect((screen.getByRole("progressbar").firstElementChild as HTMLElement).style.width).toBe("25%");
    expect(screen.getByText("50 m³/s")).toBeInTheDocument();
  });

  it("muestra una raya cuando no hay valor", () => {
    render(<BarraCelda valor={null} etiqueta="x" />);
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("BarraFiltrosActivos", () => {
  it("sin filtros activos no dibuja nada", () => {
    const { container } = render(<BarraFiltrosActivos filtros={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("muestra un chip por filtro y cada uno se quita por separado", async () => {
    const quitarA = vi.fn();
    const quitarB = vi.fn();
    render(
      <BarraFiltrosActivos
        filtros={[
          { id: "a", etiqueta: "Región Centro", onQuitar: quitarA },
          { id: "b", etiqueta: "Origen Programada", onQuitar: quitarB },
        ]}
      />,
    );
    expect(screen.getByRole("group", { name: "Filtros activos" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Quitar filtro: Origen Programada" }));
    expect(quitarB).toHaveBeenCalledOnce();
    expect(quitarA).not.toHaveBeenCalled();
  });
});

describe("RangosRapidos", () => {
  const opciones = [
    { valor: 30, etiqueta: "30 días" },
    { valor: 90, etiqueta: "90 días" },
  ] as const;

  it("marca como activa solo la opcion vigente", () => {
    render(<RangosRapidos etiqueta="Rango" opciones={opciones} valor={90} onCambiar={() => {}} />);
    expect(screen.getByRole("radiogroup", { name: "Rango" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "90 días" })).toHaveAttribute("aria-checked", "true");
    expect(screen.getByRole("radio", { name: "30 días" })).toHaveAttribute("aria-checked", "false");
  });

  it("sin coincidencia no marca ninguna", () => {
    render(<RangosRapidos etiqueta="Rango" opciones={opciones} valor={null} onCambiar={() => {}} />);
    expect(screen.getAllByRole("radio").every((r) => r.getAttribute("aria-checked") === "false")).toBe(true);
  });

  it("un clic entrega el valor de la opcion", async () => {
    const cambiar = vi.fn();
    render(<RangosRapidos etiqueta="Rango" opciones={opciones} valor={90} onCambiar={cambiar} />);
    await userEvent.click(screen.getByRole("radio", { name: "30 días" }));
    expect(cambiar).toHaveBeenCalledWith(30);
  });
});
