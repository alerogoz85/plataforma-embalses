import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EmbalsesTable } from "@/components/dashboard/EmbalsesTable";
import { EMBALSES_EJEMPLO, crearEmbalse } from "../fixtures";
import { fijarUrl } from "../mocks/navigation";

function montar(props: Partial<React.ComponentProps<typeof EmbalsesTable>> = {}) {
  const onSeleccionar = vi.fn();
  render(
    <EmbalsesTable
      embalses={EMBALSES_EJEMPLO}
      cargando={false}
      onSeleccionar={onSeleccionar}
      embalseSeleccionado={null}
      {...props}
    />,
  );
  return { onSeleccionar };
}

function nombres() {
  return screen
    .getAllByRole("row")
    .slice(1)
    .map((fila) => within(fila).getAllByRole("cell")[0].childNodes[0].textContent?.trim());
}

const encabezado = (texto: RegExp) => screen.getByRole("columnheader", { name: texto });
const fila = (nombre: string) => screen.getByRole("row", { name: new RegExp(nombre) });

describe("EmbalsesTable ordenamiento", () => {
  it("por defecto ordena por %V. util de menor a mayor", () => {
    montar();
    expect(nombres()).toEqual(["Muna", "Prado", "Agregado Bogotá", "Guavio"]);
    expect(encabezado(/% Vol\. útil/)).toHaveTextContent("↑");
  });

  it("un segundo clic sobre la misma columna invierte el orden", async () => {
    montar();
    await userEvent.click(encabezado(/% Vol\. útil/));
    expect(nombres()).toEqual(["Guavio", "Agregado Bogotá", "Prado", "Muna"]);
    expect(encabezado(/% Vol\. útil/)).toHaveTextContent("↓");
  });

  it("cambiar de columna empieza de nuevo en ascendente", async () => {
    montar();
    await userEvent.click(encabezado(/% Vol\. útil/)); // ahora descendente
    await userEvent.click(encabezado(/Turbinado/));
    expect(encabezado(/Turbinado/)).toHaveTextContent("↑");
    expect(nombres()).toEqual(["Agregado Bogotá", "Prado", "Muna", "Guavio"]); // null, 7.1, 26.5, 62.4
  });

  it("ordena texto alfabeticamente (columna Embalse)", async () => {
    montar();
    await userEvent.click(encabezado(/^Embalse/));
    expect(nombres()).toEqual(["Agregado Bogotá", "Guavio", "Muna", "Prado"]);
  });

  it("los datos no publicados (null) quedan primero en ascendente y ultimos en descendente", async () => {
    montar();
    await userEvent.click(encabezado(/Aportes/));
    expect(nombres().slice(0, 2).sort()).toEqual(["Agregado Bogotá", "Muna"]);
    await userEvent.click(encabezado(/Aportes/));
    expect(nombres().slice(-2).sort()).toEqual(["Agregado Bogotá", "Muna"]);
  });

  it("abrir la ayuda de una columna no la reordena", async () => {
    montar();
    await userEvent.click(screen.getByRole("button", { name: "Ayuda: Aportes (% media)" }));
    expect(encabezado(/% Vol\. útil/)).toHaveTextContent("↑");
    expect(nombres()).toEqual(["Muna", "Prado", "Agregado Bogotá", "Guavio"]);
  });
});

describe("EmbalsesTable busqueda", () => {
  it("filtra por nombre sin distinguir mayusculas y actualiza el conteo", async () => {
    montar();
    await userEvent.type(screen.getByPlaceholderText(/Buscar embalse/), "pRaD");
    expect(nombres()).toEqual(["Prado"]);
    expect(screen.getByText("1 de 4 registros")).toBeInTheDocument();
  });

  it("filtra tambien por region", async () => {
    montar();
    await userEvent.type(screen.getByPlaceholderText(/Buscar embalse/), "oriente");
    expect(nombres()).toEqual(["Guavio"]);
  });

  it("sin coincidencias muestra un mensaje", async () => {
    montar();
    await userEvent.type(screen.getByPlaceholderText(/Buscar embalse/), "zzz");
    expect(screen.getByText(/No hay embalses que coincidan/)).toBeInTheDocument();
    expect(screen.getByText("0 de 4 registros")).toBeInTheDocument();
  });
});

describe("EmbalsesTable barra y paginacion", () => {
  const muchos = (n: number) =>
    Array.from({ length: n }, (_, i) => crearEmbalse({ id: `E${i}`, nombre: `Embalse ${String(i).padStart(2, "0")}`, pct_volumen_util: i }));

  it("dibuja una barra de progreso con el %V. util de cada embalse", () => {
    montar();
    const barra = screen.getByRole("progressbar", { name: "% Volumen útil de Muna" });
    expect(barra).toHaveAttribute("aria-valuenow");
    expect(screen.getAllByRole("progressbar")).toHaveLength(4);
  });

  it("con pocas filas no muestra la paginacion", () => {
    montar();
    expect(screen.queryByRole("navigation", { name: "Paginación de la tabla" })).not.toBeInTheDocument();
  });

  it("pagina de 25 en 25 por defecto y navega entre paginas", async () => {
    montar({ embalses: muchos(30) });
    expect(nombres()).toHaveLength(25);
    expect(screen.getByText("Mostrando 1–25 de 30")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anterior" })).toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    expect(nombres()).toHaveLength(5);
    expect(screen.getByText("Mostrando 26–30 de 30")).toBeInTheDocument();
    expect(screen.getByText("Página 2 de 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Siguiente" })).toBeDisabled();
  });

  it("cambiar las filas por pagina vuelve a la primera pagina", async () => {
    montar({ embalses: muchos(30) });
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    await userEvent.selectOptions(screen.getByLabelText("Filas por página"), "10");
    expect(nombres()).toHaveLength(10);
    expect(screen.getByText("Página 1 de 3")).toBeInTheDocument();
  });

  it("buscar o reordenar vuelve a la primera pagina", async () => {
    montar({ embalses: muchos(30) });
    await userEvent.click(screen.getByRole("button", { name: "Siguiente" }));
    await userEvent.click(encabezado(/Embalse/));
    expect(screen.getByText("Página 1 de 2")).toBeInTheDocument();
  });

  it("si los filtros dejan menos paginas que la pedida muestra la ultima", () => {
    fijarUrl("/?pag=9");
    montar({ embalses: muchos(30) });
    expect(screen.getByText("Página 2 de 2")).toBeInTheDocument();
  });

  it("sin coincidencias ofrece borrar la busqueda", async () => {
    montar();
    await userEvent.type(screen.getByPlaceholderText(/Buscar embalse/), "zzz");
    await userEvent.click(screen.getByRole("button", { name: "Borrar la búsqueda" }));
    expect(nombres()).toHaveLength(4);
  });
});

describe("EmbalsesTable contenido", () => {
  it("muestra una raya en los datos no publicados y el dato real si existe", () => {
    montar();
    const muna = within(fila("Muna")).getAllByRole("cell");
    // [nombre, region, %vol, aportes, vertimientos, turbinado, energia, autonomia, reporte]
    expect(muna[3]).toHaveTextContent("—");
    expect(muna[6]).toHaveTextContent("—");
    expect(muna[7]).toHaveTextContent("—");
    expect(muna[5]).toHaveTextContent("26,5");
  });

  it("el agregado, que no publica aportes ni descargas, muestra una raya en cada una", () => {
    montar();
    const celdas = within(fila("Agregado Bogotá")).getAllByRole("cell");
    // aportes, vertimientos, turbinado
    for (const indice of [3, 4, 5]) expect(celdas[indice]).toHaveTextContent("—");
    expect(celdas[3]).not.toHaveTextContent("0");
    expect(celdas[5]).not.toHaveTextContent("0,0");
  });

  it("un cero real se muestra como 0, no como dato faltante", () => {
    montar();
    expect(within(fila("Guavio")).getAllByRole("cell")[4]).toHaveTextContent("0,0");
  });

  it("muestra la autonomia estimada cuando existe", () => {
    montar();
    expect(within(fila("Prado")).getAllByRole("cell")[7]).toHaveTextContent("4967");
  });

  it("marca como 'Agregado' solo al agregado", () => {
    montar();
    expect(within(fila("Agregado Bogotá")).getByText("Agregado")).toBeInTheDocument();
    expect(within(fila("Guavio")).queryByText("Agregado")).not.toBeInTheDocument();
  });

  it("muestra el %V. util con su nivel de riesgo", () => {
    montar();
    const celda = within(fila("Muna")).getAllByRole("cell")[2];
    expect(celda).toHaveTextContent("12.4%");
    expect(celda).toHaveTextContent("Crítico");
  });

  it("no rompe con valores por encima de 100%", () => {
    montar({ embalses: [crearEmbalse({ id: "PLAYAS", nombre: "Playas", pct_volumen_util: 111.8, nivel_riesgo: "NORMAL" })] });
    expect(within(fila("Playas")).getAllByRole("cell")[2]).toHaveTextContent("111.8%");
  });
});

describe("EmbalsesTable interaccion", () => {
  it("clic en una fila la selecciona", async () => {
    const { onSeleccionar } = montar();
    await userEvent.click(fila("Prado"));
    expect(onSeleccionar).toHaveBeenCalledWith("PRADO");
  });

  it("resalta la fila seleccionada", () => {
    montar({ embalseSeleccionado: "PRADO" });
    expect(fila("Prado")).toHaveStyle({ backgroundColor: "var(--color-marca-bg)" });
    expect(fila("Guavio")).not.toHaveStyle({ backgroundColor: "var(--color-marca-bg)" });
  });

  it("los enlaces de reporte apuntan a la API y no seleccionan la fila", async () => {
    const { onSeleccionar } = montar();
    const enlaces = within(fila("Prado")).getAllByRole("link");
    expect(enlaces.map((e) => e.textContent)).toEqual(["CSV", "JSON"]);
    expect(new URL(enlaces[0].getAttribute("href")!).searchParams.get("formato")).toBe("csv");
    expect(enlaces[0].getAttribute("href")).toContain("/api/v1/embalses/PRADO/reporte");
    expect(new URL(enlaces[1].getAttribute("href")!).searchParams.get("formato")).toBe("json");

    enlaces[0].addEventListener("click", (e) => e.preventDefault());
    await userEvent.click(enlaces[0]);
    expect(onSeleccionar).not.toHaveBeenCalled();
  });
});

describe("EmbalsesTable carga", () => {
  it("muestra filas esqueleto mientras carga y no hay datos", () => {
    montar({ embalses: [], cargando: true });
    expect(screen.getAllByRole("row")).toHaveLength(1 + 6);
    expect(screen.queryByText(/No hay embalses/)).not.toBeInTheDocument();
  });

  it("sin datos y sin cargar muestra el mensaje vacio", () => {
    montar({ embalses: [], cargando: false });
    expect(screen.getByText(/No hay embalses que coincidan/)).toBeInTheDocument();
  });

  it("con datos ya cargados no muestra esqueletos aunque se este recargando", () => {
    montar({ cargando: true });
    expect(nombres()).toHaveLength(4);
  });
});
