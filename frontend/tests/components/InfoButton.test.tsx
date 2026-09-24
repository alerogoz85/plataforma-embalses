import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { InfoButton } from "@/components/ui/InfoButton";

function boton() {
  return screen.getByRole("button", { name: "Ayuda: % Vol. útil" });
}

describe("InfoButton", () => {
  it("empieza cerrado y con un nombre accesible", () => {
    render(<InfoButton titulo="% Vol. útil">Explicacion</InfoButton>);
    expect(boton()).toHaveAttribute("aria-expanded", "false");
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("al pasar el cursor muestra el titulo y la explicacion, y al salir se oculta", async () => {
    render(<InfoButton titulo="% Vol. útil"><p>Porcentaje de agua útil</p></InfoButton>);
    await userEvent.hover(boton());
    const nota = screen.getByRole("note");
    expect(nota).toHaveTextContent("% Vol. útil");
    expect(nota).toHaveTextContent("Porcentaje de agua útil");
    expect(boton()).toHaveAttribute("aria-expanded", "true");

    await userEvent.unhover(boton());
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
    expect(boton()).toHaveAttribute("aria-expanded", "false");
  });

  it("el panel no intercepta el cursor (no hay parpadeo al mover el mouse)", async () => {
    render(<InfoButton titulo="% Vol. útil">x</InfoButton>);
    await userEvent.hover(boton());
    expect(screen.getByRole("note")).toHaveStyle({ pointerEvents: "none" });
  });

  it("al enfocar con el teclado lo muestra y al perder el foco lo oculta", async () => {
    render(<InfoButton titulo="% Vol. útil">x</InfoButton>);
    await userEvent.tab();
    expect(boton()).toHaveFocus();
    expect(screen.getByRole("note")).toBeInTheDocument();
    await userEvent.tab();
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("un toque (clic) lo abre para pantallas sin cursor y otro toque fuera lo cierra", async () => {
    render(
      <div>
        <span>fuera</span>
        <InfoButton titulo="% Vol. útil">x</InfoButton>
      </div>,
    );
    fireEvent.click(boton());
    expect(screen.getByRole("note")).toBeInTheDocument();
    await userEvent.click(screen.getByText("fuera"));
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("enlaza el boton con su panel mediante aria-controls", async () => {
    render(<InfoButton titulo="% Vol. útil">x</InfoButton>);
    await userEvent.hover(boton());
    expect(boton().getAttribute("aria-controls")).toBe(screen.getByRole("note").id);
  });

  it("Escape lo cierra", async () => {
    render(<InfoButton titulo="% Vol. útil">x</InfoButton>);
    await userEvent.hover(boton());
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("se cierra al hacer scroll o cambiar el tamano de la ventana", async () => {
    render(<InfoButton titulo="% Vol. útil">x</InfoButton>);
    await userEvent.hover(boton());
    fireEvent.scroll(window);
    expect(screen.queryByRole("note")).not.toBeInTheDocument();

    await userEvent.hover(boton());
    fireEvent(window, new Event("resize"));
    expect(screen.queryByRole("note")).not.toBeInTheDocument();
  });

  it("no propaga el clic al contenedor (p. ej. no reordena una columna)", async () => {
    const alClic = vi.fn();
    render(
      <div onClick={alClic}>
        <InfoButton titulo="% Vol. útil">x</InfoButton>
      </div>,
    );
    await userEvent.click(boton());
    expect(screen.getByRole("note")).toBeInTheDocument();
    expect(alClic).not.toHaveBeenCalled();
  });

  it("solo hay un panel abierto a la vez", async () => {
    render(
      <>
        <InfoButton titulo="Uno">a</InfoButton>
        <InfoButton titulo="Dos">b</InfoButton>
      </>,
    );
    await userEvent.hover(screen.getByRole("button", { name: "Ayuda: Uno" }));
    await userEvent.unhover(screen.getByRole("button", { name: "Ayuda: Uno" }));
    await userEvent.hover(screen.getByRole("button", { name: "Ayuda: Dos" }));
    expect(screen.getAllByRole("note")).toHaveLength(1);
    expect(screen.getByRole("note")).toHaveTextContent("Dos");
  });

  describe("posicion", () => {
    function abrirConBoton(caja: Partial<DOMRect>, anchoVentana: number) {
      Object.defineProperty(window, "innerWidth", { value: anchoVentana, configurable: true });
      render(<InfoButton titulo="% Vol. útil">x</InfoButton>);
      vi.spyOn(HTMLButtonElement.prototype, "getBoundingClientRect").mockReturnValue({
        left: 0, right: 0, top: 0, bottom: 0, width: 20, height: 20, x: 0, y: 0, toJSON: () => ({}), ...caja,
      });
      return userEvent.hover(boton());
    }

    it("se coloca justo debajo del boton", async () => {
      await abrirConBoton({ left: 100, bottom: 50 }, 1024);
      expect(screen.getByRole("note")).toHaveStyle({ position: "fixed", top: "56px", left: "100px", width: "320px" });
    });

    it("no se sale por la derecha de la pantalla", async () => {
      await abrirConBoton({ left: 1000, bottom: 50 }, 1024);
      expect(screen.getByRole("note")).toHaveStyle({ left: "692px" }); // 1024 - 320 - 12
    });

    it("se reduce en pantallas estrechas y respeta el margen izquierdo", async () => {
      await abrirConBoton({ left: 250, bottom: 50 }, 300);
      expect(screen.getByRole("note")).toHaveStyle({ width: "276px", left: "12px" });
    });
  });
});
