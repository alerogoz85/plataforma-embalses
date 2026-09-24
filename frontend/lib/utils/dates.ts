/** Fecha en formato YYYY-MM-DD segun el calendario local (no UTC: de noche en
 * Colombia, UTC ya esta en el dia siguiente). */
export function aISO(fecha: Date): string {
  const anio = fecha.getFullYear();
  const mes = String(fecha.getMonth() + 1).padStart(2, "0");
  const dia = String(fecha.getDate()).padStart(2, "0");
  return `${anio}-${mes}-${dia}`;
}

export function fechaHaceDias(dias: number): string {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() - dias);
  return aISO(fecha);
}

export function hoyISO(): string {
  return aISO(new Date());
}
