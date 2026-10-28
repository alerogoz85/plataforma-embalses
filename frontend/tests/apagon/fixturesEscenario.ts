import type { CatalogoEscenarios, EscenarioApagon, MesEscenario } from "@/lib/api/types";

export const crearCatalogo = (sobre: Partial<CatalogoEscenarios> = {}): CatalogoEscenarios => ({
  disponible: true,
  modos: ["probabilistico", "manual"],
  oni_minimo: -2.5, oni_maximo: 2.5, oni_paso: 0.1, oni_por_defecto: 1.0,
  simulaciones: [1000, 2000, 5000], simulaciones_por_defecto: 2000,
  horizontes: [12, 18, 24], horizonte_por_defecto: 18,
  franjas: ["madrugada_00_05", "manana_06_11", "tarde_12_17", "pico_noche_18_21", "noche_22_23"],
  fuente: { generado_en: "2026-10-27T09:00:00", origen: "Modelo de prueba", ultimo_oni_observado: 1.8, ultimo_mes_demanda: "2026-08-01", semilla: 7 },
  ...sobre,
});

export const crearMes = (i: number, sobre: Partial<MesEscenario> = {}): MesEscenario => ({
  mes: `2026-${String(i + 1).padStart(2, "0")}`,
  indice_riesgo: 5 + i, probabilidad_deficit: 0.05 * (i + 1), probabilidad_apagon_severo: 0.02 * (i + 1),
  semaforo: i < 2 ? "AMARILLO" : "ROJO",
  oni_p10: 0.1, oni_p50: 1, oni_p90: 1.9, embalse_pct_p10: 40, embalse_pct_p50: 55, embalse_pct_p90: 70,
  demanda_mwh_p10: 6.9e6, demanda_mwh_p50: 7e6, demanda_mwh_p90: 7.1e6, oferta_mwh_p10: 6.8e6, oferta_mwh_p50: 7.2e6, oferta_mwh_p90: 7.5e6,
  deficit_mwh_p50: 10, deficit_mwh_p90: 90, margen_reserva_pct_p50: 0.12,
  deficit_por_franja_mwh: [10, 20, 30, 100 + i, 40],
  ...sobre,
});

export const crearEscenario = (p: { modo?: "manual" | "probabilistico"; oni?: number; simulaciones?: number; horizonte?: number } = {}): EscenarioApagon => {
  const horizonte = p.horizonte ?? 12;
  const modo = p.modo ?? "manual";
  return { modo, oni: modo === "manual" ? (p.oni ?? 1) : null, simulaciones: p.simulaciones ?? 2000, horizonte, meses: Array.from({ length: horizonte }, (_, i) => crearMes(i % 12)) };
};
