import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ActualizarPage from "@/app/actualizar/page";
import { fijarUrl } from "../mocks/navigation";
import { crearAuditoria, crearCatalogoAdmin, crearResultadoCarga, crearSesion } from "./fixturesAdmin";

vi.mock("recharts", () => import("../mocks/recharts"));

interface Llamada { metodo: string; ruta: string; csrf: string | null; credenciales: RequestCredentials | undefined; cuerpo: BodyInit | null | undefined }

/** fetch que enruta por «METODO /ruta» (el del resto de pruebas solo enruta por ruta y aquí importa el método y los encabezados). */
function simularAdmin(rutas: Record<string, (c: Llamada) => unknown>) {
  const llamadas: Llamada[] = [];
  vi.stubGlobal("fetch", vi.fn(async (entrada: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(entrada));
    const metodo = init?.method ?? "GET";
    const c: Llamada = { metodo, ruta: url.pathname.replace("/api/v1/admin", ""), csrf: (init?.headers as Record<string, string> | undefined)?.["X-CSRF-Token"] ?? null, credenciales: init?.credentials, cuerpo: init?.body };
    llamadas.push(c);
    const manejador = rutas[`${metodo} ${c.ruta}`];
    const resultado = manejador ? manejador(c) : { status: 404, cuerpo: { detalle: `sin ruta ${metodo} ${c.ruta}` } };
    const error = typeof resultado === "object" && resultado !== null && "status" in resultado ? (resultado as { status: number; cuerpo?: unknown }) : null;
    return { ok: !error, status: error?.status ?? 200, statusText: "x", json: async () => (error ? error.cuerpo ?? null : resultado) } as Response;
  }));
  return llamadas;
}

const sinSesion = { status: 401, cuerpo: { detalle: "Debes iniciar sesión para continuar" } };
const json = (nombre: string, contenido: string, tipo = "application/json") => new File([contenido], nombre, { type: tipo });

async function escribirCredenciales(usuario: string, contrasena: string) {
  await userEvent.type(screen.getByLabelText("Usuario"), usuario);
  await userEvent.type(screen.getByLabelText("Contraseña"), contrasena);
  await userEvent.click(screen.getByRole("button", { name: "Ingresar" }));
}

beforeEach(() => fijarUrl("/actualizar"));
afterEach(() => vi.unstubAllGlobals());

describe("Acceso al módulo de actualización", () => {
  it("sin sesión muestra el formulario de acceso y no los tableros", async () => {
    simularAdmin({ "GET /sesion": () => sinSesion });
    render(<ActualizarPage />);
    expect(await screen.findByRole("form", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(screen.queryByText("1. Elige el tablero")).not.toBeInTheDocument();
  });

  it("credenciales incorrectas muestran el mensaje de la API y vacían la contraseña", async () => {
    const llamadas = simularAdmin({
      "GET /sesion": () => sinSesion,
      "POST /sesion": () => ({ status: 401, cuerpo: { detalle: "Usuario o contraseña incorrectos" } }),
    });
    render(<ActualizarPage />);
    await screen.findByRole("form", { name: "Iniciar sesión" });
    await escribirCredenciales("ana", "mala-clave");
    expect(await screen.findByRole("alert")).toHaveTextContent("Usuario o contraseña incorrectos");
    expect(screen.getByLabelText("Contraseña")).toHaveValue("");
    expect(llamadas.find((l) => l.metodo === "POST")?.credenciales).toBe("include");
  });

  it("la cuenta bloqueada muestra el aviso de la API", async () => {
    simularAdmin({ "GET /sesion": () => sinSesion, "POST /sesion": () => ({ status: 429, cuerpo: { detalle: "Demasiados intentos fallidos. Intenta de nuevo en 15 minutos" } }) });
    render(<ActualizarPage />);
    await screen.findByRole("form", { name: "Iniciar sesión" });
    await escribirCredenciales("ana", "x");
    expect(await screen.findByRole("alert")).toHaveTextContent("15 minutos");
  });

  it("el campo de contraseña es de tipo password, con autocompletado correcto, y el botón espera a que haya datos", async () => {
    simularAdmin({ "GET /sesion": () => sinSesion });
    render(<ActualizarPage />);
    const clave = await screen.findByLabelText("Contraseña");
    expect(clave).toHaveAttribute("type", "password");
    expect(clave).toHaveAttribute("autocomplete", "current-password");
    expect(screen.getByRole("button", { name: "Ingresar" })).toBeDisabled();
  });

  it("con sesión vigente entra directo y muestra solo los tableros del catálogo", async () => {
    simularAdmin({ "GET /sesion": () => crearSesion(), "GET /tableros": () => crearCatalogoAdmin(), "GET /auditoria": () => crearAuditoria() });
    render(<ActualizarPage />);
    expect(await screen.findByText("1. Elige el tablero")).toBeInTheDocument();
    expect(screen.getAllByRole("radio").map((r) => r.closest("label")?.textContent)).toEqual([
      expect.stringContaining("Optimización hidrotérmica"), expect.stringContaining("Gas natural"),
    ]);
  });

  it("un usuario sin tableros asignados lo ve explicado", async () => {
    simularAdmin({ "GET /sesion": () => crearSesion({ rol: "cargador" }), "GET /tableros": () => crearCatalogoAdmin({ tableros: [] }) });
    render(<ActualizarPage />);
    expect(await screen.findByText(/no tiene tableros asignados/)).toBeInTheDocument();
  });

  it("cerrar sesión envía el token CSRF y vuelve al formulario", async () => {
    const llamadas = simularAdmin({
      "GET /sesion": () => crearSesion(), "GET /tableros": () => crearCatalogoAdmin(), "GET /auditoria": () => crearAuditoria(), "DELETE /sesion": () => undefined,
    });
    render(<ActualizarPage />);
    await userEvent.click(await screen.findByRole("button", { name: "Cerrar sesión" }));
    expect(await screen.findByRole("form", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(llamadas.find((l) => l.metodo === "DELETE")?.csrf).toBe("csrf-de-prueba");
  });
});

async function entrarYElegir(tablero: string, rutas: Record<string, (c: Llamada) => unknown> = {}, catalogo = crearCatalogoAdmin(), rol: "administrador" | "cargador" = "administrador") {
  const llamadas = simularAdmin({ "GET /sesion": () => crearSesion({ rol }), "GET /tableros": () => catalogo, "GET /auditoria": () => crearAuditoria(), ...rutas });
  render(<ActualizarPage />);
  await userEvent.click(await screen.findByRole("radio", { name: new RegExp(tablero) }));
  return llamadas;
}

const campo = (etiqueta: string) => screen.getByLabelText(new RegExp(`^${etiqueta}`)) as HTMLInputElement;

describe("Carga y validación de archivos", () => {
  it("elegir un tablero pone su nombre en la URL y muestra sus archivos con obligatorio/opcional", async () => {
    await entrarYElegir("Optimización");
    expect(window.location.search).toBe("?tablero=optimizacion");
    expect(screen.getByText("Obligatorio")).toBeInTheDocument();
    expect(screen.getByText("Opcional")).toBeInTheDocument();
    expect(campo("Resumen de la corrida")).toHaveAttribute("accept", ".json");
  });

  it("un tablero de la URL que no existe en el catálogo se ignora", async () => {
    fijarUrl("/actualizar?tablero=embalses");
    simularAdmin({ "GET /sesion": () => crearSesion(), "GET /tableros": () => crearCatalogoAdmin() });
    render(<ActualizarPage />);
    await screen.findByText("1. Elige el tablero");
    expect(screen.queryByText("2. Carga los archivos")).not.toBeInTheDocument();
  });

  it("no se puede revisar sin los archivos obligatorios y dice cuál falta", async () => {
    await entrarYElegir("Optimización");
    expect(screen.getByRole("button", { name: /Revisar archivos/ })).toBeDisabled();
    expect(screen.getByText(/Falta: Resumen de la corrida/)).toBeInTheDocument();
  });

  it("un archivo con formato equivocado se avisa en el campo y bloquea la revisión", async () => {
    await entrarYElegir("Optimización");
    fireEvent.change(campo("Resumen de la corrida"), { target: { files: [json("resumen.exe", "MZ", "application/octet-stream")] } });
    expect(await screen.findByRole("alert")).toHaveTextContent("no es .json");
    expect(screen.getByRole("button", { name: /Revisar archivos/ })).toBeDisabled();
  });

  it("flujo completo: revisar envía el CSRF y las credenciales; aplicar envía las huellas; queda el aviso y el enlace al tablero", async () => {
    const llamadas = await entrarYElegir("Optimización", {
      "POST /tableros/optimizacion/validar": () => crearResultadoCarga(),
      "POST /tableros/optimizacion/aplicar": () => crearResultadoCarga({ aplicada: true }),
    });
    fireEvent.change(campo("Resumen de la corrida"), { target: { files: [json("resumen.json", '{"a":1}')] } });
    await userEvent.click(screen.getByRole("button", { name: /Revisar archivos/ }));

    expect(await screen.findByText("Los archivos son válidos")).toBeInTheDocument();
    expect(screen.getByText("Indicadores")).toBeInTheDocument();
    expect(screen.getByText("La corrida no es publicable.")).toBeInTheDocument();
    const validar = llamadas.find((l) => l.ruta.endsWith("/validar"))!;
    expect(validar.metodo).toBe("POST");
    expect(validar.csrf).toBe("csrf-de-prueba");
    expect(validar.credenciales).toBe("include");
    const f = validar.cuerpo as FormData;
    expect(f.getAll("claves")).toEqual(["resumen"]);
    expect((f.getAll("archivos")[0] as File).name).toBe("resumen.json");

    const aplicar = screen.getByRole("button", { name: "Aplicar actualización" });
    expect(aplicar).toBeDisabled(); // hasta confirmar
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(aplicar);

    expect(await screen.findByText("Tablero actualizado")).toBeInTheDocument();
    const envio = llamadas.find((l) => l.ruta.endsWith("/aplicar"))!;
    expect((envio.cuerpo as FormData).getAll("huellas")).toEqual(["a".repeat(64)]);
    expect(envio.csrf).toBe("csrf-de-prueba");
    expect(screen.getByRole("link", { name: "Ver el tablero" })).toHaveAttribute("href", "/optimizacion");
  });

  it("si los archivos no pasan la revisión se muestran los motivos y no se ofrece aplicar", async () => {
    await entrarYElegir("Optimización", {
      "POST /tableros/optimizacion/validar": () => crearResultadoCarga({ valido: false, resumen: [], advertencias: [], errores: ["resumen.json: no es un JSON válido", "Falta el archivo obligatorio: X"] }),
    });
    fireEvent.change(campo("Resumen de la corrida"), { target: { files: [json("resumen.json", "{")] } });
    await userEvent.click(screen.getByRole("button", { name: /Revisar archivos/ }));
    expect(await screen.findByText("Hay que corregir los archivos")).toBeInTheDocument();
    expect(screen.getByText("resumen.json: no es un JSON válido")).toBeInTheDocument();
    expect(screen.getByText("2 problemas")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Aplicar actualización" })).not.toBeInTheDocument();
  });

  it("cambiar o quitar un archivo después de revisar invalida la revisión: hay que revisar de nuevo", async () => {
    await entrarYElegir("Optimización", { "POST /tableros/optimizacion/validar": () => crearResultadoCarga() });
    fireEvent.change(campo("Resumen de la corrida"), { target: { files: [json("resumen.json", '{"a":1}')] } });
    await userEvent.click(screen.getByRole("button", { name: /Revisar archivos/ }));
    await screen.findByRole("button", { name: "Aplicar actualización" });
    await userEvent.click(screen.getByRole("button", { name: /Quitar Resumen/ }));
    expect(screen.queryByRole("button", { name: "Aplicar actualización" })).not.toBeInTheDocument();
    expect(screen.queryByText("Los archivos son válidos")).not.toBeInTheDocument();
  });

  it("una respuesta 422 de la API muestra su lista de motivos", async () => {
    await entrarYElegir("Optimización", { "POST /tableros/optimizacion/validar": () => ({ status: 422, cuerpo: { detalle: "x", errores: ["La petición debe traer un archivo por cada clave"] } }) });
    fireEvent.change(campo("Resumen de la corrida"), { target: { files: [json("resumen.json", "{}")] } });
    await userEvent.click(screen.getByRole("button", { name: /Revisar archivos/ }));
    expect(await screen.findByText("La petición debe traer un archivo por cada clave")).toBeInTheDocument();
  });

  it("si la sesión venció durante la carga vuelve al acceso con el aviso", async () => {
    await entrarYElegir("Optimización", { "POST /tableros/optimizacion/validar": () => sinSesion });
    fireEvent.change(campo("Resumen de la corrida"), { target: { files: [json("resumen.json", "{}")] } });
    await userEvent.click(screen.getByRole("button", { name: /Revisar archivos/ }));
    expect(await screen.findByText(/La sesión venció/)).toBeInTheDocument();
    expect(screen.getByRole("form", { name: "Iniciar sesión" })).toBeInTheDocument();
  });

  it("sin almacenamiento persistente avisa y no deja aplicar", async () => {
    await entrarYElegir("Optimización", { "POST /tableros/optimizacion/validar": () => crearResultadoCarga() }, crearCatalogoAdmin({ almacenamiento_persistente: false }));
    expect(screen.getByRole("alert")).toHaveTextContent("no tiene almacenamiento persistente");
    fireEvent.change(campo("Resumen de la corrida"), { target: { files: [json("resumen.json", "{}")] } });
    await userEvent.click(screen.getByRole("button", { name: /Revisar archivos/ }));
    await userEvent.click(await screen.findByRole("checkbox"));
    expect(screen.getByRole("button", { name: "Aplicar actualización" })).toBeDisabled();
  });

  it("los archivos que pesan más que el tope se avisan en el campo", async () => {
    await entrarYElegir("Gas", {}, crearCatalogoAdmin({ limite_bytes: 10 }));
    fireEvent.change(campo("Pronóstico v2"), { target: { files: [new File(["x".repeat(50)], "g.xlsx")] } });
    expect(await screen.findByRole("alert")).toHaveTextContent(/máximo es/);
  });
});

describe("Bitácora", () => {
  it("el administrador ve la bitácora con las acciones en español", async () => {
    await entrarYElegir("Gas");
    const tabla = await screen.findByRole("table");
    expect(within(tabla).getByText("Actualización")).toBeInTheDocument();
    expect(within(tabla).getByText("Inicio de sesión")).toBeInTheDocument();
  });

  it("el cargador no pide ni ve la bitácora", async () => {
    const llamadas = await entrarYElegir("Gas", {}, crearCatalogoAdmin(), "cargador");
    await waitFor(() => expect(screen.getByText("2. Carga los archivos")).toBeInTheDocument());
    expect(screen.queryByText("Bitácora")).not.toBeInTheDocument();
    expect(llamadas.some((l) => l.ruta.startsWith("/auditoria"))).toBe(false);
  });
});
