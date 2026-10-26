/**
 * Registro de tableros de la plataforma.
 *
 * El panel principal (app/page.tsx) se arma recorriendo esta lista, así que para sumar un tablero nuevo basta con
 * crear su carpeta en `app/<ruta>/`, registrar su ruta en `lib/rutas.ts` y agregar aquí una entrada.
 * Es solo información de presentación: ningún dato sensible ni de negocio vive aquí.
 *
 * Redacción de las tarjetas: la descripción responde «qué puedo ver aquí» en una frase; las etiquetas son 3 temas
 * concretos (no repiten el título); la fuente va corta y dice de dónde salen los datos.
 */
import { RUTAS, urlGuia, type IdTablero, type Ruta } from "@/lib/rutas";

export type IconoTablero = IdTablero;

/** `datos`: el tablero ya muestra resultados reales. `desarrollo`: muestra su ficha y estado hasta que el modelo entregue resultados. */
export type GrupoTablero = "datos" | "desarrollo";

export interface Tablero {
  /** Identificador estable (se usa como clave y en las pruebas). */
  id: IdTablero;
  /** Ruta canónica (sale de `lib/rutas.ts`). */
  ruta: Ruta;
  titulo: string;
  descripcion: string;
  /** De dónde salen los datos que muestra (corto). */
  fuente: string;
  /** Tres temas concretos que se pueden consultar (se muestran como etiquetas). */
  incluye: readonly string[];
  icono: IconoTablero;
  grupo: GrupoTablero;
  /** Capítulo de la guía donde se explica este tablero. */
  guia: string;
}

export const GRUPOS: Record<GrupoTablero, { titulo: string; descripcion: string }> = {
  datos: {
    titulo: "Tableros con datos",
    descripcion: "Muestran información real y actualizable, con filtros y su fecha de corte.",
  },
  desarrollo: {
    titulo: "Modelos en desarrollo",
    descripcion:
      "Aún no tienen resultados finales: muestran su ficha, su estado real y cómo cargar los resultados cuando el modelo los entregue.",
  },
};

export const TABLEROS: readonly Tablero[] = [
  {
    id: "embalses",
    ruta: RUTAS.embalses,
    titulo: "Embalses",
    descripcion: "Volumen útil, aportes y riesgo de los 24 embalses del SIN, con pronóstico a 1, 3, 6 y 12 meses.",
    fuente: "XM y SIMEM · modelo de largo plazo con escenarios El Niño/La Niña",
    incluye: ["Volumen por región", "Riesgo en 5 niveles", "Reportes CSV y JSON"],
    icono: "embalses",
    grupo: "datos",
    guia: urlGuia("embalses"),
  },
  {
    id: "carbon",
    ruta: RUTAS.carbon,
    titulo: "Carbón térmico",
    descripcion: "Consumo de carbón de las térmicas durante El Niño 2026-2027, con inventario requerido y comparación con XM.",
    fuente: "Modelo de carbón térmico · Sinergox, SIMEM y NOAA",
    incluye: ["Escenarios P10 a P90", "Uso del techo físico", "Inventario en días"],
    icono: "carbon",
    grupo: "datos",
    guia: urlGuia("carbon"),
  },
  {
    id: "dns",
    ruta: RUTAS.dns,
    titulo: "Demanda no atendida",
    descripcion: "Eventos de demanda no atendida por subárea desde 2013: dónde, cuándo y por qué ocurren, y el pronóstico del mes siguiente.",
    fuente: "SIMEM (eventos DNS y EDAC) · modelo del Ministerio",
    incluye: ["Zonas prioritarias", "Patrones por hora y día", "Causas de los eventos"],
    icono: "dns",
    grupo: "datos",
    guia: urlGuia("dns"),
  },
  {
    id: "gas",
    ruta: RUTAS.gas,
    titulo: "Gas natural",
    descripcion: "Oferta de gas declarada al Ministerio frente al gas fiscalizado por la ANH, por campo, con curvas de declinación.",
    fuente: "Declaraciones del MME y producción fiscalizada de la ANH",
    incluye: ["Qué compara y cómo", "Datos y limitaciones", "Cómo cargar resultados"],
    icono: "gas",
    grupo: "desarrollo",
    guia: urlGuia("gas"),
  },
  {
    id: "optimizacion",
    ruta: RUTAS.optimizacion,
    titulo: "Optimización hidrotérmica",
    descripcion: "Planeación hidro-térmica con SDDP y riesgo CVaR bajo escenarios ENOS: cuánta térmica usar y qué costo y riesgo implica.",
    fuente: "Documentos de modelamiento y evaluación del producto SDDP",
    incluye: ["Método SDDP y CVaR", "Estado de la evidencia", "Limitaciones"],
    icono: "optimizacion",
    grupo: "desarrollo",
    guia: urlGuia("optimizacion"),
  },
  {
    id: "apagon",
    ruta: RUTAS.apagon,
    titulo: "Riesgo de apagón",
    descripcion: "Riesgo mensual de déficit de generación del SIN condicionado por ENOS: probabilidad, margen de reserva y semáforo.",
    fuente: "Modelo Monte Carlo · NOAA/CPC, UPME y datos del sector",
    incluye: ["Semáforo mensual", "Probabilidad de déficit", "Franjas del día"],
    icono: "apagon",
    grupo: "desarrollo",
    guia: urlGuia("apagon"),
  },
];

export const tablerosDelGrupo = (grupo: GrupoTablero) => TABLEROS.filter((t) => t.grupo === grupo);
