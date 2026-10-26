"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import type { FichaModelo } from "@/lib/api/types";
import { AYUDAS_MODELOS } from "./ayudasModelos";

/**
 * Ficha documentada del modelo: la pregunta que responde y, en secciones plegables, método, datos, alcance,
 * limitaciones y siguientes pasos tal como los dicen sus documentos. La primera sección queda abierta.
 */
export function FichaPanel({ ficha }: { ficha: FichaModelo }) {
  return (
    <Card>
      <CardHeader title="Ficha del modelo" subtitle={`Según: ${ficha.documentos}`} ayuda={AYUDAS_MODELOS.ficha} />
      <div className="space-y-4 px-5 pb-5 pt-3">
        <p className="text-sm leading-relaxed">
          <span className="font-semibold">Pregunta que responde: </span>
          {ficha.pregunta}
        </p>
        <div className="space-y-2">
          {ficha.secciones.map((s, i) => (
            <details key={s.titulo} open={i === 0} className="rounded-lg border border-border px-3 py-2">
              <summary className="cursor-pointer text-sm font-semibold" style={{ color: "var(--color-marca-oscuro)" }}>
                {s.titulo}
              </summary>
              <ul className="mt-2 list-disc space-y-1.5 pl-5 text-sm leading-relaxed text-foreground">
                {s.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </details>
          ))}
        </div>
      </div>
    </Card>
  );
}
