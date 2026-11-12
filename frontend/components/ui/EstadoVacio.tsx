import type { ReactNode } from "react";

interface EstadoVacioProps {
  titulo: string;
  descripcion?: ReactNode;
  accion?: { texto: string; onClick: () => void };
  className?: string;
}

/** Bloque para cuando una consulta valida no devuelve datos (distinto de un error): explica por que y ofrece la salida. */
export function EstadoVacio({ titulo, descripcion, accion, className = "" }: EstadoVacioProps) {
  return (
    <div
      role="status"
      className={`flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border-strong p-10 text-center ${className}`}
    >
      <p className="text-sm font-semibold text-foreground">{titulo}</p>
      {descripcion && <p className="max-w-xs text-xs text-foreground-muted">{descripcion}</p>}
      {accion && (
        <button
          type="button"
          onClick={accion.onClick}
          className="rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
          style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}
        >
          {accion.texto}
        </button>
      )}
    </div>
  );
}
