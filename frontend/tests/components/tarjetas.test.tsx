import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { KpiCard } from "@/components/dashboard/KpiCard";
import { RiskBadge } from "@/components/dashboard/RiskBadge";
import { SistemaRiesgoCard } from "@/components/dashboard/SistemaRiesgoCard";
import type { NivelRiesgo } from "@/lib/api/types";

describe("KpiCard", () => {
  it("muestra etiqueta y valor", () => {
    render(<KpiCard etiqueta="Capacidad guardada" valor="13.553 GWh" />);
    expect(screen.getByText("Capacidad guardada")).toBeInTheDocument();
    expect(screen.getByText("13.553 GWh")).toBeInTheDocument();
  });

  it("colorea el delta segun su signo", () => {
    const { rerender } = render(
      <KpiCard etiqueta="x" valor="1" delta={{ texto: "+0.06 p.p.", positivo: true }} />,
    );
    expect(screen.getByText("+0.06 p.p.")).toHaveStyle({ color: "var(--color-optimo)" });
    rerender(<KpiCard etiqueta="x" valor="1" delta={{ texto: "-1.47 p.p.", positivo: false }} />);
    expect(screen.getByText("-1.47 p.p.")).toHaveStyle({ color: "var(--color-critico)" });
  });

  it("no muestra delta si no se entrega", () => {
    render(<KpiCard etiqueta="x" valor="1" delta={null} />);
    expect(screen.queryByText(/p\.p\./)).not.toBeInTheDocument();
  });

  it("solo muestra el boton de ayuda si se entrega", async () => {
    const { rerender } = render(<KpiCard etiqueta="Aportes" valor="1" />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    rerender(<KpiCard etiqueta="Aportes" valor="1" ayuda={{ titulo: "Aportes", contenido: "Explicacion" }} />);
    await userEvent.click(screen.getByRole("button", { name: "Ayuda: Aportes" }));
    expect(screen.getByRole("note")).toHaveTextContent("Explicacion");
  });

  it("renderiza el icono en el color de acento", () => {
    render(<KpiCard etiqueta="x" valor="1" acento="#0891b2" icono={<svg data-testid="icono" />} />);
    expect(screen.getByTestId("icono").parentElement).toHaveStyle({ color: "rgb(8, 145, 178)" });
  });
});

describe("RiskBadge", () => {
  const casos: [NivelRiesgo, string, string][] = [
    ["OPTIMO", "Óptimo", "var(--color-optimo)"],
    ["ALERTA", "Alerta de sequía", "var(--color-alerta)"],
    ["CRITICO", "Crítico", "var(--color-critico)"],
    ["REBOCE", "Reboce", "var(--color-reboce)"],
  ];

  it.each(casos)("%s se muestra como '%s' con su color semantico", (nivel, texto, color) => {
    render(<RiskBadge nivel={nivel} />);
    expect(screen.getByText(texto)).toHaveStyle({ color });
  });

  it("tiene un tamano compacto para tablas", () => {
    render(<RiskBadge nivel="OPTIMO" tamano="sm" />);
    expect(screen.getByText("Óptimo").className).toContain("text-[11px]");
  });
});

describe("SistemaRiesgoCard", () => {
  it.each(["OPTIMO", "ALERTA", "CRITICO", "REBOCE"] as NivelRiesgo[])("muestra el nivel %s", (nivel) => {
    render(<SistemaRiesgoCard nivel={nivel} totalEmbalses={24} />);
    expect(screen.getByText("Riesgo del sistema")).toBeInTheDocument();
    expect(screen.getByText(/monitoreados/)).toHaveTextContent("24 embalses monitoreados");
  });

  it("explica los umbrales en su ayuda", async () => {
    render(<SistemaRiesgoCard nivel="OPTIMO" totalEmbalses={1} />);
    await userEvent.click(screen.getByRole("button", { name: "Ayuda: Riesgo del sistema" }));
    const ayuda = screen.getByRole("note");
    for (const umbral of ["30%", "15%", "95%"]) expect(ayuda).toHaveTextContent(umbral);
  });
});
