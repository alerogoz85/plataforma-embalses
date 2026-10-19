import type { ReactNode } from "react";

import { InfoButton } from "./InfoButton";

interface CampoProps {
  etiqueta: string;
  ayuda: { titulo: string; contenido: ReactNode };
  children: ReactNode;
}

/**
 * Campo de filtro: etiqueta visible + boton ⓘ con la explicacion + el control (select o fecha).
 * Es comun a todos los tableros; el control debe llevar la clase `campo-select` (ver globals.css).
 */
export function Campo({ etiqueta, ayuda, children }: CampoProps) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-foreground-muted">{etiqueta}</span>
        <InfoButton titulo={ayuda.titulo}>{ayuda.contenido}</InfoButton>
      </div>
      <label className="flex flex-col">
        <span className="sr-only">{etiqueta}</span>
        {children}
      </label>
    </div>
  );
}
