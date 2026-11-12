interface OpcionRango<T extends string | number> {
  valor: T;
  etiqueta: string;
}

interface RangosRapidosProps<T extends string | number> {
  /** Nombre accesible del grupo (p. ej. «Rangos rápidos»). */
  etiqueta: string;
  opciones: readonly OpcionRango<T>[];
  /** Opcion activa; `null` cuando el estado actual no coincide con ninguna (p. ej. fechas escritas a mano). */
  valor: T | null;
  onCambiar: (valor: T) => void;
}

/** Atajos de un clic para un rango: botones de seleccion unica (radio) con la opcion vigente marcada. */
export function RangosRapidos<T extends string | number>({ etiqueta, opciones, valor, onCambiar }: RangosRapidosProps<T>) {
  return (
    <div role="radiogroup" aria-label={etiqueta} className="inline-flex gap-1 rounded-lg border border-border p-0.5">
      {opciones.map((o) => {
        const activa = o.valor === valor;
        return (
          <button
            key={String(o.valor)}
            type="button"
            role="radio"
            aria-checked={activa}
            onClick={() => onCambiar(o.valor)}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)] ${
              activa ? "text-white" : "text-foreground-muted hover:text-foreground"
            }`}
            style={activa ? { backgroundColor: "var(--color-marca)" } : undefined}
          >
            {o.etiqueta}
          </button>
        );
      })}
    </div>
  );
}
