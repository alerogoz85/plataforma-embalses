import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import DashboardPage from "@/app/page";
import { AYUDAS } from "@/components/dashboard/ayudas";
import { simularApi } from "./rutas";

vi.mock("recharts", () => import("../mocks/recharts"));

async function paginaCompleta() {
  simularApi();
  render(<DashboardPage />);
  await screen.findByText("77.5%");
  await screen.findByTestId("bar-chart");
  await waitFor(() => expect(screen.getAllByTestId("composed-chart")).toHaveLength(2));
}

function tieneAyuda(elemento: Element): boolean {
  // th: el boton va dentro. h2: va en la esquina derecha del encabezado de la tarjeta
  // (hermano del bloque del titulo). Resto: hermano dentro del mismo contenedor.
  const contenedor =
    elemento.tagName === "TH"
      ? elemento
      : elemento.tagName === "H2"
        ? elemento.parentElement!.parentElement!
        : elemento.parentElement!;
  return contenedor.querySelector('button[aria-label^="Ayuda:"]') !== null;
}

describe("catalogo de ayudas", () => {
  const entradas = Object.entries(AYUDAS);

  it("cada ayuda tiene titulo y contenido no vacios", () => {
    for (const [clave, ayuda] of entradas) {
      expect(ayuda.titulo.trim(), clave).not.toBe("");
      expect(ayuda.contenido, clave).toBeTruthy();
    }
  });

  it("los titulos no se repiten (cada boton se identifica por su nombre)", () => {
    const titulos = entradas.map(([, a]) => a.titulo);
    expect(new Set(titulos).size).toBe(titulos.length);
  });

  it("no quedan textos de la version con datos sinteticos", () => {
    const html = render(<>{entradas.map(([k, a]) => <div key={k}>{a.contenido}</div>)}</>).container.textContent!;
    for (const obsoleto of [/0\.6 kWh/, /potencia instalada/i, /Generación GWh/, /\bcotas?\b/i]) {
      expect(html).not.toMatch(obsoleto);
    }
  });
});

describe("cobertura de ayuda en el dashboard", () => {
  it("todo encabezado tecnico, columna, filtro y tarjeta tiene su boton de ayuda", async () => {
    await paginaCompleta();

    const sinAyuda: string[] = [];
    document.querySelectorAll("h2, th, p.uppercase, span.uppercase").forEach((el) => {
      const texto = el.textContent!.trim();
      if (texto && el.closest('[role="note"]') === null && !tieneAyuda(el)) sinAyuda.push(texto);
    });
    // Los encabezados de la fila de sr-only del label no cuentan como encabezados visibles.
    expect(sinAyuda).toEqual([]);
  });

  it("hay al menos un boton por cada seccion funcional", async () => {
    await paginaCompleta();
    const nombres = screen.getAllByRole("button", { name: /^Ayuda:/ }).map((b) => b.getAttribute("aria-label"));
    for (const esperado of [
      "Ayuda: Filtro de región", "Ayuda: Fecha final", "Ayuda: % Volumen útil nacional",
      "Ayuda: Riesgo del sistema", "Ayuda: Horizonte del pronóstico", "Ayuda: Senda del volumen útil",
      "Ayuda: Validación walk-forward", "Ayuda: Tabla de embalses", "Ayuda: Autonomía (días)",
    ]) {
      expect(nombres).toContain(esperado);
    }
    expect(nombres.length).toBeGreaterThanOrEqual(29);
  });

  it("todos los botones abren una explicacion con contenido y se pueden cerrar", async () => {
    await paginaCompleta();
    const botones = screen.getAllByRole("button", { name: /^Ayuda:/ });
    const problemas: string[] = [];

    for (const boton of botones) {
      await userEvent.click(boton);
      const nota = screen.queryByRole("note");
      if (!nota || (nota.textContent ?? "").trim().length < 20) problemas.push(boton.getAttribute("aria-label")!);
      await userEvent.keyboard("{Escape}");
      if (screen.queryByRole("note")) problemas.push(`${boton.getAttribute("aria-label")} (no cierra)`);
    }
    expect(problemas).toEqual([]);
  });
});
