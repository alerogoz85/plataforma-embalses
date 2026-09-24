"use client";

import { InfoButton } from "@/components/ui/InfoButton";
import { AYUDAS, type Ayuda } from "./ayudas";
import type { EmbalseResumen } from "@/lib/api/types";
import { REGIONES } from "@/lib/api/types";

interface FiltersPanelProps {
  regionSeleccionada: string | null;
  onCambiarRegion: (region: string | null) => void;
  embalseSeleccionado: string | null;
  onCambiarEmbalse: (embalseId: string | null) => void;
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
    <div className="flex flex-wrap items-end gap-4 rounded-2xl border border-border bg-background-elevated p-4">
      <Campo etiqueta="Región" ayuda={AYUDAS.filtroRegion}>
        <select
          className="campo-select"
          value={regionSeleccionada ?? ""}
          onChange={(e) => {
            onCambiarRegion(e.target.value || null);
            onCambiarEmbalse(null);
          }}
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

      <style jsx>{`
        :global(.campo-select) {
          border: 1px solid var(--border-strong);
          background: var(--background);
          color: var(--foreground);
          border-radius: 0.6rem;
          padding: 0.4rem 0.7rem;
          font-size: 0.8rem;
          min-width: 9.5rem;
        }
        :global(.campo-select:focus) {
          outline: 2px solid var(--color-marca);
          outline-offset: 1px;
        }
      `}</style>
    </div>
  );
}

function Campo({
  etiqueta,
  ayuda,
  children,
}: {
  etiqueta: string;
  ayuda: Ayuda;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1.5">
        <span className="text-[11px] font-medium uppercase tracking-wide text-foreground-muted">
          {etiqueta}
        </span>
        <InfoButton titulo={ayuda.titulo}>{ayuda.contenido}</InfoButton>
      </div>
      <label className="flex flex-col">
        <span className="sr-only">{etiqueta}</span>
        {children}
      </label>
    </div>
  );
}
