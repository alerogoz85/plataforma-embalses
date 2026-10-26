"use client";

import { Campo } from "@/components/ui/Campo";
import type { EsquemaUrl } from "@/lib/hooks/useEstadoUrl";
import { codigo, enLista } from "@/lib/utils/url";
import {
  ORIGENES_DNS,
  PERIODOS_DNS,
  type CatalogoDns,
  type OrigenDns,
  type PeriodoDns,
} from "@/lib/api/types";
import { AYUDAS_DNS } from "./ayudasDns";

/** Estado de los filtros globales del tablero. Cada campo gobierna a todos los bloques que lo usan. */
export interface FiltrosDnsEstado {
  periodo: PeriodoDns;
  region: string | null;
  subarea: string | null;
  origen: OrigenDns | null;
}

export const FILTROS_DNS_POR_DEFECTO: FiltrosDnsEstado = { periodo: 36, region: null, subarea: null, origen: null };

/**
 * Los filtros viven en la URL (`/dns?periodo=12&region=Caribe&origen=programada`). El período y el origen se validan contra las
 * listas cerradas de la API; la región y la subárea solo por forma (la página las contrasta además con el catálogo cargado).
 */
export const ESQUEMA_DNS: EsquemaUrl<FiltrosDnsEstado> = {
  periodo: { param: "periodo", defecto: () => FILTROS_DNS_POR_DEFECTO.periodo, leer: enLista(PERIODOS_DNS) },
  region: { param: "region", defecto: () => null, leer: codigo(40) },
  subarea: { param: "subarea", defecto: () => null, leer: codigo(20) },
  origen: { param: "origen", defecto: () => null, leer: enLista(ORIGENES_DNS) },
};

const etiquetaPeriodo = (m: PeriodoDns) => (m === 0 ? "Todo el histórico (2013-)" : `Últimos ${m} meses`);
const ETIQUETA_ORIGEN: Record<OrigenDns, string> = { programada: "Programada", no_programada: "No programada" };

interface FiltrosDnsPanelProps {
  filtros: FiltrosDnsEstado;
  catalogo: CatalogoDns | null;
  onCambiar: (filtros: FiltrosDnsEstado) => void;
}

/**
 * Panel de filtros del tablero DNS. Solo ofrece lo que la API acepta; la región y la subárea salen del
 * catálogo de la corrida cargada. Al cambiar de región la subárea vuelve a «Todas» (mismo patrón que en embalses).
 */
export function FiltrosDnsPanel({ filtros, catalogo, onCambiar }: FiltrosDnsPanelProps) {
  const subareas = (catalogo?.subareas ?? []).filter((s) => !filtros.region || s.region === filtros.region);

  return (
    <div className="grid grid-cols-1 gap-x-5 gap-y-4 rounded-2xl border border-border bg-background-elevated p-5 sm:grid-cols-2 lg:grid-cols-4">
      <Campo etiqueta="Período" ayuda={AYUDAS_DNS.filtroPeriodo}>
        <select className="campo-select" value={filtros.periodo} onChange={(e) => onCambiar({ ...filtros, periodo: Number(e.target.value) as PeriodoDns })}>
          {PERIODOS_DNS.map((m) => (
            <option key={m} value={m}>
              {etiquetaPeriodo(m)}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Región" ayuda={AYUDAS_DNS.filtroRegion}>
        <select className="campo-select" value={filtros.region ?? ""} onChange={(e) => onCambiar({ ...filtros, region: e.target.value || null, subarea: null })}>
          <option value="">Todas las regiones</option>
          {(catalogo?.regiones ?? []).map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Subárea" ayuda={AYUDAS_DNS.filtroSubarea}>
        <select className="campo-select" value={filtros.subarea ?? ""} onChange={(e) => onCambiar({ ...filtros, subarea: e.target.value || null })}>
          <option value="">Todas las subáreas</option>
          {subareas.map((s) => (
            <option key={s.codigo} value={s.codigo}>
              {s.nombre}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Origen" ayuda={AYUDAS_DNS.filtroOrigen}>
        <select className="campo-select" value={filtros.origen ?? ""} onChange={(e) => onCambiar({ ...filtros, origen: (e.target.value || null) as OrigenDns | null })}>
          <option value="">Programada y no programada</option>
          {ORIGENES_DNS.map((o) => (
            <option key={o} value={o}>
              {ETIQUETA_ORIGEN[o]}
            </option>
          ))}
        </select>
      </Campo>

      <div className="flex justify-end sm:col-span-2 lg:col-span-4">
        <button
          type="button"
          onClick={() => onCambiar(FILTROS_DNS_POR_DEFECTO)}
          className="inline-flex h-9 items-center gap-2 rounded-lg border px-3 text-xs font-semibold transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
          style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M3 12a9 9 0 1 0 3-6.7" />
            <path d="M3 4v5h5" />
          </svg>
          Restablecer filtros
        </button>
      </div>
    </div>
  );
}
