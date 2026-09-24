import type {
  EmbalseDetalle,
  FuenteDatos,
  Prediccion,
  RegionResumen,
  ResumenNacional,
  SendaVolumen,
} from "./types";

// En desarrollo apunta al backend local. En produccion se define "/" para llamar
// a la misma URL del sitio (Next reescribe /api/v1/* hacia la API, ver next.config.ts).
export const BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Los errores de dominio llegan como {detalle} y los de validacion de FastAPI como {detail}.
function extraerMensaje(cuerpo: unknown): string | null {
  if (typeof cuerpo !== "object" || cuerpo === null) return null;
  const { detalle, detail } = cuerpo as { detalle?: unknown; detail?: unknown };
  if (typeof detalle === "string") return detalle;
  if (typeof detail === "string") return detail;
  return null;
}

async function obtenerJSON<T>(ruta: string, signal?: AbortSignal): Promise<T> {
  const respuesta = await fetch(`${BASE_URL}${ruta}`, { signal });
  if (!respuesta.ok) {
    const cuerpo = await respuesta.json().catch(() => null);
    throw new ApiError(extraerMensaje(cuerpo) ?? respuesta.statusText, respuesta.status);
  }
  return respuesta.json() as Promise<T>;
}

function construirQuery(parametros: Record<string, string | number | string[] | undefined>): string {
  const query = new URLSearchParams();
  for (const [clave, valor] of Object.entries(parametros)) {
    if (valor === undefined || valor === "") continue;
    if (Array.isArray(valor)) {
      valor.forEach((v) => query.append(clave, v));
    } else {
      query.append(clave, String(valor));
    }
  }
  const texto = query.toString();
  return texto ? `?${texto}` : "";
}

export interface FiltrosResumen {
  regiones?: string[];
  embalses?: string[];
  fecha?: string;
}

export function obtenerResumenNacional(
  filtros: FiltrosResumen = {},
  signal?: AbortSignal,
): Promise<ResumenNacional> {
  const query = construirQuery({ region: filtros.regiones, embalse: filtros.embalses, fecha: filtros.fecha });
  return obtenerJSON<ResumenNacional>(`/api/v1/embalses/resumen${query}`, signal);
}

export function obtenerRegiones(signal?: AbortSignal): Promise<RegionResumen[]> {
  return obtenerJSON<RegionResumen[]>("/api/v1/regiones", signal);
}

export function obtenerDetalleEmbalse(
  embalseId: string,
  rango: { fechaInicio?: string; fechaFin?: string } = {},
  signal?: AbortSignal,
): Promise<EmbalseDetalle> {
  const query = construirQuery({ fecha_inicio: rango.fechaInicio, fecha_fin: rango.fechaFin });
  return obtenerJSON<EmbalseDetalle>(`/api/v1/embalses/${embalseId}${query}`, signal);
}

export function obtenerPrediccion(
  embalseId: string,
  horizonte: number,
  signal?: AbortSignal,
): Promise<Prediccion> {
  return obtenerJSON<Prediccion>(
    `/api/v1/embalses/${embalseId}/prediccion?horizonte=${horizonte}`,
    signal,
  );
}

export function obtenerFuenteDatos(signal?: AbortSignal): Promise<FuenteDatos> {
  return obtenerJSON<FuenteDatos>("/api/v1/fuente-datos", signal);
}

export function obtenerSendaVolumen(
  embalseId: string,
  horizonteMeses: number,
  signal?: AbortSignal,
): Promise<SendaVolumen> {
  const query = construirQuery({ embalse: embalseId, horizonte_meses: horizonteMeses });
  return obtenerJSON<SendaVolumen>(`/api/v1/senda-volumen${query}`, signal);
}

export function urlReporte(embalseId: string, formato: "csv" | "json", rango: { fechaInicio?: string; fechaFin?: string } = {}): string {
  const query = construirQuery({
    formato,
    fecha_inicio: rango.fechaInicio,
    fecha_fin: rango.fechaFin,
  });
  return `${BASE_URL}/api/v1/embalses/${embalseId}/reporte${query}`;
}
