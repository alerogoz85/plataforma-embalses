import type { ReactNode } from "react";

import { InfoButton } from "@/components/ui/InfoButton";
import { Sparkline } from "@/components/ui/Sparkline";

interface KpiCardProps {
  etiqueta: string;
  valor: string;
  delta?: { texto: string; positivo: boolean } | null;
  icono?: ReactNode;
  acento?: string;
  ayuda?: { titulo: string; contenido: ReactNode };
  /** Linea de contexto bajo el valor (p. ej. un rango o una comparacion), distinta del delta coloreado. */
  detalle?: ReactNode;
  /** Ultimos valores de la serie para el minigrafico de tendencia; sin ellos (o con menos de dos) no se dibuja. */
  tendencia?: readonly number[];
}

export function KpiCard({ etiqueta, valor, delta, icono, acento, ayuda, detalle, tendencia }: KpiCardProps) {
  return (
    <div className="tarjeta-elevable relative flex h-full flex-col justify-between gap-3 rounded-2xl border border-border bg-background-elevated p-5">
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
        <div className="mt-1.5 flex items-end justify-between gap-3">
          <div className="flex flex-col gap-1.5">
            {detalle && <p className="text-xs tabular-nums text-foreground-muted">{detalle}</p>}
            {delta && (
              <p
                className="text-xs font-medium tabular-nums"
                style={{ color: delta.positivo ? "var(--color-optimo)" : "var(--color-critico)" }}
              >
                {delta.texto}
              </p>
            )}
          </div>
          {tendencia && <Sparkline datos={tendencia} etiqueta={`Tendencia de ${etiqueta}`} color={acento} />}
        </div>
      </div>
    </div>
  );
}
