"use client";

import type { ReactNode } from "react";

import { Card } from "./Card";

interface PanelAmpliableProps {
  /** Identificador estable (enlaza el botón con el contenido para los lectores de pantalla). */
  id: string;
  /** Encabezado de la tarjeta (un `CardHeader`). */
  encabezado: ReactNode;
  /** Qué se ve al ampliar, p. ej. «19 zonas»: va en el botón «Ver todo (19 zonas)». */
  resumen: string;
  ampliado: boolean;
  onAlternar: () => void;
  children: ReactNode;
}

/**
 * Tarjeta de contenido largo que por defecto mide lo mismo que su vecina de la fila (simetría) y se puede ampliar.
 *
 * - **Contraída (por defecto):** en pantallas anchas (dos columnas) la tarjeta se posiciona sobre su celda del grid, y como no aporta
 *   altura propia la fila mide lo que mide la vecina (con un mínimo de 26 rem para que siempre se pueda leer); en pantallas estrechas
 *   tiene una altura máxima de 28 rem. El contenido se desplaza dentro de la tarjeta, así que ningún dato queda inaccesible.
 * - **Ampliada:** la tarjeta toma su altura natural y muestra todo; la fila deja de estirar a la vecina (la página elige `items-start`).
 *
 * El botón anuncia su estado con `aria-expanded`; la zona desplazable es enfocable con teclado y tiene nombre accesible.
 */
export function PanelAmpliable({ id, encabezado, resumen, ampliado, onAlternar, children }: PanelAmpliableProps) {
  return (
    <div className={ampliado ? "" : "relative xl:min-h-[26rem]"}>
      <Card className={`flex flex-col ${ampliado ? "" : "xl:absolute xl:inset-0"}`}>
        {encabezado}
        <div
          id={id}
          className={ampliado ? "" : "min-h-0 flex-1 overflow-y-auto max-xl:max-h-[28rem]"}
          {...(ampliado ? {} : { tabIndex: 0, role: "region", "aria-label": "Contenido desplazable" })}
        >
          {children}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 border-t border-border px-5 py-2.5">
          <p className="text-xs text-foreground-muted">{ampliado ? "Se muestra todo el contenido." : "Desplázate dentro del panel o amplíalo para verlo completo."}</p>
          <button
            type="button"
            onClick={onAlternar}
            aria-expanded={ampliado}
            aria-controls={id}
            className="max-w-full rounded-lg border px-3 py-1.5 text-left text-xs font-semibold transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
            style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}
          >
            {ampliado ? "Ver menos" : `Ver todo (${resumen})`}
          </button>
        </div>
      </Card>
    </div>
  );
}
