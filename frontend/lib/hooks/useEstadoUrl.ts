"use client";

import { usePathname, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

/**
 * Estado de una vista guardado en la dirección (URL): cada filtro y cada alternancia tiene su parámetro, así que
 * la vista exacta se puede copiar, compartir, recargar y recorrer con «atrás/adelante».
 *
 * Reglas:
 * - Se lee con validación: un valor ausente o inválido da el valor por defecto (nunca un error ni un valor sin validar).
 * - Se escribe solo lo que difiere del valor por defecto, para que las direcciones queden cortas.
 * - Un cambio reemplaza la entrada del historial (no la apila): cada clic en un filtro no llena el botón «atrás».
 * - Se escribe con `window.history.replaceState`, la vía que documenta Next para sincronizar la URL con `useSearchParams`:
 *   no hay viaje al servidor en cada cambio (importa en la búsqueda de la tabla, que cambia con cada tecla).
 */
export interface CampoUrl<T> {
  /** Nombre del parámetro en la URL. */
  param: string;
  /** Valor por defecto; es función porque algunos dependen de la fecha de hoy. */
  defecto: () => T;
  /** Convierte el texto de la URL en el valor; `undefined` si no es válido. */
  leer: (crudo: string) => T | undefined;
  /** Convierte el valor en texto de la URL (por defecto, `String`). */
  escribir?: (valor: T) => string;
}

export type EsquemaUrl<E> = { [K in keyof E]: CampoUrl<E[K]> };

export interface AccionesUrl<E> {
  /** Cambia uno o varios campos a la vez (una sola navegación). */
  actualizar: (cambios: Partial<E>) => void;
  /** Vuelve todos los campos de este esquema a su valor por defecto (los parámetros de otros esquemas se conservan). */
  restablecer: () => void;
}

/** Lee el estado del esquema desde unos parámetros de URL (función pura, también usada en las pruebas). */
export function leerEstado<E>(esquema: EsquemaUrl<E>, parametros: URLSearchParams): E {
  const estado = {} as E;
  for (const clave of Object.keys(esquema) as (keyof E)[]) {
    const campo = esquema[clave];
    const crudo = parametros.get(campo.param);
    const valor = crudo === null ? undefined : campo.leer(crudo);
    estado[clave] = valor === undefined ? campo.defecto() : valor;
  }
  return estado;
}

/** Aplica un estado sobre unos parámetros: escribe lo que difiere del defecto y quita lo demás. Conserva el resto de parámetros. */
export function escribirEstado<E>(esquema: EsquemaUrl<E>, estado: E, base: URLSearchParams): URLSearchParams {
  const salida = new URLSearchParams(base);
  for (const clave of Object.keys(esquema) as (keyof E)[]) {
    const campo = esquema[clave];
    const valor = estado[clave];
    const texto = campo.escribir ? campo.escribir(valor) : String(valor ?? "");
    const textoDefecto = campo.escribir ? campo.escribir(campo.defecto()) : String(campo.defecto() ?? "");
    if (valor === null || valor === undefined || texto === "" || texto === textoDefecto) salida.delete(campo.param);
    else salida.set(campo.param, texto);
  }
  return salida;
}

export function useEstadoUrl<E>(esquema: EsquemaUrl<E>): [E, AccionesUrl<E>] {
  const parametros = useSearchParams();
  const pathname = usePathname();

  const texto = parametros?.toString() ?? "";
  const estado = useMemo(() => leerEstado(esquema, new URLSearchParams(texto)), [esquema, texto]);

  // `replaceState` cambia `window.location` al instante, así que dos cambios seguidos en el mismo evento (p. ej. región +
  // embalse) se componen solos sobre la URL ya modificada; no hace falta guardar nada en un ref.
  const navegar = useCallback(
    (cambios: Partial<E>) => {
      const actual = new URLSearchParams(window.location.search);
      const nuevo = { ...leerEstado(esquema, actual), ...cambios };
      const query = escribirEstado(esquema, nuevo, actual).toString();
      window.history.replaceState(null, "", query ? `${pathname}?${query}` : pathname);
    },
    [esquema, pathname],
  );

  const restablecer = useCallback(() => navegar(leerEstado(esquema, new URLSearchParams())), [esquema, navegar]);

  return [estado, { actualizar: navegar, restablecer }];
}
