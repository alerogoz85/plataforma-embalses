"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";

interface InfoButtonProps {
  titulo: string;
  children: ReactNode;
}

const ANCHO_PANEL = 320;
const MARGEN = 12;

export function InfoButton({ titulo, children }: InfoButtonProps) {
  const [posicion, setPosicion] = useState<{ top: number; left: number } | null>(null);
  const botonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const idPanel = useId();
  const abierto = posicion !== null;

  useEffect(() => {
    if (!abierto) return;
    const cerrar = () => setPosicion(null);
    const alPulsarFuera = (evento: MouseEvent) => {
      const objetivo = evento.target as Node;
      if (!panelRef.current?.contains(objetivo) && !botonRef.current?.contains(objetivo)) cerrar();
    };
    const alPulsarTecla = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") cerrar();
    };
    document.addEventListener("mousedown", alPulsarFuera);
    document.addEventListener("keydown", alPulsarTecla);
    window.addEventListener("scroll", cerrar, true);
    window.addEventListener("resize", cerrar);
    return () => {
      document.removeEventListener("mousedown", alPulsarFuera);
      document.removeEventListener("keydown", alPulsarTecla);
      window.removeEventListener("scroll", cerrar, true);
      window.removeEventListener("resize", cerrar);
    };
  }, [abierto]);

  // Se muestra al pasar el cursor (o al enfocar con teclado) y se oculta al salir.
  // El clic tambien lo abre, para pantallas tactiles donde no hay hover.
  function abrir(evento?: React.SyntheticEvent) {
    evento?.stopPropagation();
    const caja = botonRef.current?.getBoundingClientRect();
    if (!caja) return;
    const ancho = Math.min(ANCHO_PANEL, window.innerWidth - MARGEN * 2);
    const left = Math.max(MARGEN, Math.min(caja.left, window.innerWidth - ancho - MARGEN));
    setPosicion({ top: caja.bottom + 6, left });
  }

  return (
    <>
      <button
        ref={botonRef}
        type="button"
        onMouseEnter={abrir}
        onMouseLeave={() => setPosicion(null)}
        onFocus={abrir}
        onBlur={() => setPosicion(null)}
        onClick={abrir}
        aria-label={`Ayuda: ${titulo}`}
        aria-expanded={abierto}
        aria-controls={abierto ? idPanel : undefined}
        className="inline-flex h-4 w-4 shrink-0 cursor-help items-center justify-center rounded-full bg-marca-bg text-[10px] font-bold leading-none text-marca transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
      >
        <span aria-hidden="true">i</span>
      </button>
      {abierto && (
        <div
          ref={panelRef}
          id={idPanel}
          role="note"
          style={{
            position: "fixed",
            top: posicion.top,
            left: posicion.left,
            width: Math.min(ANCHO_PANEL, window.innerWidth - MARGEN * 2),
            zIndex: 50,
            pointerEvents: "none",
          }}
          className="rounded-xl border border-border-strong bg-background-elevated p-3 text-left text-xs font-normal normal-case leading-relaxed tracking-normal text-foreground shadow-lg"
        >
          <p className="mb-1 font-semibold">{titulo}</p>
          <div className="space-y-1.5 text-foreground-muted">{children}</div>
        </div>
      )}
    </>
  );
}
