"use client";

import { Card } from "@/components/ui/Card";
import { InfoButton } from "@/components/ui/InfoButton";
import type { FichaModelo } from "@/lib/api/types";
import { COLOR_ESTADO, ETIQUETA_ESTADO } from "@/lib/utils/modelos";
import { AYUDAS_MODELOS } from "./ayudasModelos";

/** Cabecera del tablero: resumen del modelo y su estado real (qué hay y qué no) con el texto de los documentos. */
export function EstadoModeloCard({ ficha }: { ficha: FichaModelo }) {
  const color = COLOR_ESTADO[ficha.estado];
  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span
          className="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold"
          style={{ color, backgroundColor: `color-mix(in srgb, ${color} 14%, transparent)` }}
        >
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: color }} aria-hidden="true" />
          {ETIQUETA_ESTADO[ficha.estado]}
        </span>
        <InfoButton titulo={AYUDAS_MODELOS.estado.titulo}>{AYUDAS_MODELOS.estado.contenido}</InfoButton>
      </div>
      <h2 className="mt-3 text-base font-bold" style={{ color: "var(--color-marca-oscuro)" }}>
        {ficha.titulo}
      </h2>
      <p className="mt-1 text-sm leading-relaxed text-foreground-muted">{ficha.resumen}</p>
      <p className="mt-3 rounded-lg px-3 py-2 text-sm leading-relaxed" style={{ backgroundColor: "var(--color-alerta-bg)" }}>
        {ficha.estado_detalle}
      </p>
    </Card>
  );
}
