/**
 * Manejador central de rutas de la aplicación.
 *
 * Es la ÚNICA fuente de verdad de las direcciones: ningún componente escribe una ruta a mano. De aquí salen
 * - las rutas de cada tablero y sus enlaces a la guía (panel, encabezado, pruebas),
 * - los alias que redirigen a la ruta canónica (los usa `next.config.ts`),
 * - la construcción de URLs con parámetros (`conParametros`) para que cada vista y cada filtro tenga dirección propia.
 *
 * Es solo datos y funciones puras: no importa React ni Next, para poder usarse también en la configuración.
 */

export const RUTAS = {
  panel: "/",
  informacion: "/informacion",
  embalses: "/embalses",
  carbon: "/carbon",
  dns: "/dns",
  gas: "/gas",
  optimizacion: "/optimizacion",
  apagon: "/apagon",
} as const;

export type IdTablero = Exclude<keyof typeof RUTAS, "panel" | "informacion">;
export type Ruta = (typeof RUTAS)[keyof typeof RUTAS];

/** Tableros en el orden en que se muestran. */
export const IDS_TABLERO: readonly IdTablero[] = ["embalses", "carbon", "dns", "gas", "optimizacion", "apagon"];

/** Capítulo de la guía (`/informacion#ancla`) donde se explica cada tablero. */
export const ANCLAS_GUIA: Record<IdTablero | "panel", string> = {
  panel: "panel",
  embalses: "mapa",
  carbon: "carbon-mapa",
  dns: "dns-mapa",
  gas: "modelos",
  optimizacion: "modelos",
  apagon: "modelos",
};

/** Direcciones alternativas que se redirigen a la ruta canónica (nombres que alguien podría escribir a mano). */
export const ALIAS_DE_RUTAS: Readonly<Record<string, Ruta>> = {
  "/tableros": RUTAS.panel,
  "/inicio": RUTAS.panel,
  "/embalse": RUTAS.embalses,
  "/carbon-termico": RUTAS.carbon,
  "/demanda-no-atendida": RUTAS.dns,
  "/gas-natural": RUTAS.gas,
  "/optimizacion-hidrotermica": RUTAS.optimizacion,
  "/riesgo-apagon": RUTAS.apagon,
  "/guia": RUTAS.informacion,
};

export const rutaDe = (id: IdTablero): Ruta => RUTAS[id];

/** `/informacion#ancla` del capítulo de un tablero (o del panel). */
export const urlGuia = (id: IdTablero | "panel"): string => `${RUTAS.informacion}#${ANCLAS_GUIA[id]}`;

export type ValorParametro = string | number | boolean | null | undefined;

/**
 * Ruta + parámetros de consulta. Omite los valores nulos, indefinidos y vacíos para que las direcciones queden cortas
 * (un filtro en su valor por defecto no aparece en la URL). Las claves se ordenan para que la misma vista tenga siempre la misma URL.
 */
export function conParametros(ruta: string, parametros: Record<string, ValorParametro>): string {
  const query = new URLSearchParams();
  for (const clave of Object.keys(parametros).sort()) {
    const valor = parametros[clave];
    if (valor === null || valor === undefined || valor === "") continue;
    query.set(clave, String(valor));
  }
  const texto = query.toString();
  return texto ? `${ruta}?${texto}` : ruta;
}

const CONOCIDAS = new Set<string>(Object.values(RUTAS));

/** ¿La ruta (sin parámetros ni ancla, con o sin barra final) es una de las canónicas de la aplicación? */
export function esRutaConocida(ruta: string): boolean {
  const limpia = ruta.split(/[?#]/)[0].replace(/\/+$/, "") || "/";
  return CONOCIDAS.has(limpia);
}

/** Ruta canónica para una dirección escrita a mano (alias, mayúsculas, barra final); `null` si no corresponde a nada. */
export function resolverRuta(ruta: string): Ruta | null {
  const limpia = (ruta.split(/[?#]/)[0].replace(/\/+$/, "") || "/").toLowerCase();
  const canonica = Object.values(RUTAS).find((r) => r === limpia);
  return canonica ?? ALIAS_DE_RUTAS[limpia] ?? null;
}
