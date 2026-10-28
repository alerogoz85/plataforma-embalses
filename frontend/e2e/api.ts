import type { Page } from "@playwright/test";

import { FUENTE_REAL, crearDetalle, crearPrediccion, crearResumen, crearSenda } from "../tests/fixtures";
import { crearCatalogo, crearEscenario } from "../tests/apagon/fixturesEscenario";
import { crearAuditoria, crearCatalogoAdmin, crearResultadoCarga, crearSesion } from "../tests/actualizacion/fixturesAdmin";
import { conResultados, crearFichaModelo, sinResultados } from "../tests/modelos/fixturesModelos";
import {
  crearCambiosDns, crearCatalogoDns, crearCausasDns, crearModeloDns, crearPatronesDns, crearResumenDns, crearSerieDns, crearZonasDns,
} from "../tests/dns/fixturesDns";
import { crearComparacionXm, crearInventario, crearResumenCarbon, crearSerieCarbon, crearValidacionCarbon } from "../tests/carbon/fixturesCarbon";

/** Peticiones a la API que hizo la pagina (ruta + parametros), en orden. */
export type Llamadas = URL[];

/**
 * Simula toda la API en el navegador con los mismos datos de ejemplo de las pruebas unitarias.
 * Devuelve la lista (viva) de llamadas para poder comprobar que cada filtro consulta lo correcto.
 */
/** `resultados` permite simular que un modelo analitico (gas, optimizacion, apagon) ya tiene resultados importados. */
export async function simularApi(
  page: Page, resultados: Partial<Record<string, ReturnType<typeof conResultados>>> = {}, { escenariosApagon = false }: { escenariosApagon?: boolean } = {},
): Promise<Llamadas> {
  const llamadas: Llamadas = [];
  let sesionAdmin = false;
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
    if (p === "/dns/catalogo") return json(crearCatalogoDns());
    if (p === "/dns/resumen") return json(crearResumenDns());
    if (p === "/dns/serie") return json(crearSerieDns());
    if (p === "/dns/zonas") return json(crearZonasDns());
    if (p === "/dns/patrones") return json(crearPatronesDns());
    if (p === "/dns/causas") return json(crearCausasDns());
    if (p === "/dns/cambios-reporte") return json(crearCambiosDns());
    if (p === "/dns/modelo") return json(crearModeloDns());
    // Módulo de actualización: la sesión empieza cerrada y se abre con el inicio de sesión (la simulación mantiene ese estado).
    // Con credenciales (cookie) el navegador exige un origen concreto y «allow-credentials», no «*».
    if (p.startsWith("/admin/")) {
      const metodo = ruta.request().method();
      const cabeceras = {
        "access-control-allow-origin": ruta.request().headers()["origin"] ?? "*", "access-control-allow-credentials": "true",
        "access-control-allow-headers": "Content-Type, X-CSRF-Token", "access-control-allow-methods": "GET, POST, DELETE",
      };
      const responder = (status: number, cuerpo?: unknown) => ruta.fulfill({ status, headers: cabeceras, ...(cuerpo === undefined ? {} : { json: cuerpo }) });
      if (metodo === "OPTIONS") return responder(204);
      if (p === "/admin/sesion" && metodo === "POST") {
        const { contrasena } = ruta.request().postDataJSON() as { contrasena: string };
        if (contrasena !== "clave-correcta-2026") return responder(401, { detalle: "Usuario o contraseña incorrectos" });
        sesionAdmin = true;
        return responder(200, crearSesion());
      }
      if (!sesionAdmin) return responder(401, { detalle: "Debes iniciar sesión para continuar" });
      if (p === "/admin/sesion" && metodo === "DELETE") { sesionAdmin = false; return responder(204); }
      if (p === "/admin/sesion") return responder(200, crearSesion());
      if (p === "/admin/tableros") return responder(200, crearCatalogoAdmin());
      if (p === "/admin/auditoria") return responder(200, crearAuditoria());
      if (p.endsWith("/validar")) return responder(200, crearResultadoCarga());
      if (p.endsWith("/aplicar")) return responder(200, crearResultadoCarga({ aplicada: true }));
    }
    // Visor de apagón: solo con `escenariosApagon`; sin él el catálogo dice «no disponible» y queda el tablero genérico.
    if (p === "/modelos/apagon/escenarios") return json(crearCatalogo({ disponible: escenariosApagon }));
    if (p === "/modelos/apagon/escenario" && escenariosApagon) {
      const q = url.searchParams;
      return json(crearEscenario({ modo: q.get("modo") as "manual", oni: Number(q.get("oni") ?? 1), simulaciones: Number(q.get("simulaciones")), horizonte: Number(q.get("horizonte")) }));
    }
    const modelo = /^\/modelos\/([a-z]+)\/(ficha|resultados)$/.exec(p);
    if (modelo) {
      const [, id, recurso] = modelo;
      return json(recurso === "ficha" ? crearFichaModelo({ id: id as never, estado: resultados[id] ? "con_resultados" : "sin_resultados" }) : (resultados[id] ?? sinResultados(id as never)));
    }
    return ruta.fulfill({ status: 404, json: { detalle: `sin simulacion para ${p}` } });
  });
  return llamadas;
}
