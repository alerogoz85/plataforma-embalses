import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Header } from "@/components/layout/Header";

describe("Header", () => {
  it("ofrece el acceso «Información» a la guia, en una pestana nueva", () => {
    render(<Header fechaCorte="22 de sept de 2026" />);
    const enlace = screen.getByRole("link", { name: "Información" });
    expect(enlace).toHaveAttribute("href", "/informacion");
    expect(enlace).toHaveAttribute("target", "_blank");
    expect(enlace.getAttribute("rel")).toContain("noopener");
  });

  it("agrupa los accesos antes del boton de tema: Tableros, Información y tema", () => {
    render(<Header />);
    const grupo = screen.getByRole("link", { name: "Información" }).parentElement!;
    expect(within(grupo).getByRole("button", { name: /Cambiar a modo/ })).toBeInTheDocument();
    expect([...grupo.children].map((el) => el.tagName)).toEqual(["A", "A", "BUTTON"]);
  });

  it("el enlace «Tableros» vuelve al panel principal en la misma pestana", () => {
    render(<Header />);
    const enlace = screen.getByRole("link", { name: "Tableros" });
    expect(enlace).toHaveAttribute("href", "/");
    expect(enlace).not.toHaveAttribute("target");
  });

  it("en el propio panel no se muestra el enlace «Tableros»", () => {
    render(<Header enlacePanel={false} />);
    expect(screen.queryByRole("link", { name: "Tableros" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Información" })).toBeInTheDocument();
  });

  it("muestra la fecha de corte o avisa que esta cargando", () => {
    const { rerender } = render(<Header />);
    expect(screen.getByText(/Cargando corte de información/)).toBeInTheDocument();
    rerender(<Header fechaCorte="22 de sept de 2026" />);
    expect(screen.getByText("Corte al 22 de sept de 2026")).toBeInTheDocument();
  });

  it("acepta otro titulo y subtitulo (otros tableros); el subtitulo gana sobre la fecha de corte", () => {
    render(<Header titulo="Modelo de carbón térmico" subtitulo="Proyección oct-2026 a jun-2027" fechaCorte="x" />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Modelo de carbón térmico");
    expect(screen.getByText("Proyección oct-2026 a jun-2027")).toBeInTheDocument();
    expect(screen.queryByText(/Corte al/)).not.toBeInTheDocument();
  });

  it("por defecto conserva el titulo del tablero de embalses", () => {
    render(<Header />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent("Monitoreo y predicción de embalses");
  });
});
