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
    <div className="relative flex h-full flex-col justify-between gap-3 rounded-2xl border border-border bg-background-elevated p-5 transition-shadow hover:shadow-md">
      {ayuda && (
        <span className="absolute right-3 top-3">
          <InfoButton titulo={ayuda.titulo}>{ayuda.contenido}</InfoButton>
        </span>
      )}
      <p className="pr-6 text-xs font-medium uppercase tracking-wide text-foreground-muted">{etiqueta}</p>
      <div>
        <div className="flex items-center justify-between gap-3">
          <p className="text-2xl font-semibold tabular-nums text-foreground">{valor}</p>
          {icono && (
            <span
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl"
              style={{ color: acento, backgroundColor: acento ? `${acento}1a` : undefined }}
            >
              {icono}
            </span>
          )}
        </div>
        {delta && (
          <p
            className="mt-1.5 text-xs font-medium tabular-nums"
            style={{ color: delta.positivo ? "var(--color-optimo)" : "var(--color-critico)" }}
          >
            {delta.texto}
          </p>
        )}
      </div>
    </div>
  );
}
