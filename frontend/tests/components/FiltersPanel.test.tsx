import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { FiltersPanel } from "@/components/dashboard/FiltersPanel";
import { REGIONES } from "@/lib/api/types";
import { EMBALSES_EJEMPLO } from "../fixtures";

function montar(props: Partial<React.ComponentProps<typeof FiltersPanel>> = {}) {
  const manejadores = {
    onCambiarRegion: vi.fn(),
    onCambiarEmbalse: vi.fn(),
    onRestablecer: vi.fn(),
    onCambiarFechaInicio: vi.fn(),
    onCambiarFechaFin: vi.fn(),
  };
  render(
    <FiltersPanel
      regionSeleccionada={null}
      embalseSeleccionado="GUAVIO"
      fechaInicio="2026-03-27"
      fechaFin="2026-09-23"
      embalsesDisponibles={EMBALSES_EJEMPLO}
      {...manejadores}
      {...props}
    />,
  );
  return manejadores;
}

const region = () => screen.getByRole("combobox", { name: /Región/ });
const embalse = () => screen.getByRole("combobox", { name: /Embalse/ });

describe("FiltersPanel", () => {
  it("ofrece las seis regiones hidrologicas de XM, incluida Caldas", () => {
    montar();
    const opciones = within(region()).getAllByRole("option").map((o) => o.textContent);
    expect(opciones).toEqual(["Todas las regiones", ...REGIONES]);
    expect(opciones).toContain("Caldas");
  });

  it("lista todos los embalses cuando no hay region", () => {
    montar();
    const nombres = within(embalse()).getAllByRole("option").map((o) => o.textContent);
    expect(nombres).toEqual(["Todos los embalses", "Guavio", "Prado", "Muna", "Agregado Bogotá"]);
  });

  it("solo lista los embalses de la region elegida", () => {
    montar({ regionSeleccionada: "Centro", embalseSeleccionado: "PRADO" });
    const nombres = within(embalse()).getAllByRole("option").map((o) => o.textContent);
    expect(nombres).toEqual(["Todos los embalses", "Prado", "Muna", "Agregado Bogotá"]);
  });

  it("al elegir una region solo informa la region (la pagina decide el embalse)", async () => {
    const m = montar();
    await userEvent.selectOptions(region(), "Centro");
    expect(m.onCambiarRegion).toHaveBeenCalledWith("Centro");
    expect(m.onCambiarEmbalse).not.toHaveBeenCalled();
  });

  it("el boton 'Restablecer filtros' avisa a la pagina sin tocar cada filtro", async () => {
    const m = montar();
    await userEvent.click(screen.getByRole("button", { name: "Restablecer filtros" }));
    expect(m.onRestablecer).toHaveBeenCalledTimes(1);
    expect(m.onCambiarRegion).not.toHaveBeenCalled();
    expect(m.onCambiarEmbalse).not.toHaveBeenCalled();
  });

  it("volver a 'Todas las regiones' informa null, no una cadena vacia", async () => {
    const m = montar({ regionSeleccionada: "Centro", embalseSeleccionado: "PRADO" });
    await userEvent.selectOptions(region(), "Todas las regiones");
    expect(m.onCambiarRegion).toHaveBeenCalledWith(null);
  });

  it("al elegir un embalse informa su id", async () => {
    const m = montar();
    await userEvent.selectOptions(embalse(), "Prado");
    expect(m.onCambiarEmbalse).toHaveBeenCalledWith("PRADO");
    expect(m.onCambiarRegion).not.toHaveBeenCalled();
  });

  it("refleja la seleccion actual", () => {
    montar({ regionSeleccionada: "Centro", embalseSeleccionado: "MUNA" });
    expect(region()).toHaveValue("Centro");
    expect(embalse()).toHaveValue("MUNA");
  });

  it("las fechas muestran su valor y se limitan entre si", () => {
    montar();
    const desde = screen.getByLabelText("Desde", { selector: "input" });
    const hasta = screen.getByLabelText("Hasta", { selector: "input" });
    expect(desde).toHaveValue("2026-03-27");
    expect(hasta).toHaveValue("2026-09-23");
    expect(desde).toHaveAttribute("max", "2026-09-23");
    expect(hasta).toHaveAttribute("min", "2026-03-27");
  });

  it("informa los cambios de fecha", () => {
    const m = montar();
    const desde = screen.getByLabelText("Desde", { selector: "input" });
    const hasta = screen.getByLabelText("Hasta", { selector: "input" });
    // fireEvent porque userEvent.type no es fiable en <input type="date"> de jsdom.
    return import("@testing-library/react").then(({ fireEvent }) => {
      fireEvent.change(desde, { target: { value: "2026-04-01" } });
      fireEvent.change(hasta, { target: { value: "2026-09-01" } });
      expect(m.onCambiarFechaInicio).toHaveBeenCalledWith("2026-04-01");
      expect(m.onCambiarFechaFin).toHaveBeenCalledWith("2026-09-01");
    });
  });

  it("cada filtro tiene su boton de ayuda y abrirlo no cambia el filtro", async () => {
    const m = montar();
    for (const titulo of ["Filtro de región", "Filtro de embalse", "Fecha inicial", "Fecha final"]) {
      await userEvent.click(screen.getByRole("button", { name: `Ayuda: ${titulo}` }));
      expect(screen.getByRole("note")).toHaveTextContent(titulo);
    }
    expect(m.onCambiarRegion).not.toHaveBeenCalled();
    expect(m.onCambiarEmbalse).not.toHaveBeenCalled();
  });
});
