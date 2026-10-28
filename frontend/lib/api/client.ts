import type {
  CatalogoEscenarios,
  EscenarioApagon,
  ModoOni,
  CambioReporteDns,
  CatalogoDns,
  FichaModelo,
  CausasDns,
  ComparacionXm,
  EmbalseDetalle,
  FuenteDatos,
  InventarioMensual,
  ModeloDns,
  PatronesDns,
  ResultadosModelo,
  ResumenDns,
  SerieDns,
  ZonaDns,
  Prediccion,
  RegionResumen,
  ResumenCarbon,
  ResumenNacional,
  SendaVolumen,
  SerieCarbon,
  ValidacionCarbon,
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
  return obtenerJSON<EmbalseDetalle>(`/api/v1/embalses/${encodeURIComponent(embalseId)}${query}`, signal);
}

export function obtenerPrediccion(
  embalseId: string,
  horizonte: number,
  signal?: AbortSignal,
): Promise<Prediccion> {
  return obtenerJSON<Prediccion>(
    `/api/v1/embalses/${encodeURIComponent(embalseId)}/prediccion?horizonte=${horizonte}`,
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

// ---- Modelo de carbon termico (solo lectura; los parametros son listas cerradas que la API valida)
export function obtenerResumenCarbon(horizonteMeses: number, dias: number, signal?: AbortSignal): Promise<ResumenCarbon> {
  const query = construirQuery({ horizonte_meses: horizonteMeses, dias });
  return obtenerJSON<ResumenCarbon>(`/api/v1/carbon/resumen${query}`, signal);
}

export function obtenerSerieCarbon(historiaMeses: number, horizonteMeses: number, signal?: AbortSignal): Promise<SerieCarbon> {
  const query = construirQuery({ historia_meses: historiaMeses, horizonte_meses: horizonteMeses });
  return obtenerJSON<SerieCarbon>(`/api/v1/carbon/serie${query}`, signal);
}

export function obtenerInventarioCarbon(horizonteMeses: number, dias: number, signal?: AbortSignal): Promise<InventarioMensual[]> {
  const query = construirQuery({ horizonte_meses: horizonteMeses, dias });
  return obtenerJSON<InventarioMensual[]>(`/api/v1/carbon/inventario${query}`, signal);
}

export function obtenerComparacionXm(horizonteMeses: number, signal?: AbortSignal): Promise<ComparacionXm[]> {
  const query = construirQuery({ horizonte_meses: horizonteMeses });
  return obtenerJSON<ComparacionXm[]>(`/api/v1/carbon/comparacion-xm${query}`, signal);
}

export function obtenerValidacionCarbon(signal?: AbortSignal): Promise<ValidacionCarbon> {
  return obtenerJSON<ValidacionCarbon>("/api/v1/carbon/validacion", signal);
}

// ---- Modelo de demanda no atendida (DNS): solo lectura; periodo y origen son listas cerradas
export interface FiltrosDnsApi {
  periodoMeses: number;
  region?: string | null;
  subarea?: string | null;
  origen?: string | null;
}

const queryDns = (f: FiltrosDnsApi, conPeriodoYOrigen = true) =>
  construirQuery({
    periodo_meses: conPeriodoYOrigen ? f.periodoMeses : undefined,
    origen: conPeriodoYOrigen ? (f.origen ?? undefined) : undefined,
    region: f.region ?? undefined,
    subarea: f.subarea ?? undefined,
  });

export const obtenerCatalogoDns = (signal?: AbortSignal) => obtenerJSON<CatalogoDns>("/api/v1/dns/catalogo", signal);

export const obtenerResumenDns = (f: FiltrosDnsApi, signal?: AbortSignal) =>
  obtenerJSON<ResumenDns>(`/api/v1/dns/resumen${queryDns(f)}`, signal);

export const obtenerSerieDns = (f: FiltrosDnsApi, signal?: AbortSignal) =>
  obtenerJSON<SerieDns>(`/api/v1/dns/serie${queryDns(f)}`, signal);

export const obtenerPatronesDns = (f: FiltrosDnsApi, signal?: AbortSignal) =>
  obtenerJSON<PatronesDns>(`/api/v1/dns/patrones${queryDns(f)}`, signal);

export const obtenerCausasDns = (f: FiltrosDnsApi, signal?: AbortSignal) =>
  obtenerJSON<CausasDns>(`/api/v1/dns/causas${queryDns(f)}`, signal);

// Estos tres son resultados del modelo sobre todo el historico: solo respetan region y subarea.
export const obtenerZonasDns = (f: FiltrosDnsApi, signal?: AbortSignal) =>
  obtenerJSON<{ zonas: ZonaDns[] }>(`/api/v1/dns/zonas${queryDns(f, false)}`, signal);

export const obtenerCambiosReporteDns = (f: FiltrosDnsApi, signal?: AbortSignal) =>
  obtenerJSON<{ cambios: CambioReporteDns[] }>(`/api/v1/dns/cambios-reporte${queryDns(f, false)}`, signal);

export const obtenerModeloDns = (f: FiltrosDnsApi, signal?: AbortSignal) =>
  obtenerJSON<ModeloDns>(`/api/v1/dns/modelo${queryDns(f, false)}`, signal);

// ---- Modelos analiticos con ficha (gas, optimizacion, apagon)
export const obtenerFichaModelo = (modeloId: string, signal?: AbortSignal) =>
  obtenerJSON<FichaModelo>(`/api/v1/modelos/${encodeURIComponent(modeloId)}/ficha`, signal);

export const obtenerResultadosModelo = (modeloId: string, signal?: AbortSignal) =>
  obtenerJSON<ResultadosModelo>(`/api/v1/modelos/${encodeURIComponent(modeloId)}/resultados`, signal);

export const obtenerCatalogoEscenariosApagon = (signal?: AbortSignal) =>
  obtenerJSON<CatalogoEscenarios>("/api/v1/modelos/apagon/escenarios", signal);

export interface ParametrosEscenario {
  modo: ModoOni;
  /** Solo en modo manual: en modo probabilístico el modelo usa el pronóstico ENOS y el ONI no interviene. */
  oni: number;
  simulaciones: number;
  horizonte: number;
}

export const obtenerEscenarioApagon = (p: ParametrosEscenario, signal?: AbortSignal) =>
  obtenerJSON<EscenarioApagon>(
    `/api/v1/modelos/apagon/escenario${construirQuery({ modo: p.modo, oni: p.modo === "manual" ? p.oni : undefined, simulaciones: p.simulaciones, horizonte: p.horizonte })}`,
    signal,
  );

export function urlReporte(embalseId: string, formato: "csv" | "json", rango: { fechaInicio?: string; fechaFin?: string } = {}): string {
  const query = construirQuery({
    formato,
    fecha_inicio: rango.fechaInicio,
    fecha_fin: rango.fechaFin,
  });
  return `${BASE_URL}/api/v1/embalses/${embalseId}/reporte${query}`;
}
