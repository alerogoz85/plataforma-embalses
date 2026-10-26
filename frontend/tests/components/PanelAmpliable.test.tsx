import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import DnsPage from "@/app/dns/page";
import { PanelAmpliable } from "@/components/ui/PanelAmpliable";
import { simularFetch } from "../mocks/fetch";
import { fijarUrl, parametrosActuales, urlActual } from "../mocks/navigation";
import {
  crearCambiosDns, crearCatalogoDns, crearCausasDns, crearModeloDns, crearPatronesDns, crearResumenDns, crearSerieDns, crearZonasDns,
} from "../dns/fixturesDns";

vi.mock("recharts", () => import("../mocks/recharts"));

function montar(ampliado = false) {
  const alternar = vi.fn();
  const vista = render(
    <PanelAmpliable id="panel-x" resumen="19 zonas" ampliado={ampliado} onAlternar={alternar} encabezado={<h2>Titulo</h2>}>
      <p>contenido largo</p>
    </PanelAmpliable>,
  );
  return { alternar, ...vista };
}

describe("PanelAmpliable", () => {
  it("por defecto esta contraido: zona desplazable enfocable con nombre, y boton «Ver todo» con su resumen", () => {
    montar();
    const zona = screen.getByRole("region", { name: "Contenido desplazable" });
    expect(zona).toHaveAttribute("tabindex", "0");
    expect(zona).toHaveAttribute("id", "panel-x");
    expect(zona.className).toContain("overflow-y-auto");
    const boton = screen.getByRole("button", { name: "Ver todo (19 zonas)" });
    expect(boton).toHaveAttribute("aria-expanded", "false");
    expect(boton).toHaveAttribute("aria-controls", "panel-x");
  });

  it("contraido es una tarjeta superpuesta a su celda (para no aportar altura propia) con minimo legible", () => {
    const { container } = montar();
    expect(container.firstElementChild!.className).toContain("xl:min-h-[26rem]");
    expect(container.querySelector(".rounded-2xl")!.className).toContain("xl:absolute");
  });

  it("ampliado muestra todo sin zona con scroll y el boton dice «Ver menos»", () => {
    const { container } = montar(true);
    expect(screen.queryByRole("region", { name: "Contenido desplazable" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ver menos" })).toHaveAttribute("aria-expanded", "true");
    expect(container.querySelector(".rounded-2xl")!.className).not.toContain("xl:absolute");
    expect(screen.getByText("contenido largo")).toBeInTheDocument();
  });

  it("el contenido esta siempre en el DOM (nada queda inaccesible al contraer) y el boton avisa", async () => {
    const { alternar } = montar();
    expect(screen.getByText("contenido largo")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Ver todo/ }));
    expect(alternar).toHaveBeenCalledOnce();
  });
});

const D = "/api/v1/dns";
function apiDns() {
  return simularFetch({
    [`${D}/catalogo`]: () => crearCatalogoDns(), [`${D}/resumen`]: () => crearResumenDns(), [`${D}/serie`]: () => crearSerieDns(),
    [`${D}/zonas`]: () => crearZonasDns(), [`${D}/patrones`]: () => crearPatronesDns(), [`${D}/causas`]: () => crearCausasDns(),
    [`${D}/cambios-reporte`]: () => crearCambiosDns(), [`${D}/modelo`]: () => crearModeloDns(),
  });
}

describe("Tablero DNS: paneles ampliables (Priorizacion de zonas y Modelo predictivo)", () => {
  it("por defecto ambos estan contraidos, con el numero de elementos en el boton", async () => {
    fijarUrl("/dns");
    apiDns();
    render(<DnsPage />);
    expect(await screen.findByRole("button", { name: "Ver todo (2 zonas)" })).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByRole("button", { name: /^Ver todo \(2 subáreas y más\)$/ })).toHaveAttribute("aria-expanded", "false");
  });

  it("las dos filas se estiran al mismo alto por defecto y se sueltan (items-start) al ampliar el panel largo", async () => {
    fijarUrl("/dns");
    apiDns();
    const { container } = render(<DnsPage />);
    await screen.findByRole("button", { name: "Ver todo (2 zonas)" });
    const filas = () => [...container.querySelectorAll("main > div[class*=\"xl:grid-cols-2\"]")].map((g) => g.className);
    expect(filas().every((c) => c.includes("xl:items-stretch"))).toBe(true);
    await userEvent.click(screen.getByRole("button", { name: "Ver todo (2 zonas)" }));
    const [primera, segunda] = filas();
    expect(primera).toContain("xl:items-start");
    expect(segunda).toContain("xl:items-stretch"); // la otra fila no cambia
  });

  it("ampliar escribe ?ampliar= en la URL, se pueden ampliar los dos y «Ver menos» lo quita", async () => {
    fijarUrl("/dns");
    apiDns();
    render(<DnsPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Ver todo (2 zonas)" }));
    expect(urlActual()).toBe("/dns?ampliar=zonas");
    await userEvent.click(screen.getByRole("button", { name: /^Ver todo \(2 subáreas/ }));
    expect(parametrosActuales().get("ampliar")).toBe("zonas,modelo");
    await userEvent.click(screen.getAllByRole("button", { name: "Ver menos" })[0]);
    expect(parametrosActuales().get("ampliar")).toBe("modelo");
    await userEvent.click(screen.getByRole("button", { name: "Ver menos" }));
    expect(urlActual()).toBe("/dns");
  });

  it("una direccion con ?ampliar= abre los paneles ya ampliados; valores desconocidos se ignoran", async () => {
    fijarUrl("/dns?ampliar=modelo,otro");
    apiDns();
    render(<DnsPage />);
    expect(await screen.findByRole("button", { name: "Ver todo (2 zonas)" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Ver menos" })).toHaveLength(1);
    expect(screen.getAllByRole("region", { name: "Contenido desplazable" })).toHaveLength(1); // solo zonas sigue contraido
  });

  it("filtrar no cambia el estado ampliado, y «Restablecer filtros» tampoco lo toca", async () => {
    fijarUrl("/dns?ampliar=zonas&periodo=12");
    apiDns();
    render(<DnsPage />);
    await screen.findByRole("button", { name: "Ver menos" });
    await userEvent.click(screen.getByRole("button", { name: /Restablecer filtros/ }));
    expect(urlActual()).toBe("/dns?ampliar=zonas");
  });

  it("el clic en una zona sigue funcionando dentro del panel contraido", async () => {
    fijarUrl("/dns");
    apiDns();
    render(<DnsPage />);
    await userEvent.click(await screen.findByRole("button", { name: "SubArea Tres" }));
    expect(parametrosActuales().get("subarea")).toBe("Are0003");
  });
});
