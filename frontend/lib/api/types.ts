// Clasificacion del %V. util: Normal >80, Estable 70-80, Alerta temprana 60-70, Situacion delicada 50-60, Critico <50.
export type NivelRiesgo = "NORMAL" | "ESTABLE" | "ALERTA_TEMPRANA" | "SITUACION_DELICADA" | "CRITICO";

export interface EmbalseResumen {
  id: string;
  nombre: string;
  region: string;
  es_agregado: boolean;
  fecha: string;
  pct_volumen_util: number;
  nivel_riesgo: NivelRiesgo;
  volumen_util_mm3: number;
  capacidad_util_mm3: number;
  energia_util_gwh: number | null;
  aportes_m3s: number | null;
  aportes_pct_media: number | null;
  vertimientos_m3s: number | null;
  turbinado_m3s: number | null;
  dias_autonomia: number | null;
  delta_diario_pct: number;
  delta_semanal_pct: number;
}

export interface RegionResumen {
  region: string;
  pct_volumen_util: number;
  aportes_pct_media: number | null;
  nivel_riesgo: NivelRiesgo;
  num_embalses: number;
  energia_util_gwh: number;
}

export interface KpiNacional {
  fecha_corte: string;
  pct_volumen_util_nacional: number;
  delta_diario_pct: number;
  delta_semanal_pct: number;
  aportes_pct_media_nacional: number | null;
  capacidad_guardada_gwh: number;
  nivel_riesgo_sistema: NivelRiesgo;
  total_embalses: number;
}

export interface ResumenNacional {
  kpis: KpiNacional;
  regiones: RegionResumen[];
  embalses: EmbalseResumen[];
}

export interface SeriePunto {
  fecha: string;
  pct_volumen_util: number;
  energia_util_gwh: number | null;
  aportes_m3s: number | null;
  aportes_pct_media: number | null;
  vertimientos_m3s: number | null;
  turbinado_m3s: number | null;
}

export interface EmbalseDetalle {
  resumen: EmbalseResumen;
  serie_historica: SeriePunto[];
}

export interface PrediccionPunto {
  fecha: string;
  valor_esperado: number;
  limite_inferior: number;
  limite_superior: number;
}

export interface Prediccion {
  embalse_id: string;
  horizonte_dias: number;
  /** null cuando la proyección es la de Outputs: sus límites son escenarios P10/P90, no un IC. */
  nivel_confianza: number | null;
  generado_en: string;
  metodo: string;
  puntos: PrediccionPunto[];
  /** "outputs": modelo de largo plazo interpolado a diario; "holt_winters": respaldo estadístico. */
  origen: OrigenProyeccion;
}

export const REGIONES: string[] = ["Antioquia", "Caldas", "Caribe", "Centro", "Oriente", "Valle"];
// 1, 3, 6 y 12 meses, con el mes comercial de 30 dias (lo que espera la API).
export const HORIZONTES_PREDICCION = [30, 90, 180, 360] as const;
export type HorizontePrediccion = (typeof HORIZONTES_PREDICCION)[number];

export interface PuntoMensual {
  mes: string; // "YYYY-MM"
  pct_volumen_util: number;
}

export interface PuntoProyeccionMensual {
  mes: string; // "YYYY-MM"
  valor_esperado: number;
  limite_inferior: number;
  limite_superior: number;
}

export interface MetricaValidacion {
  modelo: string;
  mae: number;
  r2: number;
}

export interface SendaVolumen {
  embalse_id: string;
  nombre: string;
  metodo: string;
  generado_en: string;
  ultimo_observado: PuntoMensual;
  minimo_proyectado: PuntoProyeccionMensual;
  historico: PuntoMensual[];
  proyeccion: PuntoProyeccionMensual[];
  validacion: MetricaValidacion[];
  /** "outputs": modelo de largo plazo (limites = escenarios P10/P90); "holt_winters": respaldo estadístico (IC 95%). */
  origen_proyeccion: OrigenProyeccion;
  /** Meses proyectados de verdad: una corrida de Outputs puede publicar menos de los pedidos. */
  horizonte_efectivo_meses: number;
}

export type OrigenProyeccion = "outputs" | "holt_winters";

export const ID_TOTAL_NACIONAL = "TOTAL";
/** Id del agregado de una región ("Todos los embalses" con una región elegida). */
export const idAgregadoRegion = (region: string) => `REGION:${region}`;
export const HORIZONTES_SENDA_VOLUMEN = [1, 3, 6, 12] as const;
export type HorizonteSendaVolumen = (typeof HORIZONTES_SENDA_VOLUMEN)[number];

export interface FuenteDatos {
  fuente: string;
  descripcion: string;
  es_real: boolean;
  fecha_corte: string | null;
  actualizado_en: string | null;
}

// ---------------------------------------------------------------- Modelo de carbon termico
// Espejo de los DTO de /api/v1/carbon/*. Consumo en GBTU/dia; inventario y consumo mensual en kt;
// aportes y uso del techo en %. Las bandas son escenarios P10/P50/P90, no intervalos de confianza.

export interface BandaCarbon {
  p10: number;
  p50: number;
  p90: number;
}

export interface PuntoCarbon {
  fecha: string;
  carbon_gbtu_dia: number;
  mes_completo: boolean;
  fuente: string | null;
}

export interface TrimestreCarbon {
  trimestre: string;
  meses: number;
  carbon_mt: BandaCarbon;
  dentro_del_horizonte: boolean;
}

export interface ResumenCarbon {
  origen: string;
  poder_calorifico_mbtu_t: number;
  techo_gbtu_dia: number;
  maximo_historico: PuntoCarbon;
  ultimo_observado: PuntoCarbon;
  horizonte_meses: number;
  pico: {
    fecha: string;
    carbon_gbtu_dia: BandaCarbon;
    uso_techo_p50_pct: number;
    prob_supera_maximo_pct: number;
  };
  inventario_pico: { fecha: string; dias_inventario: number; kt_p50: number; kt_p90: number } | null;
  trimestres: TrimestreCarbon[];
  criterios_cumplidos: number;
  criterios_total: number;
}

export interface HistoricoCarbon {
  fecha: string;
  carbon_gbtu_dia: number;
  techo_gbtu_dia: number | null;
  uso_techo_pct: number | null;
  aportes_pct_media: number | null;
  roni: number | null;
  fuente: string;
  mes_completo: boolean;
}

export interface ProyeccionCarbon {
  fecha: string;
  dias: number;
  roni: BandaCarbon;
  aportes_pct_media: BandaCarbon;
  uso_techo_pct: BandaCarbon;
  carbon_gbtu_dia: BandaCarbon;
  carbon_kt_mes: BandaCarbon;
  prob_supera_maximo_pct: number;
  observado_parcial_gbtu_dia: number | null;
}

export interface SerieCarbon {
  techo_gbtu_dia: number;
  maximo_historico_gbtu_dia: number;
  poder_calorifico_mbtu_t: number;
  horizonte_meses: number;
  historico: HistoricoCarbon[];
  proyeccion: ProyeccionCarbon[];
}

export interface InventarioMensual {
  fecha: string;
  dias_inventario: number;
  kt_p50: number;
  kt_p90: number;
}

export interface ComparacionXm {
  fecha: string;
  modelo: BandaCarbon;
  techo_gbtu_dia: number;
  xm_estocastico_gbtu_dia: number | null;
  xm_historicas_min_gbtu_dia: number | null;
  xm_historicas_max_gbtu_dia: number | null;
}

export interface ErrorHorizonteCarbon {
  horizonte_meses: number;
  pronosticos: number;
  mae_modelo: number;
  mae_persistencia: number;
  mae_estacional: number;
  mae_climatologia: number;
  sesgo_modelo: number;
}

export interface EpisodioCarbon {
  episodio: string;
  inicio: string;
  fin: string;
  meses: number;
  real_gbtu_dia: number;
  p50_gbtu_dia: number;
  error_total_pct: number;
  mae_modelo: number;
  mae_ingenuo: number;
  cobertura_p10_p90_pct: number;
}

export interface CriterioCarbon {
  criterio: string;
  resultado: string;
  cumple: boolean;
  interpretacion: string;
}

export interface ValidacionCarbon {
  errores_horizonte: ErrorHorizonteCarbon[];
  episodios: EpisodioCarbon[];
  criterios_cumplidos: number;
  criterios_total: number;
  veredicto: CriterioCarbon[];
  supuestos: { nombre: string; valor: string }[];
}

// Listas cerradas: son las mismas que valida la API (cualquier otro valor responde 422).
export const HORIZONTES_CARBON = [1, 3, 6, 9] as const;
export type HorizonteCarbon = (typeof HORIZONTES_CARBON)[number];
export const HISTORIAS_CARBON = [12, 36, 60, 0] as const; // 0 = toda la historia
export type HistoriaCarbon = (typeof HISTORIAS_CARBON)[number];
export const DIAS_INVENTARIO = [15, 30, 45, 60] as const;
export type DiasInventario = (typeof DIAS_INVENTARIO)[number];
export type UnidadCarbon = "gbtu" | "kt";

// ---------------------------------------------------------------- Modelo de demanda no atendida (DNS)
// Espejo de los DTO de /api/v1/dns/*. Energía en GWh; porcentajes 0-100; conteos de eventos.
// Las variaciones son frente a la ventana anterior de igual duración (null si no hay base).

export interface SubareaDns {
  codigo: string;
  nombre: string;
  region: string;
  departamentos: string | null;
}

export interface CatalogoDns {
  origen: string;
  fecha_inicio: string;
  fecha_corte: string;
  mes_corte_parcial: boolean;
  regiones: string[];
  subareas: SubareaDns[];
  periodo_pronostico: string;
}

export interface ResumenDns {
  periodo_meses: number;
  desde: string;
  hasta: string;
  eventos: number;
  energia_gwh: number;
  pct_criticos: number;
  pct_no_programados: number | null;
  variacion_eventos_pct: number | null;
  variacion_energia_pct: number | null;
  causa_mas_frecuente: string | null;
  causa_mas_frecuente_eventos: number;
  eventos_edac: number;
}

export interface MesDns {
  mes: string;
  eventos: number;
  energia_gwh: number;
  eventos_no_programados: number;
  parcial: boolean;
}

export interface SerieDns {
  meses: MesDns[];
  pronostico: { mes: string; eventos: number; energia_gwh: number; subareas: number } | null;
  nota_pronostico: string | null;
}

export interface ZonaDns {
  ranking: number;
  codigo: string;
  nombre: string;
  region: string;
  indice_priorizacion: number;
  energia_total_gwh: number;
  n_eventos: number;
  pct_criticos: number;
  variacion_pct: number;
}

export interface PatronesDns {
  por_hora: number[];
  dias: string[];
  por_dia_semana: number[];
  franjas: { franja: string; no_programada: number; programada: number; pct_no_programada: number | null }[];
  eventos_usados: number;
  eventos_hora_desconocida: number;
}

export interface CausasDns {
  total: number;
  causas: { causa: string; eventos: number; energia_gwh: number; pct_eventos: number }[];
  origen_de_la_causa: { nombre: string; eventos: number }[];
  tipos_evento: { nombre: string; eventos: number }[];
  niveles_red: { nombre: string; eventos: number }[];
}

export interface CambioReporteDns {
  codigo: string;
  nombre: string;
  region: string;
  periodo_quiebre: string;
  direccion: string;
  pct_generica_antes: number;
  pct_generica_despues: number;
  pct_causa_conocida_antes: number;
  pct_causa_conocida_despues: number;
}

export interface MetricaDns {
  modelo: string;
  variable: string;
  mae: number;
  rmse: number;
  mejora_vs_persistencia_pct: number | null;
}

export interface ModeloDns {
  periodo_pronostico: string;
  metricas: MetricaDns[];
  importancia: { variable: string; importancia_n_eventos: number; importancia_energia_kwh: number }[];
  pronostico: { codigo: string; nombre: string; region: string; n_eventos: number; energia_gwh: number }[];
}

// Listas cerradas: son las mismas que valida la API (cualquier otro valor responde 422).
export const PERIODOS_DNS = [12, 36, 60, 0] as const; // 0 = todo el histórico
export type PeriodoDns = (typeof PERIODOS_DNS)[number];
export const ORIGENES_DNS = ["programada", "no_programada"] as const;
export type OrigenDns = (typeof ORIGENES_DNS)[number];

// ---------------------------------------------------------------- Modelos analíticos con ficha (gas, optimización, apagón)
// Espejo de /api/v1/modelos/{modelo_id}/*. La ficha viene de los documentos del modelo; los resultados solo existen
// cuando se importaron las salidas del modelo (si no, `disponible` es false: es un estado normal, no un error).

export const MODELOS_ANALITICOS = ["gas", "optimizacion", "apagon"] as const;
export type ModeloAnalitico = (typeof MODELOS_ANALITICOS)[number];
export type EstadoModelo = "sin_resultados" | "prueba_tecnica" | "con_resultados";
export type NivelIndicador = "ok" | "alerta" | "critico";

export interface FichaModelo {
  id: ModeloAnalitico;
  titulo: string;
  resumen: string;
  estado: EstadoModelo;
  estado_detalle: string;
  documentos: string;
  pregunta: string;
  secciones: { titulo: string; items: string[] }[];
  datos_documentados: { etiqueta: string; valor: string; detalle: string; documento: string }[];
  archivos_esperados: { ruta: string; contenido: string }[];
  comando_importacion: string;
  carpeta_proyecto: string;
}

export interface IndicadorModelo {
  etiqueta: string;
  valor: string;
  detalle: string | null;
  nivel: NivelIndicador | null;
}

export interface PuntoSerieModelo {
  x: string;
  y: number;
  p10: number | null;
  p90: number | null;
}

export interface SerieModelo {
  id: string;
  titulo: string;
  unidad: string;
  tipo: "linea" | "barras";
  puntos: PuntoSerieModelo[];
}

export interface TablaModelo {
  id: string;
  titulo: string;
  columnas: string[];
  filas: (string | number | null)[][];
  nota: string | null;
  /** dimensión -> columna: con una dimensión elegida solo se muestran las filas cuya columna coincide con la opción. */
  filtros_columna: Record<string, string>;
}

/** Un filtro del resultado (p. ej. el campo o la variable). Los gráficos y tablas que lo declaran se muestran solo si coinciden con la opción elegida. */
export interface DimensionModelo {
  id: string;
  etiqueta: string;
  opciones: string[];
  por_defecto: string;
}

export interface LineaGraficoModelo {
  nombre: string;
  estilo: "continua" | "punteada";
  puntos: PuntoSerieModelo[];
}

/** Gráfico con varias líneas sobre el mismo eje (observado, pronóstico, referencia…). */
export interface GraficoModelo {
  id: string;
  titulo: string;
  unidad: string;
  lineas: LineaGraficoModelo[];
  etiquetas: Record<string, string>;
}

export interface ResultadoModelo {
  generado_en: string;
  origen: string;
  configuracion: { nombre: string; valor: string }[];
  indicadores: IndicadorModelo[];
  series: SerieModelo[];
  tablas: TablaModelo[];
  advertencias: string[];
  dimensiones: DimensionModelo[];
  graficos: GraficoModelo[];
}

export interface ResultadosModelo {
  modelo_id: ModeloAnalitico;
  disponible: boolean;
  resultado: ResultadoModelo | null;
}
