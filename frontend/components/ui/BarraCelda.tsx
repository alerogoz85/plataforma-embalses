interface BarraCeldaProps {
  valor: number | null | undefined;
  /** Valor que ocupa toda la barra (100 para porcentajes). */
  maximo?: number;
  color?: string;
  etiqueta: string;
  /** Texto junto a la barra; por defecto el valor con un decimal y «%» cuando el maximo es 100. */
  formato?: (valor: number) => string;
}

const porDefecto = (maximo: number) => (valor: number) =>
  maximo === 100 ? `${valor.toLocaleString("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 })} %` : String(valor);

/** Barra de progreso para una celda de tabla: la barra comunica la magnitud y el numero la precisa. */
export function BarraCelda({ valor, maximo = 100, color = "var(--color-marca)", etiqueta, formato }: BarraCeldaProps) {
  if (valor === null || valor === undefined || !Number.isFinite(valor)) {
    return <span className="text-xs text-foreground-muted">—</span>;
  }
  const proporcion = maximo > 0 ? Math.min(Math.max(valor / maximo, 0), 1) : 0;
  return (
    <div className="flex items-center gap-2">
      <div
        role="progressbar"
        aria-label={etiqueta}
        aria-valuemin={0}
        aria-valuemax={maximo}
        aria-valuenow={Math.min(Math.max(valor, 0), maximo)}
        className="h-1.5 w-24 overflow-hidden rounded-full bg-border"
      >
        <div className="h-full rounded-full" style={{ width: `${proporcion * 100}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs tabular-nums text-foreground">{(formato ?? porDefecto(maximo))(valor)}</span>
    </div>
  );
}
