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

  it("el acceso queda al lado del boton de tema, en el mismo grupo", () => {
    render(<Header />);
    const grupo = screen.getByRole("link", { name: "Información" }).parentElement!;
    expect(within(grupo).getByRole("button", { name: /Cambiar a modo/ })).toBeInTheDocument();
    // el enlace va antes del boton de tema
    const orden = [...grupo.children].map((el) => el.tagName);
    expect(orden).toEqual(["A", "BUTTON"]);
  });

  it("muestra la fecha de corte o avisa que esta cargando", () => {
    const { rerender } = render(<Header />);
    expect(screen.getByText(/Cargando corte de información/)).toBeInTheDocument();
    rerender(<Header fechaCorte="22 de sept de 2026" />);
    expect(screen.getByText("Corte al 22 de sept de 2026")).toBeInTheDocument();
  });
});
