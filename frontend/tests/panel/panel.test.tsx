import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PanelPage from "@/app/page";
import { TABLEROS } from "@/lib/tableros";

describe("Panel principal de tableros", () => {
  it("el primer tablero es embalses y el segundo carbon termico", () => {
    expect(TABLEROS.map((t) => [t.id, t.ruta])).toEqual([
      ["embalses", "/embalses"],
      ["carbon", "/carbon"],
    ]);
  });

  it("muestra un acceso por cada tablero registrado, en ese orden", () => {
    render(<PanelPage />);
    const accesos = within(screen.getByRole("region", { name: "Tableros disponibles" })).getAllByRole("link");
    expect(accesos.map((a) => a.getAttribute("href"))).toEqual(["/embalses", "/carbon"]);
    expect(within(accesos[0]).getByRole("heading", { name: "Embalses" })).toBeInTheDocument();
    expect(within(accesos[1]).getByRole("heading", { name: "Carbón térmico" })).toBeInTheDocument();
  });

  it("cada acceso tiene un nombre accesible claro", () => {
    render(<PanelPage />);
    expect(screen.getByRole("link", { name: "Abrir el tablero de Embalses" })).toHaveAttribute("href", "/embalses");
    expect(screen.getByRole("link", { name: "Abrir el tablero de Carbón térmico" })).toHaveAttribute("href", "/carbon");
  });

  it("cada tarjeta dice de donde salen sus datos y que incluye", () => {
    render(<PanelPage />);
    for (const t of TABLEROS) {
      const tarjeta = screen.getByRole("link", { name: `Abrir el tablero de ${t.titulo}` });
      expect(tarjeta).toHaveTextContent(t.fuente);
      expect(within(tarjeta).getAllByRole("listitem")).toHaveLength(t.incluye.length);
    }
  });

  it("tiene un unico titulo principal y el acceso a la guia, sin enlace circular a si mismo", () => {
    render(<PanelPage />);
    expect(screen.getAllByRole("heading", { level: 1 }).map((h) => h.textContent)).toEqual([
      "Plataforma de Tableros Analíticos",
      "Tableros",
    ].slice(0, 1).concat(["Tableros"]));
    expect(screen.getByRole("link", { name: "Información" })).toHaveAttribute("href", "/informacion");
    expect(screen.queryByRole("link", { name: "Tableros" })).not.toBeInTheDocument();
  });

  it("los tableros registrados tienen rutas y ids unicos", () => {
    expect(new Set(TABLEROS.map((t) => t.id)).size).toBe(TABLEROS.length);
    expect(new Set(TABLEROS.map((t) => t.ruta)).size).toBe(TABLEROS.length);
    expect(TABLEROS.every((t) => t.ruta.startsWith("/") && !t.ruta.endsWith("/"))).toBe(true);
  });
});
