import { InfoButton } from "@/components/ui/InfoButton";
import type { NivelRiesgo } from "@/lib/api/types";
import { AYUDAS } from "./ayudas";
import { COLOR_VAR_RIESGO, etiquetaRiesgo } from "@/lib/utils/formatters";

export function SistemaRiesgoCard({ nivel, totalEmbalses }: { nivel: NivelRiesgo; totalEmbalses: number }) {
  const colores = COLOR_VAR_RIESGO[nivel];
  return (
    <div className="relative flex h-full flex-col justify-between gap-3 rounded-2xl border border-border bg-background-elevated p-5">
      <span className="absolute right-3 top-3">
        <InfoButton titulo={AYUDAS.riesgoSistema.titulo}>{AYUDAS.riesgoSistema.contenido}</InfoButton>
      </span>
      <p className="pr-6 text-xs font-medium uppercase tracking-wide text-foreground-muted">
        Riesgo del sistema
      </p>
      <div>
        <div
          className="inline-flex items-center gap-2 rounded-xl px-3 py-1.5"
          style={{ backgroundColor: colores.fondo, color: colores.texto }}
        >
          <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colores.texto }} />
          <span className="text-lg font-semibold">{etiquetaRiesgo(nivel)}</span>
        </div>
        <p className="mt-1.5 text-xs text-foreground-muted">{totalEmbalses} embalses monitoreados</p>
      </div>
    </div>
  );
}
