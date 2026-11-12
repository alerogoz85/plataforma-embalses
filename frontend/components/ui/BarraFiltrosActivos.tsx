import { ChipFiltro } from "./ChipFiltro";

export interface FiltroActivo {
  id: string;
  etiqueta: string;
  onQuitar: () => void;
}

/**
 * Fila de chips con los filtros que NO estan en su valor por defecto, comun a todos los tableros: de un vistazo se ve que
 * recorte se esta mirando y cada chip se quita con un clic. Sin filtros activos no ocupa espacio.
 */
export function BarraFiltrosActivos({ filtros, className = "" }: { filtros: readonly FiltroActivo[]; className?: string }) {
  if (filtros.length === 0) return null;
  return (
    <div className={`-mt-2 flex flex-wrap items-center gap-2 ${className}`} role="group" aria-label="Filtros activos">
      <span className="text-xs text-foreground-muted">Filtros activos:</span>
      {filtros.map((f) => (
        <ChipFiltro key={f.id} etiqueta={f.etiqueta} onQuitar={f.onQuitar} />
      ))}
    </div>
  );
}
