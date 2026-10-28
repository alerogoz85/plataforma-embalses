/** Utilidades de los archivos que se suben en el módulo de actualización (puras, salvo la compresión, que usa el navegador). */

const UNIDADES = ["B", "KB", "MB", "GB"];

export function formatearTamano(bytes: number): string {
  let valor = bytes;
  let unidad = 0;
  while (valor >= 1024 && unidad < UNIDADES.length - 1) {
    valor /= 1024;
    unidad += 1;
  }
  return `${unidad === 0 ? valor : valor.toFixed(1).replace(".", ",")} ${UNIDADES[unidad]}`;
}

export const extensionDe = (nombre: string): string => (nombre.includes(".") ? nombre.split(".").pop()!.toLowerCase() : "");

/** Valor del atributo `accept` de un campo de archivo según los formatos del tablero. */
export const aceptarDe = (formatos: string[]): string => formatos.map((f) => `.${f}`).join(",");

/** Formatos de texto que se pueden comprimir antes de enviarlos (xlsx y parquet ya vienen comprimidos). */
export const COMPRIMIBLES = ["csv", "json"];

/**
 * Los CSV/JSON grandes se envían en .gz para que quepan en el límite de una petición (los eventos del modelo DNS pesan ~6 MB y el tope
 * es 4,4 MB). La API los descomprime con tope de tamaño y los trata como el archivo original. Sin `CompressionStream` (navegadores
 * viejos) se envía tal cual y la API avisa si no cabe.
 */
export async function comprimirSiHaceFalta(archivo: File, umbral: number): Promise<File> {
  if (archivo.size <= umbral || !COMPRIMIBLES.includes(extensionDe(archivo.name)) || typeof CompressionStream === "undefined") return archivo;
  const flujo = archivo.stream().pipeThrough(new CompressionStream("gzip"));
  const datos = await new Response(flujo).blob();
  return new File([datos], `${archivo.name}.gz`, { type: "application/gzip" });
}

/** Fecha y hora de la bitácora (llegan en UTC con «Z») en la zona del navegador. */
export function formatearMomento(iso: string): string {
  return new Intl.DateTimeFormat("es-CO", { dateStyle: "short", timeStyle: "medium" }).format(new Date(iso));
}
