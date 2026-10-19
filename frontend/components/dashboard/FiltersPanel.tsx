"use client";

import { Campo } from "@/components/ui/Campo";
import { AYUDAS } from "./ayudas";
import type { EmbalseResumen } from "@/lib/api/types";
import { REGIONES } from "@/lib/api/types";

interface FiltersPanelProps {
  regionSeleccionada: string | null;
  onCambiarRegion: (region: string | null) => void;
  embalseSeleccionado: string | null;
  onCambiarEmbalse: (embalseId: string | null) => void;
  onRestablecer: () => void;
  fechaInicio: string;
  fechaFin: string;
  onCambiarFechaInicio: (fecha: string) => void;
  onCambiarFechaFin: (fecha: string) => void;
  embalsesDisponibles: EmbalseResumen[];
}

export function FiltersPanel({
  regionSeleccionada,
  onCambiarRegion,
  embalseSeleccionado,
  onCambiarEmbalse,
  onRestablecer,
  fechaInicio,
  fechaFin,
  onCambiarFechaInicio,
  onCambiarFechaFin,
  embalsesDisponibles,
}: FiltersPanelProps) {
  const opcionesEmbalse = regionSeleccionada
    ? embalsesDisponibles.filter((e) => e.region === regionSeleccionada)
    : embalsesDisponibles;

  return (
    <div className="grid grid-cols-1 gap-x-5 gap-y-4 rounded-2xl border border-border bg-background-elevated p-5 sm:grid-cols-2 lg:grid-cols-4">
      <Campo etiqueta="Región" ayuda={AYUDAS.filtroRegion}>
        <select
          className="campo-select"
          value={regionSeleccionada ?? ""}
          onChange={(e) => onCambiarRegion(e.target.value || null)}
        >
          <option value="">Todas las regiones</option>
          {REGIONES.map((region) => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Embalse" ayuda={AYUDAS.filtroEmbalse}>
        <select
          className="campo-select"
          value={embalseSeleccionado ?? ""}
          onChange={(e) => onCambiarEmbalse(e.target.value || null)}
        >
          <option value="">Todos los embalses</option>
          {opcionesEmbalse.map((embalse) => (
            <option key={embalse.id} value={embalse.id}>
              {embalse.nombre}
            </option>
          ))}
        </select>
      </Campo>

      <Campo etiqueta="Desde" ayuda={AYUDAS.filtroDesde}>
        <input
          type="date"
          className="campo-select"
          value={fechaInicio}
          max={fechaFin}
          onChange={(e) => onCambiarFechaInicio(e.target.value)}
        />
      </Campo>

      <Campo etiqueta="Hasta" ayuda={AYUDAS.filtroHasta}>
        <input
          type="date"
          className="campo-select"
          value={fechaFin}
          min={fechaInicio}
          onChange={(e) => onCambiarFechaFin(e.target.value)}
        />
      </Campo>

      <div className="flex justify-end sm:col-span-2 lg:col-span-4">
        <button
          type="button"
          onClick={onRestablecer}
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
