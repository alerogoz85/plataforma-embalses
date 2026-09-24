import type { NivelRiesgo } from "@/lib/api/types";
import { COLOR_VAR_RIESGO, etiquetaRiesgo } from "@/lib/utils/formatters";

export function RiskBadge({ nivel, tamano = "md" }: { nivel: NivelRiesgo; tamano?: "sm" | "md" }) {
  const colores = COLOR_VAR_RIESGO[nivel];
  const padding = tamano === "sm" ? "px-2 py-0.5 text-[11px]" : "px-2.5 py-1 text-xs";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${padding}`}
      style={{ color: colores.texto, backgroundColor: colores.fondo }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: colores.texto }} />
      {etiquetaRiesgo(nivel)}
    </span>
  );
}
