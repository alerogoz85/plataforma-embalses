/**
 * Lectores de parámetros de URL. La dirección la puede escribir cualquiera, así que todo valor se valida:
 * un parámetro inválido NO falla ni se propaga a la API, simplemente se ignora (queda el valor por defecto).
 * Cada lector recibe el texto crudo y devuelve el valor ya tipado, o `undefined` si no es válido.
 */

/** Un valor de una lista cerrada (los mismos que acepta la API), p. ej. períodos o horizontes. */
export function enLista<T extends string | number>(permitidos: readonly T[]): (crudo: string) => T | undefined {
  return (crudo) => permitidos.find((p) => String(p) === crudo);
}

/** Fecha AAAA-MM-DD que existe en el calendario. */
export function fechaIso(crudo: string): string | undefined {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(crudo)) return undefined;
  const fecha = new Date(`${crudo}T00:00:00Z`);
  return !Number.isNaN(fecha.getTime()) && fecha.toISOString().slice(0, 10) === crudo ? crudo : undefined;
}

/** Mes AAAA-MM con mes entre 01 y 12. */
export function mesIso(crudo: string): string | undefined {
  return /^\d{4}-(0[1-9]|1[0-2])$/.test(crudo) ? crudo : undefined;
}

/** Texto corto de letras, números, espacios, guion y guion bajo (códigos y nombres, nunca marcado ni caracteres de control). */
export function codigo(maximo = 40): (crudo: string) => string | undefined {
  const patron = new RegExp(`^[\\p{L}\\p{N} _-]{1,${maximo}}$`, "u");
  return (crudo) => (patron.test(crudo) ? crudo : undefined);
}

/** Texto libre acotado (búsquedas): se recorta y se limita su largo; vacío cuenta como ausente. */
export function textoLibre(maximo = 60): (crudo: string) => string | undefined {
  return (crudo) => {
    const limpio = crudo.replace(/[\u0000-\u001f\u007f]/g, "").trim().slice(0, maximo);
    return limpio || undefined;
  };
}
