"use client";

import type { CatalogoEscenarios, ModoOni } from "@/lib/api/types";
import { faseEnso, formatearOni } from "@/lib/utils/gemelo";
import { AYUDAS_APAGON } from "./ayudasApagon";
import { ControlDeslizador } from "./ControlDeslizador";
import { InfoButton } from "@/components/ui/InfoButton";

export interface EstadoControles {
  modo: ModoOni;
  oni: number;
  simulaciones: number;
  horizonte: number;
}

const ROTULO_MODO: Record<ModoOni, string> = { probabilistico: "Pronóstico ENOS (NOAA/CPC)", manual: "Manual (deslizador)" };

/**
 * Menú izquierdo del visor: modo de ONI, ONI objetivo, simulaciones y horizonte, con las mismas opciones que el visor de referencia.
 * En modo «Pronóstico ENOS» no hay ONI que mover, así que ese deslizador y la fase ENOS se reemplazan por una nota.
 */
export function PanelControles({
  catalogo, estado, onCambio, onRestablecer,
}: {
  catalogo: CatalogoEscenarios;
  estado: EstadoControles;
  onCambio: (cambios: Partial<EstadoControles>) => void;
  onRestablecer: () => void;
}) {
  const indiceSim = Math.max(0, catalogo.simulaciones.indexOf(estado.simulaciones));
  const indiceHor = Math.max(0, catalogo.horizontes.indexOf(estado.horizonte));
  const ultimaSim = catalogo.simulaciones.length - 1;
  const ultimoHor = catalogo.horizontes.length - 1;

  return (
    <aside aria-label="Controles del escenario" className="flex flex-col gap-5 rounded-2xl border border-border bg-background-elevated p-5 lg:sticky lg:top-28 lg:self-start">
      <div>
        <p className="text-base font-semibold text-foreground">⚡ Gemelo digital</p>
        <p className="mt-1 text-xs leading-relaxed text-foreground-muted">Riesgo de apagón del SIN condicionado por ENOS · modelo Monte Carlo</p>
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="flex w-full items-center justify-between gap-2 text-xs font-medium text-foreground-muted">
          Modo de ONI
          <InfoButton titulo={AYUDAS_APAGON.modoOni.titulo}>{AYUDAS_APAGON.modoOni.contenido}</InfoButton>
        </legend>
        {catalogo.modos.map((m) => (
          <label key={m} className="flex cursor-pointer items-center gap-2 text-sm text-foreground">
            <input type="radio" name="modo-oni" checked={estado.modo === m} onChange={() => onCambio({ modo: m })} className="accent-[var(--color-marca)]" />
            {ROTULO_MODO[m]}
          </label>
        ))}
      </fieldset>

      {estado.modo === "manual" ? (
        <>
          <ControlDeslizador
            etiqueta="ONI objetivo (°C)" ayuda={AYUDAS_APAGON.oni}
            min={catalogo.oni_minimo} max={catalogo.oni_maximo} paso={catalogo.oni_paso} valor={estado.oni}
            rotulo={estado.oni.toFixed(2)} rotuloMin={catalogo.oni_minimo.toFixed(2)} rotuloMax={catalogo.oni_maximo.toFixed(2)}
            onCambio={(oni) => onCambio({ oni: Math.round(oni * 10) / 10 })}
          />
          <div aria-label="Fase ENOS">
            <p className="text-xs font-medium text-foreground-muted">Fase ENOS</p>
            <p className="mt-1 text-2xl font-semibold leading-tight text-foreground">{faseEnso(estado.oni)}</p>
            <span className="mt-1.5 inline-flex rounded-full px-2 py-0.5 text-xs font-semibold" style={{ color: "var(--color-optimo)", backgroundColor: "var(--color-optimo-bg)" }}>
              {estado.oni >= 0 ? "↑" : "↓"} {formatearOni(estado.oni)}
            </span>
          </div>
        </>
      ) : (
        <p className="rounded-xl px-3 py-3 text-sm leading-relaxed" style={{ backgroundColor: "var(--color-marca-bg)", color: "var(--color-marca-oscuro)" }}>
          Usa el pronóstico probabilístico de ENOS vigente en el modelo.
        </p>
      )}

      <ControlDeslizador
        etiqueta="Simulaciones Monte Carlo" ayuda={AYUDAS_APAGON.simulaciones}
        min={0} max={ultimaSim} paso={1} valor={indiceSim} rotulo={String(estado.simulaciones)}
        rotuloMin={String(catalogo.simulaciones[0])} rotuloMax={String(catalogo.simulaciones[ultimaSim])}
        onCambio={(i) => onCambio({ simulaciones: catalogo.simulaciones[i] })}
      />
      <ControlDeslizador
        etiqueta="Horizonte (meses)" ayuda={AYUDAS_APAGON.horizonte}
        min={0} max={ultimoHor} paso={1} valor={indiceHor} rotulo={String(estado.horizonte)}
        rotuloMin={String(catalogo.horizontes[0])} rotuloMax={String(catalogo.horizontes[ultimoHor])}
        onCambio={(i) => onCambio({ horizonte: catalogo.horizontes[i] })}
      />

      <button
        type="button"
        onClick={onRestablecer}
        className="inline-flex h-9 items-center justify-center rounded-lg border px-3 text-xs font-semibold transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
        style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}
      >
        Restablecer controles
      </button>
    </aside>
  );
}
