"use client";

import {
  obtenerCambiosReporteDns,
  obtenerCatalogoDns,
  obtenerCausasDns,
  obtenerModeloDns,
  obtenerPatronesDns,
  obtenerResumenDns,
  obtenerSerieDns,
  obtenerZonasDns,
  type FiltrosDnsApi,
} from "@/lib/api/client";
import { useAsyncResource } from "./useAsyncResource";

/**
 * Un hook por endpoint del tablero DNS. Cada uno vuelve a consultar solo cuando cambia un filtro
 * del que depende: los de eventos usan los cuatro filtros; zonas, cambios y modelo solo región/subárea.
 */
export const useCatalogoDns = () => useAsyncResource((s) => obtenerCatalogoDns(s), []);

export const useResumenDns = (f: FiltrosDnsApi) =>
  useAsyncResource((s) => obtenerResumenDns(f, s), [f.periodoMeses, f.region, f.subarea, f.origen]);

export const useSerieDns = (f: FiltrosDnsApi) =>
  useAsyncResource((s) => obtenerSerieDns(f, s), [f.periodoMeses, f.region, f.subarea, f.origen]);

export const usePatronesDns = (f: FiltrosDnsApi) =>
  useAsyncResource((s) => obtenerPatronesDns(f, s), [f.periodoMeses, f.region, f.subarea, f.origen]);

export const useCausasDns = (f: FiltrosDnsApi) =>
  useAsyncResource((s) => obtenerCausasDns(f, s), [f.periodoMeses, f.region, f.subarea, f.origen]);

export const useZonasDns = (f: FiltrosDnsApi) =>
  useAsyncResource((s) => obtenerZonasDns(f, s), [f.region, f.subarea]);

export const useCambiosReporteDns = (f: FiltrosDnsApi) =>
  useAsyncResource((s) => obtenerCambiosReporteDns(f, s), [f.region, f.subarea]);

export const useModeloDns = (f: FiltrosDnsApi) =>
  useAsyncResource((s) => obtenerModeloDns(f, s), [f.region, f.subarea]);
