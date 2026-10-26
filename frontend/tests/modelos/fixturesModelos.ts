import type { FichaModelo, ResultadoModelo, ResultadosModelo } from "@/lib/api/types";

export const crearFichaModelo = (sobre: Partial<FichaModelo> = {}): FichaModelo => ({
  id: "apagon",
  titulo: "Riesgo de apagón condicionado por ENOS",
  resumen: "Modelo Monte Carlo nacional que estima el riesgo de déficit de generación.",
  estado: "sin_resultados",
  estado_detalle: "El modelo está implementado, pero no se dispone de una corrida final.",
  documentos: "Actividades 1 a 6",
  pregunta: "¿Qué probabilidad tiene el SIN de no cubrir la demanda?",
  secciones: [
    { titulo: "Método", items: ["Simulación Monte Carlo de 3.000 trayectorias.", "Semáforo VERDE / AMARILLO / ROJO."] },
    { titulo: "Limitaciones documentadas", items: ["Sin restricciones de red."] },
  ],
  datos_documentados: [
    { etiqueta: "Simulaciones por corrida", valor: "3.000", detalle: "Trayectorias Monte Carlo", documento: "Actividad 5" },
    { etiqueta: "Historia de ONI", valor: "317 meses", detalle: "2000 a 2026", documento: "Actividad 5" },
  ],
  archivos_esperados: [
    { ruta: "resultados_modelo_riesgo_apagon/resumen_mensual.csv", contenido: "Percentiles y semáforo por mes." },
    { ruta: "resultados_modelo_riesgo_apagon/metadatos_corrida.json", contenido: "Metadatos. Opcional." },
  ],
  comando_importacion: 'python -m infrastructure.ingesta.importar_resultado_modelo --modelo apagon --carpeta "../../5. Modelo apagón/Scripts"',
  carpeta_proyecto: "5. Modelo apagón/Scripts",
  ...sobre,
});

export const crearResultadoModelo = (sobre: Partial<ResultadoModelo> = {}): ResultadoModelo => ({
  generado_en: "2026-10-01T12:30:00",
  origen: "Modelo de riesgo de apagón (Monte Carlo) · 3 meses, 2026-10 a 2026-12",
  configuracion: [{ nombre: "Simulaciones", valor: "3000" }, { nombre: "Horizonte (meses)", valor: "18" }],
  indicadores: [
    { etiqueta: "Meses en rojo", valor: "1", detalle: "de 3 meses", nivel: "critico" },
    { etiqueta: "Mayor probabilidad de déficit", valor: "60,0 %", detalle: "2026-12", nivel: null },
  ],
  series: [
    { id: "indice", titulo: "Índice de riesgo (0-100)", unidad: "puntos", tipo: "linea", puntos: [
      { x: "2026-10", y: 10, p10: null, p90: null }, { x: "2026-11", y: 40, p10: null, p90: null }, { x: "2026-12", y: 85, p10: null, p90: null }] },
    { id: "embalse", titulo: "Nivel útil de los embalses", unidad: "%", tipo: "linea", puntos: [
      { x: "2026-10", y: 55, p10: 40, p90: 70 }, { x: "2026-11", y: 50, p10: 35, p90: 66 }, { x: "2026-12", y: 45, p10: 30, p90: 60 }] },
    { id: "deficit_p50", titulo: "Déficit esperado (P50)", unidad: "GWh", tipo: "barras", puntos: [
      { x: "2026-10", y: 0, p10: null, p90: null }, { x: "2026-11", y: 1, p10: null, p90: null }, { x: "2026-12", y: 90, p10: null, p90: null }] },
  ],
  tablas: [{ id: "semaforo", titulo: "Semáforo y probabilidades por mes", columnas: ["Mes", "Semáforo", "Índice"],
             filas: [["2026-10", "Verde", 10], ["2026-11", "Amarillo", 40.5], ["2026-12", "Rojo", null]], nota: "El déficit no incluye restricciones de red.", filtros_columna: {} }],
  advertencias: ["Mide adecuación de generación nacional agregada."],
  dimensiones: [],
  graficos: [],
  ...sobre,
});

export const sinResultados = (id: ResultadosModelo["modelo_id"] = "apagon"): ResultadosModelo => ({ modelo_id: id, disponible: false, resultado: null });
export const conResultados = (resultado = crearResultadoModelo(), id: ResultadosModelo["modelo_id"] = "apagon"): ResultadosModelo => ({
  modelo_id: id, disponible: true, resultado,
});

/** Resultado con dimensiones (serie y variable), gráficos por combinación y una tabla filtrable, como el de gas. */
export const crearResultadoConDimensiones = (): ResultadoModelo => {
  const punto = (x: string, y: number, p10: number | null = null, p90: number | null = null) => ({ x, y, p10, p90 });
  const grafico = (serie: string, variable: string) => ({
    id: `${serie}|${variable}`,
    titulo: `${serie} · ${variable}`,
    unidad: "GBTUD",
    etiquetas: { serie, variable },
    lineas: [
      { nombre: "Observado", estilo: "continua" as const, puntos: [punto("2026-01", 10), punto("2026-02", 11)] },
      { nombre: "Pronóstico", estilo: "continua" as const, puntos: [punto("2026-03", 12, 10, 14), punto("2026-04", 13, 11, 15)] },
      { nombre: "Referencia Arps", estilo: "punteada" as const, puntos: [punto("2026-03", 12.5)] },
    ],
  });
  return crearResultadoModelo({
    series: [],
    dimensiones: [
      { id: "serie", etiqueta: "Campo", opciones: ["NACIONAL", "CUSIANA"], por_defecto: "NACIONAL" },
      { id: "variable", etiqueta: "Variable", opciones: ["Fiscalizado", "Comercializado"], por_defecto: "Fiscalizado" },
    ],
    graficos: [grafico("NACIONAL", "Fiscalizado"), grafico("CUSIANA", "Fiscalizado"), grafico("NACIONAL", "Comercializado")],
    tablas: [
      { id: "v2_resumen", titulo: "Resumen por serie", columnas: ["Campo", "Variable", "Semáforo"], nota: null, filtros_columna: { serie: "Campo", variable: "Variable" },
        filas: [["NACIONAL", "Fiscalizado", "Verde"], ["CUSIANA", "Fiscalizado", "Rojo"], ["NACIONAL", "Comercializado", "Amarillo"]] },
    ],
  });
};
