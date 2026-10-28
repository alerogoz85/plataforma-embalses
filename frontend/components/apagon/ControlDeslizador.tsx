"use client";

import { useId } from "react";

import { InfoButton } from "@/components/ui/InfoButton";
import type { ReactNode } from "react";

interface Props {
  etiqueta: string;
  ayuda?: { titulo: string; contenido: ReactNode };
  min: number;
  max: number;
  paso: number;
  valor: number;
  /** Texto de lo que se está eligiendo (por defecto, el valor). */
  rotulo?: string;
  rotuloMin?: string;
  rotuloMax?: string;
  onCambio: (valor: number) => void;
}

/** Deslizador del menú izquierdo: etiqueta con ayuda ⓘ, el valor elegido encima y los extremos debajo (como el visor de referencia). */
export function ControlDeslizador({ etiqueta, ayuda, min, max, paso, valor, rotulo, rotuloMin, rotuloMax, onCambio }: Props) {
  const id = useId();
  const porcentaje = ((valor - min) / (max - min)) * 100;
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <label htmlFor={id} className="text-xs font-medium text-foreground-muted">
          {etiqueta}
        </label>
        {ayuda && <InfoButton titulo={ayuda.titulo}>{ayuda.contenido}</InfoButton>}
      </div>
      <p className="text-xs font-semibold tabular-nums" style={{ color: "var(--color-marca)", marginLeft: `calc(${porcentaje}% - ${porcentaje * 0.16}px)` }}>
        {rotulo ?? valor}
      </p>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={paso}
        value={valor}
        onChange={(e) => onCambio(Number(e.target.value))}
        className="h-2 w-full cursor-pointer accent-[var(--color-marca)]"
      />
      <div className="flex justify-between text-[11px] tabular-nums text-foreground-muted">
        <span>{rotuloMin ?? min}</span>
        <span>{rotuloMax ?? max}</span>
      </div>
    </div>
  );
}
