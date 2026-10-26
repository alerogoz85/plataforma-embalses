import type { Page } from "@playwright/test";

import { FUENTE_REAL, crearDetalle, crearPrediccion, crearResumen, crearSenda } from "../tests/fixtures";
import { crearComparacionXm, crearInventario, crearResumenCarbon, crearSerieCarbon, crearValidacionCarbon } from "../tests/carbon/fixturesCarbon";

/** Peticiones a la API que hizo la pagina (ruta + parametros), en orden. */
export type Llamadas = URL[];

/**
 * Simula toda la API en el navegador con los mismos datos de ejemplo de las pruebas unitarias.
 * Devuelve la lista (viva) de llamadas para poder comprobar que cada filtro consulta lo correcto.
 */
export async function simularApi(page: Page): Promise<Llamadas> {
  const llamadas: Llamadas = [];
  await page.route("**/api/v1/**", async (ruta) => {
    const url = new URL(ruta.request().url());
    llamadas.push(url);
    const p = url.pathname.replace("/api/v1", "");
    const json = (cuerpo: unknown) => ruta.fulfill({ json: cuerpo, headers: { "access-control-allow-origin": "*" } });

    if (p === "/fuente-datos") return json(FUENTE_REAL);
    if (p === "/embalses/resumen") return json(crearResumen());
    if (p === "/senda-volumen") return json(crearSenda());
    if (/^\/embalses\/[^/]+\/prediccion$/.test(p)) return json(crearPrediccion(6));
    if (/^\/embalses\/[^/]+$/.test(p)) return json(crearDetalle(12));
    if (p === "/carbon/resumen") return json(crearResumenCarbon());
    if (p === "/carbon/serie") return json(crearSerieCarbon());
    if (p === "/carbon/inventario") return json(crearInventario());
    if (p === "/carbon/comparacion-xm") return json(crearComparacionXm());
    if (p === "/carbon/validacion") return json(crearValidacionCarbon());
    return ruta.fulfill({ status: 404, json: { detalle: `sin simulacion para ${p}` } });
  });
  return llamadas;
}
