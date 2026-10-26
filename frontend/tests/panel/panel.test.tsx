import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import PanelPage from "@/app/page";
import { RUTAS } from "@/lib/rutas";
import { GRUPOS, TABLEROS, tablerosDelGrupo } from "@/lib/tableros";

const grupo = (nombre: string) => screen.getByRole("list", { name: nombre });

describe("Registro de tableros", () => {
  it("el orden es embalses, carbon, demanda no atendida, gas, optimizacion y apagon", () => {
    expect(TABLEROS.map((t) => [t.id, t.ruta])).toEqual([
      ["embalses", "/embalses"],
      ["carbon", "/carbon"],
      ["dns", "/dns"],
      ["gas", "/gas"],
      ["optimizacion", "/optimizacion"],
      ["apagon", "/apagon"],
    ]);
  });

  it("las rutas salen del manejador central y las guias apuntan a un capitulo de /informacion", () => {
    for (const t of TABLEROS) {
      expect(t.ruta).toBe(RUTAS[t.id]);
      expect(t.guia).toMatch(/^\/informacion#[a-z-]+$/);
    }
  });

  it("ids y rutas son unicos, y cada ruta empieza con / y no termina con /", () => {
    expect(new Set(TABLEROS.map((t) => t.id)).size).toBe(TABLEROS.length);
    expect(new Set(TABLEROS.map((t) => t.ruta)).size).toBe(TABLEROS.length);
    expect(TABLEROS.every((t) => t.ruta.startsWith("/") && !t.ruta.endsWith("/"))).toBe(true);
  });

  it("tres tableros con datos y tres modelos en desarrollo", () => {
    expect(tablerosDelGrupo("datos").map((t) => t.id)).toEqual(["embalses", "carbon", "dns"]);
    expect(tablerosDelGrupo("desarrollo").map((t) => t.id)).toEqual(["gas", "optimizacion", "apagon"]);
  });

  it("cada tarjeta tiene tres etiquetas y una descripcion corta (una frase)", () => {
    for (const t of TABLEROS) {
      expect(t.incluye).toHaveLength(3);
      expect(t.descripcion.length).toBeLessThanOrEqual(160);
      expect(t.descripcion.endsWith(".")).toBe(true);
    }
  });
});

describe("Panel principal «Tableros Analíticos»", () => {
  it("tiene un unico h1 (el nombre del sistema) y los demas titulos son h2/h3", () => {
    render(<PanelPage />);
    expect(screen.getAllByRole("heading", { level: 1 }).map((h) => h.textContent)).toEqual(["Tableros Analíticos"]);
    expect(screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent)).toEqual([
      "Elige un tablero", GRUPOS.datos.titulo, GRUPOS.desarrollo.titulo,
    ]);
    expect(screen.getAllByRole("heading", { level: 3 })).toHaveLength(6);
  });

  it("separa los tableros con datos de los modelos en desarrollo, cada grupo con su explicacion", () => {
    render(<PanelPage />);
    expect(within(grupo(GRUPOS.datos.titulo)).getAllByRole("heading", { level: 3 }).map((h) => h.textContent)).toEqual([
      "Embalses", "Carbón térmico", "Demanda no atendida",
    ]);
    expect(within(grupo(GRUPOS.desarrollo.titulo)).getAllByRole("heading", { level: 3 }).map((h) => h.textContent)).toEqual([
      "Gas natural", "Optimización hidrotérmica", "Riesgo de apagón",
    ]);
    expect(screen.getByText(GRUPOS.desarrollo.descripcion)).toBeInTheDocument();
  });

  it("cada tablero tiene su acceso principal con nombre accesible y su ruta", () => {
    render(<PanelPage />);
    for (const t of TABLEROS) {
      expect(screen.getByRole("link", { name: `Abrir el tablero de ${t.titulo}` })).toHaveAttribute("href", t.ruta);
    }
  });

  it("cada tablero tiene ademas un acceso a su capitulo de la guia, fuera del enlace principal (sin enlaces anidados)", () => {
    const { container } = render(<PanelPage />);
    for (const t of TABLEROS) {
      expect(screen.getByRole("link", { name: `Guía del tablero de ${t.titulo}` })).toHaveAttribute("href", t.guia);
    }
    expect(container.querySelectorAll("a a")).toHaveLength(0);
  });

  it("solo los modelos en desarrollo llevan la marca «En desarrollo»", () => {
    render(<PanelPage />);
    for (const t of tablerosDelGrupo("desarrollo")) {
      expect(within(screen.getByRole("link", { name: `Abrir el tablero de ${t.titulo}` }).closest("article")!).getByText("En desarrollo")).toBeInTheDocument();
    }
    for (const t of tablerosDelGrupo("datos")) {
      expect(within(screen.getByRole("link", { name: `Abrir el tablero de ${t.titulo}` }).closest("article")!).queryByText("En desarrollo")).not.toBeInTheDocument();
    }
    expect(screen.getAllByText("En desarrollo")).toHaveLength(3);
  });

  it("cada tarjeta dice de donde salen sus datos y que se puede consultar", () => {
    render(<PanelPage />);
    for (const t of TABLEROS) {
      const tarjeta = screen.getByRole("link", { name: `Abrir el tablero de ${t.titulo}` }).closest("article")!;
      expect(tarjeta).toHaveTextContent(t.fuente);
      expect(within(tarjeta).getByRole("list", { name: "Qué puedes consultar" }).querySelectorAll("li")).toHaveLength(3);
    }
  });

  it("explica que los filtros quedan en la direccion y ofrece la guia, sin enlace circular al panel", () => {
    render(<PanelPage />);
    expect(screen.getByText(/Los filtros quedan en la dirección de la página/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir la guía técnica y el manual" })).toHaveAttribute("href", RUTAS.informacion);
    expect(screen.getByRole("link", { name: "Información" })).toHaveAttribute("href", RUTAS.informacion);
    expect(screen.queryByRole("link", { name: "Tableros" })).not.toBeInTheDocument();
  });
});
