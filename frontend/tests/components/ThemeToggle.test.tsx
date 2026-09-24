import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ThemeToggle } from "@/components/layout/ThemeToggle";

const aClaro = () => screen.getByRole("button", { name: "Cambiar a modo claro" });
const aOscuro = () => screen.getByRole("button", { name: "Cambiar a modo oscuro" });

function simularPreferenciaDelSistema(oscuro: boolean) {
  window.matchMedia = ((consulta: string) => ({
    matches: oscuro && consulta.includes("dark"),
    media: consulta,
    addEventListener: () => {},
    removeEventListener: () => {},
  })) as unknown as typeof window.matchMedia;
}

describe("ThemeToggle", () => {
  it("arranca en claro cuando no hay preferencia guardada ni del sistema", () => {
    render(<ThemeToggle />);
    expect(aOscuro()).toBeInTheDocument();
  });

  it("respeta la preferencia de modo oscuro del sistema si no hay una guardada", () => {
    simularPreferenciaDelSistema(true);
    render(<ThemeToggle />);
    expect(aClaro()).toBeInTheDocument();
  });

  it("la preferencia guardada gana sobre la del sistema", () => {
    simularPreferenciaDelSistema(true);
    window.localStorage.setItem("tema", "light");
    render(<ThemeToggle />);
    expect(aOscuro()).toBeInTheDocument();
  });

  it("alternar a oscuro aplica la clase, guarda la preferencia y cambia la etiqueta", async () => {
    render(<ThemeToggle />);
    await userEvent.click(aOscuro());
    expect(document.documentElement).toHaveClass("dark");
    expect(window.localStorage.getItem("tema")).toBe("dark");
    expect(aClaro()).toBeInTheDocument();
  });

  it("alternar de nuevo vuelve a claro", async () => {
    render(<ThemeToggle />);
    await userEvent.click(aOscuro());
    await userEvent.click(aClaro());
    expect(document.documentElement).not.toHaveClass("dark");
    expect(window.localStorage.getItem("tema")).toBe("light");
    expect(aOscuro()).toBeInTheDocument();
  });

  it("dos toggles en la pagina se mantienen sincronizados", async () => {
    render(
      <>
        <ThemeToggle />
        <ThemeToggle />
      </>,
    );
    await userEvent.click(screen.getAllByRole("button", { name: "Cambiar a modo oscuro" })[0]);
    expect(screen.getAllByRole("button", { name: "Cambiar a modo claro" })).toHaveLength(2);
  });
});
