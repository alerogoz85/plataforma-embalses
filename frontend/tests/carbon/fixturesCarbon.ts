import type { ComparacionXm, InventarioMensual, ResumenCarbon, SerieCarbon, ValidacionCarbon } from "@/lib/api/types";

export const PODER = 25; // simple a proposito: 100 GBTU/dia = 4 kt/dia

const banda = (p10: number, p50: number, p90: number) => ({ p10, p50, p90 });

export function crearResumenCarbon(sobre: Partial<ResumenCarbon> = {}): ResumenCarbon {
  return {
    origen: "prueba",
    poder_calorifico_mbtu_t: PODER,
    techo_gbtu_dia: 400,
    maximo_historico: { fecha: "2024-03-01", carbon_gbtu_dia: 340, mes_completo: true, fuente: null },
    ultimo_observado: { fecha: "2026-10-01", carbon_gbtu_dia: 213, mes_completo: false, fuente: "Estimado" },
    horizonte_meses: 9,
    pico: { fecha: "2027-02-01", carbon_gbtu_dia: banda(300, 350, 400), uso_techo_p50_pct: 87.5, prob_supera_maximo_pct: 62 },
    inventario_pico: { fecha: "2027-02-01", dias_inventario: 45, kt_p50: 630, kt_p90: 720 },
    trimestres: [
      { trimestre: "2026Q4", meses: 3, carbon_mt: banda(0.9, 1.0, 1.1), dentro_del_horizonte: true },
      { trimestre: "2027Q1", meses: 3, carbon_mt: banda(1.0, 1.2, 1.4), dentro_del_horizonte: true },
      { trimestre: "2027Q2", meses: 1, carbon_mt: banda(0.3, 0.4, 0.5), dentro_del_horizonte: false },
    ],
    criterios_cumplidos: 35,
    criterios_total: 38,
    ...sobre,
  };
}

export function crearSerieCarbon(sobre: Partial<SerieCarbon> = {}): SerieCarbon {
  const h = (fecha: string, v: number, completo = true) => ({
    fecha, carbon_gbtu_dia: v, techo_gbtu_dia: 400, uso_techo_pct: 50, aportes_pct_media: 90, roni: 0, fuente: "Real", mes_completo: completo,
  });
  const p = (fecha: string, b: [number, number, number], parcial: number | null = null) => ({
    fecha, dias: 30, roni: banda(-1, 0, 1), aportes_pct_media: banda(80, 90, 100), uso_techo_pct: banda(70, 80, 90),
    carbon_gbtu_dia: banda(...b), carbon_kt_mes: banda(1, 2, 3), prob_supera_maximo_pct: 10, observado_parcial_gbtu_dia: parcial,
  });
  return {
    techo_gbtu_dia: 400,
    maximo_historico_gbtu_dia: 340,
    poder_calorifico_mbtu_t: PODER,
    horizonte_meses: 9,
    historico: [h("2026-08-01", 200), h("2026-09-01", 250), h("2026-10-01", 213, false)],
    proyeccion: [p("2026-10-01", [250, 300, 350], 213), p("2026-11-01", [260, 310, 370])],
    ...sobre,
  };
}

export const crearInventario = (): InventarioMensual[] => [
  { fecha: "2026-10-01", dias_inventario: 45, kt_p50: 500, kt_p90: 600 },
  { fecha: "2026-11-01", dias_inventario: 45, kt_p50: 520, kt_p90: 640 },
];

export const crearComparacionXm = (xm: number | null = 450): ComparacionXm[] => [
  { fecha: "2026-10-01", modelo: banda(250, 300, 350), techo_gbtu_dia: 400, xm_estocastico_gbtu_dia: xm, xm_historicas_min_gbtu_dia: null, xm_historicas_max_gbtu_dia: null },
  { fecha: "2026-11-01", modelo: banda(260, 310, 370), techo_gbtu_dia: 400, xm_estocastico_gbtu_dia: 380, xm_historicas_min_gbtu_dia: null, xm_historicas_max_gbtu_dia: null },
];

export const crearValidacionCarbon = (): ValidacionCarbon => ({
  errores_horizonte: [
    { horizonte_meses: 1, pronosticos: 65, mae_modelo: 45.8, mae_persistencia: 47.2, mae_estacional: 112.3, mae_climatologia: 87.1, sesgo_modelo: -3.9 },
    { horizonte_meses: 3, pronosticos: 60, mae_modelo: 60.1, mae_persistencia: 70.0, mae_estacional: 112.3, mae_climatologia: 87.1, sesgo_modelo: -1.0 },
  ],
  episodios: [
    { episodio: "El Niño 2023-24", inicio: "2023-10-01", fin: "2024-03-01", meses: 6, real_gbtu_dia: 300, p50_gbtu_dia: 280, error_total_pct: -6.7, mae_modelo: 30, mae_ingenuo: 50, cobertura_p10_p90_pct: 83 },
  ],
  criterios_cumplidos: 1,
  criterios_total: 2,
  veredicto: [
    { criterio: "[aportes] RESET de Ramsey", resultado: "p=0.590", cumple: true, interpretacion: "Forma funcional adecuada" },
    { criterio: "[aportes] Breusch-Pagan", resultado: "p=0.001", cumple: false, interpretacion: "Varianza de residuos constante" },
  ],
  supuestos: [{ nombre: "Techo físico [GBTU/día]", valor: "403.3" }],
});
