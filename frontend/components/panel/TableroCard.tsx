import Link from "next/link";

import type { IconoTablero, Tablero } from "@/lib/tableros";

const ICONOS: Record<IconoTablero, React.ReactNode> = {
  // Gota de agua sobre el nivel del embalse
  embalses: (
    <>
      <path d="M12 3s6 6.2 6 10.2a6 6 0 1 1-12 0C6 9.2 12 3 12 3Z" />
      <path d="M3 21h18" />
    </>
  ),
  // Llama sobre un montón de carbón (consumo térmico)
  carbon: (
    <>
      <path d="M12 3c1 3 4 4.5 4 8a4 4 0 0 1-8 0c0-1.6.8-2.6 1.6-3.6" />
      <path d="M3 21h18" />
      <path d="M6 21l2-3h8l2 3" />
    </>
  ),
  // Llama de gas sobre un tubo (gasoducto)
  gas: (
    <>
      <path d="M12 3c1 2.5 4 4 4 7.5a4 4 0 0 1-8 0c0-1.5.7-2.6 1.5-3.5" />
      <path d="M3 18h18M3 21h18" />
    </>
  ),
  // Balanza: decisión entre alternativas con costo y riesgo
  optimizacion: (
    <>
      <path d="M12 3v18M7 21h10" />
      <path d="M5 7h14" />
      <path d="M5 7l-2.5 6a3 3 0 0 0 5 0L5 7ZM19 7l-2.5 6a3 3 0 0 0 5 0L19 7Z" />
    </>
  ),
  // Bombilla apagada
  apagon: (
    <>
      <path d="M9 18h6M10 21h4" />
      <path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2V17h5v-1.1c0-.8.4-1.5 1-2A6 6 0 0 0 12 3Z" />
    </>
  ),
  // Rayo cortado: energía que no llegó
  dns: (
    <>
      <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />
      <path d="M3 3l18 18" />
    </>
  ),
};

/** Tarjeta de acceso a un tablero. Toda la tarjeta es un enlace (área de clic grande y un solo foco). */
export function TableroCard({ tablero }: { tablero: Tablero }) {
  return (
    <Link
      href={tablero.ruta}
      aria-label={`Abrir el tablero de ${tablero.titulo}`}
      className="group flex h-full flex-col gap-4 rounded-2xl border border-border bg-background-elevated p-6 shadow-sm shadow-black/[0.02] transition-all hover:-translate-y-0.5 hover:border-[var(--color-marca)] hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
    >
      <span className="flex items-start justify-between gap-2">
      <span
        className="flex h-12 w-12 items-center justify-center rounded-xl text-white"
        style={{ backgroundColor: "var(--color-marca)" }}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          {ICONOS[tablero.icono]}
        </svg>
      </span>
        {tablero.etiqueta && (
          <span
            className="rounded-full px-2.5 py-1 text-[11px] font-semibold"
            style={{ backgroundColor: "var(--color-alerta-bg)", color: "var(--color-alerta)" }}
          >
            {tablero.etiqueta}
          </span>
        )}
      </span>

      <div className="flex flex-col gap-2">
        <h2 className="text-xl font-bold" style={{ color: "var(--color-marca-oscuro)" }}>
          {tablero.titulo}
        </h2>
        <p className="text-sm leading-relaxed text-foreground-muted">{tablero.descripcion}</p>
      </div>

      <ul className="flex flex-wrap gap-1.5" aria-label="Qué incluye">
        {tablero.incluye.map((item) => (
          <li
            key={item}
            className="rounded-full px-2.5 py-1 text-[11px] font-medium"
            style={{ backgroundColor: "var(--color-marca-bg)", color: "var(--color-marca-oscuro)" }}
          >
            {item}
          </li>
        ))}
      </ul>

      <p className="text-xs text-foreground-muted">
        <span className="font-semibold text-foreground">Fuente: </span>
        {tablero.fuente}
      </p>

      <span
        className="mt-auto inline-flex items-center gap-1.5 text-sm font-semibold"
        style={{ color: "var(--color-marca)" }}
      >
        Abrir tablero
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="transition-transform group-hover:translate-x-1" aria-hidden="true">
          <path d="M5 12h14" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      </span>
    </Link>
  );
}
