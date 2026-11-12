interface ChipFiltroProps {
  etiqueta: string;
  onQuitar: () => void;
}

/** Filtro activo mostrado como chip; un clic lo quita. Pensado para la barra de contexto y el drill-down. */
export function ChipFiltro({ etiqueta, onQuitar }: ChipFiltroProps) {
  return (
    <button
      type="button"
      onClick={onQuitar}
      aria-label={`Quitar filtro: ${etiqueta}`}
      className="inline-flex items-center gap-1.5 rounded-full bg-marca-bg px-3 py-1 text-xs font-semibold text-marca-oscuro transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
    >
      {etiqueta}
      <span aria-hidden>×</span>
    </button>
  );
}
