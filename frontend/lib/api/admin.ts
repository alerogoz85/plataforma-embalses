import { ApiError, BASE_URL } from "./client";
import type { CatalogoActualizacion, RegistroAuditoria, ResultadoCarga, SesionAdmin } from "./types";

/**
 * Cliente del módulo de actualización. A diferencia del resto de la API (solo lectura, sin credenciales), aquí:
 * - las peticiones llevan la cookie de sesión (`credentials: "include"`; la cookie es HttpOnly, el JavaScript no la lee);
 * - las que escriben llevan el token CSRF que entregó el inicio de sesión (encabezado X-CSRF-Token);
 * - el cuerpo de un error puede traer la lista de motivos (`errores`).
 */
export class ErrorAdmin extends ApiError {
  constructor(message: string, status: number, public readonly errores: string[] = []) {
    super(message, status);
    this.name = "ErrorAdmin";
  }
}

async function pedir<T>(ruta: string, init: RequestInit & { csrf?: string } = {}): Promise<T> {
  const { csrf, headers, ...resto } = init;
  const respuesta = await fetch(`${BASE_URL}/api/v1/admin${ruta}`, {
    ...resto,
    credentials: "include",
    headers: { ...(csrf ? { "X-CSRF-Token": csrf } : {}), ...headers },
  });
  if (respuesta.status === 204) return undefined as T;
  const cuerpo: unknown = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const c = (cuerpo ?? {}) as { detalle?: unknown; detail?: unknown; errores?: unknown };
    const mensaje = typeof c.detalle === "string" ? c.detalle : typeof c.detail === "string" ? c.detail : respuesta.statusText;
    const errores = Array.isArray(c.errores) ? c.errores.filter((e): e is string => typeof e === "string") : [];
    throw new ErrorAdmin(mensaje, respuesta.status, errores);
  }
  return cuerpo as T;
}

export const iniciarSesion = (usuario: string, contrasena: string) =>
  pedir<SesionAdmin>("/sesion", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ usuario, contrasena }) });

export const obtenerSesion = (signal?: AbortSignal) => pedir<SesionAdmin>("/sesion", { signal });

export const cerrarSesion = (csrf: string) => pedir<void>("/sesion", { method: "DELETE", csrf });

export const obtenerTablerosActualizables = (signal?: AbortSignal) => pedir<CatalogoActualizacion>("/tableros", { signal });

export const obtenerAuditoria = (limite = 50, signal?: AbortSignal) => pedir<RegistroAuditoria[]>(`/auditoria?limite=${limite}`, { signal });

export interface ArchivoParaEnviar {
  clave: string;
  archivo: File;
}

function formulario(archivos: ArchivoParaEnviar[], huellas?: Record<string, string>): FormData {
  const f = new FormData();
  for (const { clave, archivo } of archivos) {
    f.append("claves", clave);
    f.append("archivos", archivo, archivo.name);
    if (huellas) f.append("huellas", huellas[clave] ?? "");
  }
  return f;
}

export const validarCarga = (tablero: string, archivos: ArchivoParaEnviar[], csrf: string) =>
  pedir<ResultadoCarga>(`/tableros/${encodeURIComponent(tablero)}/validar`, { method: "POST", body: formulario(archivos), csrf });

export const aplicarCarga = (tablero: string, archivos: ArchivoParaEnviar[], huellas: Record<string, string>, csrf: string) =>
  pedir<ResultadoCarga>(`/tableros/${encodeURIComponent(tablero)}/aplicar`, { method: "POST", body: formulario(archivos, huellas), csrf });
