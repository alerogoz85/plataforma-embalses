import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import NoEncontrada from "@/app/not-found";
import { CargandoTablero } from "@/components/ui/CargandoTablero";
import { RUTAS } from "@/lib/rutas";
import { TABLEROS } from "@/lib/tableros";

describe("Pagina 404", () => {
  it("explica el error con un unico h1 (el sistema) y un titulo claro", () => {
    render(<NoEncontrada />);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByRole("heading", { level: 2, name: "No encontramos esa página" })).toBeInTheDocument();
    expect(screen.getByText("Error 404")).toBeInTheDocument();
  });

  it("ofrece volver al panel y lista todos los tableros del registro con su ruta", () => {
    render(<NoEncontrada />);
    const nav = screen.getByRole("navigation", { name: "Tableros disponibles" });
    expect(within(nav).getByRole("link", { name: "Ir al panel de tableros" })).toHaveAttribute("href", RUTAS.panel);
    for (const t of TABLEROS) expect(within(nav).getByRole("link", { name: t.titulo })).toHaveAttribute("href", t.ruta);
  });
});

describe("CargandoTablero (fallback mientras se lee la URL)", () => {
  it("muestra el titulo del tablero, el encabezado y esqueletos marcados como ocupados", () => {
    const { container } = render(<CargandoTablero titulo="Demanda no atendida (DNS)" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Demanda no atendida (DNS)");
    expect(container.querySelector("[aria-busy='true']")).toBeInTheDocument();
    expect(container.querySelectorAll(".skeleton").length).toBeGreaterThan(0);
  });
});
