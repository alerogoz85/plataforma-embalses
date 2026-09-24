import type { ReactNode } from "react";

import { InfoButton } from "@/components/ui/InfoButton";

interface KpiCardProps {
  etiqueta: string;
  valor: string;
  delta?: { texto: string; positivo: boolean } | null;
  icono?: ReactNode;
  acento?: string;
  ayuda?: { titulo: string; contenido: ReactNode };
}

export function KpiCard({ etiqueta, valor, delta, icono, acento, ayuda }: KpiCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-background-elevated p-5 transition-shadow hover:shadow-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <p className="text-xs font-medium uppercase tracking-wide text-foreground-muted">
            {etiqueta}
          </p>
          {ayuda && <InfoButton titulo={ayuda.titulo}>{ayuda.contenido}</InfoButton>}
        </div>
        {icono && (
          <span
            className="flex h-8 w-8 items-center justify-center rounded-xl"
            style={{ color: acento, backgroundColor: acento ? `${acento}1a` : undefined }}
          >
            {icono}
          </span>
        )}
      </div>
      <p className="mt-2 text-2xl font-semibold tabular-nums text-foreground">{valor}</p>
      {delta && (
        <p
          className="mt-1.5 text-xs font-medium tabular-nums"
          style={{ color: delta.positivo ? "var(--color-optimo)" : "var(--color-critico)" }}
        >
          {delta.texto}
        </p>
      )}
    </div>
  );
}
