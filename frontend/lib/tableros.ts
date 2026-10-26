/**
 * Registro de tableros de la plataforma.
 *
 * El panel principal (app/page.tsx) se arma recorriendo esta lista, así que para sumar un
 * tablero nuevo basta con crear su carpeta en `app/<ruta>/` y agregar aquí una entrada.
 * Es solo información de presentación: ningún dato sensible ni de negocio vive aquí.
 */
export type IconoTablero = "embalses" | "carbon" | "dns";

export interface Tablero {
  /** Identificador estable (se usa como clave y en las pruebas). */
  id: string;
  /** Ruta interna del tablero (carpeta dentro de `app/`). */
  ruta: `/${string}`;
  titulo: string;
  descripcion: string;
  /** De dónde salen los datos que muestra. */
  fuente: string;
  /** Lo principal que se puede ver en él (se muestra como etiquetas). */
  incluye: readonly string[];
  icono: IconoTablero;
}

export const TABLEROS: readonly Tablero[] = [
  {
    id: "embalses",
    ruta: "/embalses",
    titulo: "Embalses",
    descripcion:
      "Monitoreo del volumen útil, los aportes y el riesgo de los 24 embalses del SIN, con su pronóstico a 1, 3, 6 y 12 meses.",
    fuente: "Datos públicos de XM y SIMEM; proyección del modelo de largo plazo con escenarios El Niño/La Niña.",
    incluye: ["Volumen útil nacional y por región", "Riesgo en 5 niveles", "Senda de largo plazo", "Reportes CSV y JSON"],
    icono: "embalses",
  },
  {
    id: "carbon",
    ruta: "/carbon",
    titulo: "Carbón térmico",
    descripcion:
      "Proyección del consumo de carbón de las plantas térmicas del SIN durante El Niño 2026-2027, con su incertidumbre, el inventario requerido y la comparación con XM.",
    fuente: "Modelo de carbón térmico (ENOS → aportes → carbón, Monte Carlo) con datos de Sinergox, SIMEM y NOAA.",
    incluye: ["Escenarios P10, P50 y P90", "Uso del techo físico", "Inventario en días de consumo", "Validación del modelo"],
    icono: "carbon",
  },
  {
    id: "dns",
    ruta: "/dns",
    titulo: "Demanda no atendida",
    descripcion:
      "Eventos de demanda no atendida (DNS) por subárea operativa del SIN desde 2013: dónde, cuándo y por qué ocurren, qué zonas priorizar y qué pronostica el modelo para el mes siguiente.",
    fuente: "Eventos DNS y EDAC reportados a SIMEM; índice de priorización, patrones y modelo predictivo del Ministerio.",
    incluye: ["Priorización de zonas", "Patrones por hora y día", "Causas de los eventos", "Pronóstico mensual"],
    icono: "dns",
  },
];
