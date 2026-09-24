import type {
  EmbalseDetalle,
  EmbalseResumen,
  FuenteDatos,
  KpiNacional,
  Prediccion,
  RegionResumen,
  ResumenNacional,
  SendaVolumen,
  SeriePunto,
} from "@/lib/api/types";

export function crearEmbalse(sobrescribir: Partial<EmbalseResumen> = {}): EmbalseResumen {
  return {
    id: "GUAVIO",
    nombre: "Guavio",
    region: "Oriente",
    es_agregado: false,
    fecha: "2026-09-22",
    pct_volumen_util: 94.3,
    nivel_riesgo: "OPTIMO",
    volumen_util_mm3: 943,
    capacidad_util_mm3: 1000,
    energia_util_gwh: 2400,
    aportes_m3s: 80,
    aportes_pct_media: 80,
    vertimientos_m3s: 0,
    turbinado_m3s: 62.4,
    dias_autonomia: null,
    delta_diario_pct: -0.2,
    delta_semanal_pct: -1.1,
    ...sobrescribir,
  };
}

export const EMBALSES_EJEMPLO: EmbalseResumen[] = [
  crearEmbalse(),
  crearEmbalse({
    id: "PRADO", nombre: "Prado", region: "Centro", pct_volumen_util: 35.8,
    aportes_pct_media: 28, turbinado_m3s: 7.1, energia_util_gwh: 90, dias_autonomia: 4967,
  }),
  crearEmbalse({
    id: "MUNA", nombre: "Muna", region: "Centro", pct_volumen_util: 12.4, nivel_riesgo: "CRITICO",
    aportes_m3s: null, aportes_pct_media: null, energia_util_gwh: null, turbinado_m3s: 26.5,
  }),
  crearEmbalse({
    id: "AGREGADO_BOGOTA", nombre: "Agregado Bogotá", region: "Centro", es_agregado: true,
    pct_volumen_util: 66.8, aportes_m3s: null, aportes_pct_media: null, turbinado_m3s: null,
    vertimientos_m3s: null,
  }),
];

export const REGIONES_EJEMPLO: RegionResumen[] = [
  { region: "Oriente", pct_volumen_util: 94.3, aportes_pct_media: 80, nivel_riesgo: "REBOCE", num_embalses: 1, energia_util_gwh: 2400 },
  { region: "Centro", pct_volumen_util: 30.1, aportes_pct_media: 28, nivel_riesgo: "OPTIMO", num_embalses: 3, energia_util_gwh: 500 },
  { region: "Caldas", pct_volumen_util: 12, aportes_pct_media: null, nivel_riesgo: "CRITICO", num_embalses: 1, energia_util_gwh: 10 },
];

export const KPIS_EJEMPLO: KpiNacional = {
  fecha_corte: "2026-09-22",
  pct_volumen_util_nacional: 77.5,
  delta_diario_pct: -0.34,
  delta_semanal_pct: -1.47,
  aportes_pct_media_nacional: 46.3,
  capacidad_guardada_gwh: 13553,
  nivel_riesgo_sistema: "OPTIMO",
  total_embalses: 24,
};

export function crearResumen(sobrescribir: Partial<ResumenNacional> = {}): ResumenNacional {
  return { kpis: KPIS_EJEMPLO, regiones: REGIONES_EJEMPLO, embalses: EMBALSES_EJEMPLO, ...sobrescribir };
}

export function crearSerie(dias = 5): SeriePunto[] {
  return Array.from({ length: dias }, (_, i) => ({
    fecha: `2026-09-${String(18 + i).padStart(2, "0")}`,
    pct_volumen_util: 90 + i,
    energia_util_gwh: 2000 + i,
    aportes_m3s: i % 2 === 0 ? 40 : null,
    aportes_pct_media: i % 2 === 0 ? 50 : null,
    vertimientos_m3s: 0,
    turbinado_m3s: 30,
  }));
}

export function crearDetalle(dias = 5): EmbalseDetalle {
  return { resumen: crearEmbalse(), serie_historica: crearSerie(dias) };
}

export function crearPrediccion(puntos = 3): Prediccion {
  return {
    embalse_id: "GUAVIO",
    horizonte_dias: 30,
    nivel_confianza: 0.95,
    generado_en: "2026-09-23T12:00:00Z",
    metodo: "Holt-Winters de prueba",
    puntos: Array.from({ length: puntos }, (_, i) => ({
      fecha: `2026-09-${String(23 + i).padStart(2, "0")}`,
      valor_esperado: 90 - i,
      limite_inferior: 85 - i,
      limite_superior: 95 - i,
    })),
  };
}

export function crearSenda(sobrescribir: Partial<SendaVolumen> = {}): SendaVolumen {
  return {
    embalse_id: "TOTAL",
    nombre: "Total nacional",
    metodo: "Holt-Winters estacional de prueba",
    generado_en: "2026-09-23T12:00:00Z",
    ultimo_observado: { mes: "2026-09", pct_volumen_util: 79 },
    minimo_proyectado: { mes: "2027-04", valor_esperado: 60, limite_inferior: 40, limite_superior: 80 },
    historico: [
      { mes: "2026-07", pct_volumen_util: 70 },
      { mes: "2026-08", pct_volumen_util: 75 },
      { mes: "2026-09", pct_volumen_util: 79 },
    ],
    proyeccion: [
      { mes: "2026-10", valor_esperado: 78, limite_inferior: 70, limite_superior: 86 },
      { mes: "2026-11", valor_esperado: 72, limite_inferior: 60, limite_superior: 84 },
    ],
    validacion: [
      { modelo: "Persistencia (ultimo valor)", mae: 3.57, r2: 0.537 },
      { modelo: "Holt-Winters estacional de prueba", mae: 2.217, r2: 0.828 },
    ],
    ...sobrescribir,
  };
}

export const FUENTE_REAL: FuenteDatos = {
  fuente: "SIMEM / XM",
  descripcion: "Datos publicos de XM",
  es_real: true,
  fecha_corte: "2026-09-22",
  actualizado_en: "2026-09-23T17:50:06Z",
};
