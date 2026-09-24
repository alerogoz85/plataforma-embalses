import { REGIONES, type EmbalseResumen, type FuenteDatos, type ResumenNacional } from "@/lib/api/types";
import {
  EMBALSES_EJEMPLO,
  FUENTE_REAL,
  KPIS_EJEMPLO,
  REGIONES_EJEMPLO,
  crearDetalle,
  crearEmbalse,
  crearPrediccion,
  crearSenda,
} from "../fixtures";
import { simularFetch } from "../mocks/fetch";

interface Opciones {
  embalses?: EmbalseResumen[];
  fuente?: FuenteDatos;
  kpis?: Partial<ResumenNacional["kpis"]>;
}

/** Simula toda la API que consume la pagina; el resumen respeta el filtro de region. */
export function simularApi({ embalses = EMBALSES_EJEMPLO, fuente = FUENTE_REAL, kpis = {} }: Opciones = {}) {
  const rutas: Parameters<typeof simularFetch>[0] = {
    "/api/v1/fuente-datos": () => fuente,
    "/api/v1/senda-volumen": (url) => crearSenda({ embalse_id: url.searchParams.get("embalse")! }),
    "/api/v1/embalses/resumen": (url) => {
      const regiones = url.searchParams.getAll("region");
      const filtrados = regiones.length ? embalses.filter((e) => regiones.includes(e.region)) : embalses;
      return {
        kpis: { ...KPIS_EJEMPLO, total_embalses: filtrados.length, ...kpis },
        regiones: REGIONES_EJEMPLO,
        embalses: filtrados,
      } satisfies ResumenNacional;
    },
  };
  // "Todos los embalses": el total nacional y el agregado de cada region.
  const agregados = [
    { id: "TOTAL", nombre: "Total nacional" },
    ...REGIONES.map((region) => ({ id: encodeURIComponent(`REGION:${region}`), nombre: `Región ${region}` })),
  ];
  for (const { id, nombre } of agregados) {
    rutas[`/api/v1/embalses/${id}`] = () => ({
      ...crearDetalle(5),
      resumen: crearEmbalse({ id: decodeURIComponent(id), nombre, es_agregado: true }),
    });
    rutas[`/api/v1/embalses/${id}/prediccion`] = () => ({ ...crearPrediccion(3), embalse_id: decodeURIComponent(id) });
  }
  for (const embalse of embalses) {
    rutas[`/api/v1/embalses/${embalse.id}`] = () => ({ ...crearDetalle(5), resumen: crearEmbalse(embalse) });
    rutas[`/api/v1/embalses/${embalse.id}/prediccion`] = () => ({ ...crearPrediccion(3), embalse_id: embalse.id });
  }
  return simularFetch(rutas);
}
