import type {
  CambioReporteDns, CatalogoDns, CausasDns, ModeloDns, PatronesDns, ResumenDns, SerieDns, ZonaDns,
} from "@/lib/api/types";

export const crearCatalogoDns = (sobre: Partial<CatalogoDns> = {}): CatalogoDns => ({
  origen: "Modelo DNS de prueba",
  fecha_inicio: "2013-01-02",
  fecha_corte: "2026-08-11",
  mes_corte_parcial: true,
  regiones: ["Norte", "Sur", "Sin asignar"],
  subareas: [
    { codigo: "Are0002", nombre: "SubArea Dos", region: "Norte", departamentos: null },
    { codigo: "Are0003", nombre: "SubArea Tres", region: "Sur", departamentos: null },
    { codigo: "Are0001", nombre: "SubArea Uno", region: "Norte", departamentos: "Antioquia" },
  ],
  periodo_pronostico: "2026-08",
  ...sobre,
});

export const crearResumenDns = (sobre: Partial<ResumenDns> = {}): ResumenDns => ({
  periodo_meses: 36, desde: "2023-09", hasta: "2026-08", eventos: 5963, energia_gwh: 214.1, pct_criticos: 9.3,
  pct_no_programados: 82.9, variacion_eventos_pct: 142.2, variacion_energia_pct: -39.3,
  causa_mas_frecuente: "mantenimiento", causa_mas_frecuente_eventos: 2835, eventos_edac: 14, ...sobre,
});

export const crearSerieDns = (sobre: Partial<SerieDns> = {}): SerieDns => ({
  meses: [
    { mes: "2026-06", eventos: 100, energia_gwh: 4.5, eventos_no_programados: 80, parcial: false },
    { mes: "2026-07", eventos: 120, energia_gwh: 6.0, eventos_no_programados: 90, parcial: false },
    { mes: "2026-08", eventos: 40, energia_gwh: 2.0, eventos_no_programados: 30, parcial: true },
  ],
  pronostico: { mes: "2026-08", eventos: 311, energia_gwh: 3.5, subareas: 19 },
  nota_pronostico: null,
  ...sobre,
});

export const crearZonasDns = (): { zonas: ZonaDns[] } => ({
  zonas: [
    { ranking: 1, codigo: "Are0001", nombre: "SubArea Uno", region: "Norte", indice_priorizacion: 83.2, energia_total_gwh: 164.5, n_eventos: 2326, pct_criticos: 21, variacion_pct: -6.0 },
    { ranking: 2, codigo: "Are0003", nombre: "SubArea Tres", region: "Sur", indice_priorizacion: 65.3, energia_total_gwh: 24.6, n_eventos: 1839, pct_criticos: 1, variacion_pct: 2081.2 },
  ],
});

export const crearPatronesDns = (sobre: Partial<PatronesDns> = {}): PatronesDns => ({
  por_hora: Array.from({ length: 24 }, (_, h) => (h === 7 ? 90 : 10)),
  dias: ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
  por_dia_semana: [10, 11, 12, 13, 14, 15, 30],
  franjas: [
    { franja: "Madrugada (0-5h)", no_programada: 6, programada: 4, pct_no_programada: 60 },
    { franja: "Mañana (6-11h)", no_programada: 5, programada: 5, pct_no_programada: 50 },
    { franja: "Tarde (12-17h)", no_programada: 9, programada: 1, pct_no_programada: 90 },
    { franja: "Noche (18-23h)", no_programada: 0, programada: 0, pct_no_programada: null },
  ],
  eventos_usados: 105, eventos_hora_desconocida: 14, ...sobre,
});

export const crearCausasDns = (sobre: Partial<CausasDns> = {}): CausasDns => ({
  total: 100,
  causas: [
    { causa: "mantenimiento", eventos: 48, energia_gwh: 145.3, pct_eventos: 48 },
    { causa: "desconocido", eventos: 45, energia_gwh: 64.6, pct_eventos: 45 },
    { causa: "fallas", eventos: 7, energia_gwh: 4.2, pct_eventos: 7 },
  ],
  origen_de_la_causa: [{ nombre: "sin clasificar", eventos: 45 }, { nombre: "inferida (TF-IDF)", eventos: 30 }, { nombre: "reportada", eventos: 25 }],
  tipos_evento: [
    { nombre: "Disparo de activo/protección", eventos: 40 }, { nombre: "Trabajos de mantenimiento (consignación)", eventos: 30 },
    { nombre: "Otro / no clasificado", eventos: 10 }, { nombre: "Indisponibilidad de activo", eventos: 8 },
    { nombre: "Evento no programado (SDL)", eventos: 7 }, { nombre: "Evento programado (SDL)", eventos: 5 },
  ],
  niveles_red: [{ nombre: "No especificado", eventos: 60 }],
  ...sobre,
});

export const crearCambiosDns = (): { cambios: CambioReporteDns[] } => ({
  cambios: [
    { codigo: "Are0001", nombre: "SubArea Uno", region: "Norte", periodo_quiebre: "2024-09", direccion: "SUBIDA",
      pct_generica_antes: 0, pct_generica_despues: 82.8, pct_causa_conocida_antes: 25, pct_causa_conocida_despues: 3.2 },
  ],
});

export const crearModeloDns = (sobre: Partial<ModeloDns> = {}): ModeloDns => ({
  periodo_pronostico: "2026-08",
  metricas: [
    { modelo: "persistencia", variable: "n_eventos", mae: 6.65, rmse: 14.8, mejora_vs_persistencia_pct: null },
    { modelo: "GradientBoosting", variable: "n_eventos", mae: 5.22, rmse: 11.9, mejora_vs_persistencia_pct: 21.5 },
    { modelo: "persistencia", variable: "energia_kwh", mae: 238279.21, rmse: 465410.26, mejora_vs_persistencia_pct: null },
    { modelo: "GradientBoosting (log)", variable: "energia_kwh", mae: 200703.92, rmse: 414069.8, mejora_vs_persistencia_pct: 15.8 },
  ],
  importancia: [
    { variable: "n_eventos", importancia_n_eventos: 0.567, importancia_energia_kwh: 0.03 },
    { variable: "n_eventos_roll6", importancia_n_eventos: 0.212, importancia_energia_kwh: 0.62 },
  ],
  pronostico: [
    { codigo: "Are0001", nombre: "SubArea Uno", region: "Norte", n_eventos: 64.8, energia_gwh: 0.65 },
    { codigo: "Are0003", nombre: "SubArea Tres", region: "Sur", n_eventos: 38, energia_gwh: 0.66 },
  ],
  ...sobre,
});
