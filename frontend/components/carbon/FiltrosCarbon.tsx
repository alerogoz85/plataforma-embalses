"use client";

import { Campo } from "@/components/ui/Campo";
import {
  DIAS_INVENTARIO,
  HISTORIAS_CARBON,
  HORIZONTES_CARBON,
  type DiasInventario,
  type HistoriaCarbon,
  type HorizonteCarbon,
  type UnidadCarbon,
} from "@/lib/api/types";
import { ETIQUETA_UNIDAD } from "@/lib/utils/carbon";
import { AYUDAS_CARBON } from "./ayudasCarbon";

/** Estado de los filtros globales del tablero. Cada campo gobierna a todos los graficos que lo usan. */
export interface FiltrosCarbon {
  historia: HistoriaCarbon;
  horizonte: HorizonteCarbon;
  unidad: UnidadCarbon;
  dias: DiasInventario;
}

export const FILTROS_CARBON_POR_DEFECTO: FiltrosCarbon = { historia: 36, horizonte: 9, unidad: "gbtu", dias: 45 };

interface FiltrosCarbonPanelProps {
  filtros: FiltrosCarbon;
  onCambiar: (filtros: FiltrosCarbon) => void;
}

const etiquetaHistoria = (m: HistoriaCarbon) => (m === 0 ? "Toda la historia" : `Últimos ${m} meses`);

/**
 * Panel de filtros del tablero de carbon. Solo ofrece las opciones que la API acepta (listas
 * cerradas), de modo que desde la interfaz nunca se envia un valor que el servidor rechace.
 */
export function FiltrosCarbonPanel({ filtros, onCambiar }: FiltrosCarbonPanelProps) {
  const cambiar = <K extends keyof FiltrosCarbon>(campo: K, valor: FiltrosCarbon[K]) => onCambiar({ ...filtros, [campo]: valor });

  return (
    <div className="grid grid-cols-1 gap-x-5 gap-y-4 rounded-2xl border border-border bg-background-elevated p-5 sm:grid-cols-2 lg:grid-cols-4">
      <Campo etiqueta="Historia" ayuda={AYUDAS_CARBON.filtroHistoria}>
        <select className="campo-select" value={filtros.historia} onChange={(e) => cambiar("historia", Number(e.target.value) as HistoriaCarbon)}>
          {HISTORIAS_CARBON.map((m) => (
            <option key={m} value={m}>
              {etiquetaHistoria(m)}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Horizonte" ayuda={AYUDAS_CARBON.filtroHorizonte}>
        <select className="campo-select" value={filtros.horizonte} onChange={(e) => cambiar("horizonte", Number(e.target.value) as HorizonteCarbon)}>
          {HORIZONTES_CARBON.map((m) => (
            <option key={m} value={m}>
              {m === 1 ? "1 mes" : `${m} meses`}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Unidad" ayuda={AYUDAS_CARBON.filtroUnidad}>
        <select className="campo-select" value={filtros.unidad} onChange={(e) => cambiar("unidad", e.target.value as UnidadCarbon)}>
          {(Object.keys(ETIQUETA_UNIDAD) as UnidadCarbon[]).map((u) => (
            <option key={u} value={u}>
              {ETIQUETA_UNIDAD[u]}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Días de inventario" ayuda={AYUDAS_CARBON.filtroInventario}>
        <select className="campo-select" value={filtros.dias} onChange={(e) => cambiar("dias", Number(e.target.value) as DiasInventario)}>
          {DIAS_INVENTARIO.map((d) => (
            <option key={d} value={d}>
              {d} días
            </option>
          ))}
        </select>
      </Campo>

      <div className="flex justify-end sm:col-span-2 lg:col-span-4">
        <button
          type="button"
          onClick={() => onCambiar(FILTROS_CARBON_POR_DEFECTO)}
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
