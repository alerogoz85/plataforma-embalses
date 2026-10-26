"use client";

import { KpiCard } from "@/components/dashboard/KpiCard";
import type { FichaModelo } from "@/lib/api/types";
import { AYUDAS_MODELOS } from "./ayudasModelos";

/** Cifras ya publicadas en los documentos del modelo, rotuladas como tales (no son resultados de esta plataforma). */
export function DatosDocumentados({ datos }: { datos: FichaModelo["datos_documentados"] }) {
  return (
    <section aria-label="Cifras documentadas" className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {datos.map((d, i) => (
        <KpiCard
          key={d.etiqueta}
          etiqueta={d.etiqueta}
          valor={d.valor}
          detalle={`${d.detalle} · ${d.documento}`}
          acento="var(--color-marca)"
          ayuda={i === 0 ? AYUDAS_MODELOS.datosDocumentados : undefined}
        />
      ))}
    </section>
  );
}
