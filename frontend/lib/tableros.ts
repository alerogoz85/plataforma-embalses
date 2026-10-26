/**
 * Registro de tableros de la plataforma.
 *
 * El panel principal (app/page.tsx) se arma recorriendo esta lista, así que para sumar un
 * tablero nuevo basta con crear su carpeta en `app/<ruta>/` y agregar aquí una entrada.
 * Es solo información de presentación: ningún dato sensible ni de negocio vive aquí.
 */
export type IconoTablero = "embalses" | "carbon" | "dns" | "gas" | "optimizacion" | "apagon";

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
  /** Aviso corto en la tarjeta cuando el tablero aún no muestra resultados finales (p. ej. «En desarrollo»). */
  etiqueta?: string;
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
  {
    id: "gas",
    ruta: "/gas",
    titulo: "Gas natural",
    descripcion:
      "Oferta de gas declarada al Ministerio frente al gas fiscalizado por la ANH a nivel de campo, con curvas de declinación para evaluar y proyectar la oferta.",
    fuente: "Declaraciones de gas del MME y producción fiscalizada de la ANH, según los documentos del modelo.",
    incluye: ["Qué compara y cómo", "Datos y limitaciones", "Estado del modelo", "Carga de resultados"],
    icono: "gas",
    etiqueta: "En desarrollo",
  },
  {
    id: "optimizacion",
    ruta: "/optimizacion",
    titulo: "Optimización hidrotérmica",
    descripcion:
      "Planeación hidro-térmica estocástica (SDDP con riesgo CVaR) bajo escenarios ENOS: cuánta térmica usar, cuánta agua conservar y qué costo y riesgo implica.",
    fuente: "Documentos de modelamiento y evaluación técnica del producto SDDP; salidas de la corrida cuando se importen.",
    incluye: ["Método SDDP/CVaR", "Estado de la evidencia", "Limitaciones", "Carga de resultados"],
    icono: "optimizacion",
    etiqueta: "En desarrollo",
  },
  {
    id: "apagon",
    ruta: "/apagon",
    titulo: "Riesgo de apagón",
    descripcion:
      "Riesgo mensual de déficit de generación del SIN condicionado por ENOS (Monte Carlo): probabilidad de déficit, margen de reserva, índice de riesgo y semáforo.",
    fuente: "Modelo Monte Carlo de riesgo con datos de NOAA/CPC, UPME y el sector; salidas de la corrida cuando se importen.",
    incluye: ["Semáforo mensual", "Probabilidad de déficit", "Franjas horarias", "Carga de resultados"],
    icono: "apagon",
    etiqueta: "En desarrollo",
  },
];
