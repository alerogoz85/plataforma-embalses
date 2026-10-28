"use client";

import { useId } from "react";

import type { ArchivoRequerido } from "@/lib/api/types";
import { aceptarDe, extensionDe, formatearTamano } from "@/lib/utils/archivos";

/** Un campo de archivo del paquete de un tablero: qué es, qué formatos acepta, si es obligatorio y el archivo elegido. */
export function SelectorArchivo({
  requerido, archivo, onElegir, onQuitar, limite,
}: {
  requerido: ArchivoRequerido;
  archivo: File | null;
  onElegir: (f: File) => void;
  onQuitar: () => void;
  /** Tamaño máximo (bytes) de lo que viaja por la red; los CSV/JSON se comprimen solos antes de enviarse. */
  limite: number;
}) {
  const id = useId();
  const extension = archivo ? extensionDe(archivo.name) : "";
  const formatoInvalido = archivo !== null && !requerido.formatos.includes(extension);
  const comprimible = archivo !== null && ["csv", "json"].includes(extension);
  const muyGrande = archivo !== null && archivo.size > limite && !comprimible;

  return (
    <div className="flex flex-col gap-1.5 rounded-xl border border-border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <label htmlFor={id} className="text-sm font-semibold">
          {requerido.etiqueta}
        </label>
        <span
          className="rounded-full px-2 py-0.5 text-[11px] font-semibold"
          style={requerido.obligatorio ? { color: "var(--color-critico)", backgroundColor: "var(--color-critico-bg)" } : { color: "var(--foreground-muted)", backgroundColor: "var(--border)" }}
        >
          {requerido.obligatorio ? "Obligatorio" : "Opcional"}
        </span>
      </div>
      {requerido.descripcion && <p className="text-xs text-foreground-muted">{requerido.descripcion}</p>}
      <p className="text-xs text-foreground-muted">Formato: {requerido.formatos.map((f) => `.${f}`).join(" o ")}</p>
      <input
        id={id}
        type="file"
        accept={aceptarDe(requerido.formatos)}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onElegir(f);
          e.target.value = ""; // permite volver a elegir el mismo archivo después de quitarlo
        }}
        className="text-xs file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-white"
        style={{ ["--tw-file-bg" as string]: "var(--color-marca)" }}
      />
      {archivo && (
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          <span className="break-all">
            {archivo.name} · {formatearTamano(archivo.size)}
          </span>
          <button type="button" onClick={onQuitar} className="font-semibold underline" style={{ color: "var(--color-marca)" }} aria-label={`Quitar ${requerido.etiqueta}`}>
            Quitar
          </button>
        </div>
      )}
      {formatoInvalido && (
        <p role="alert" className="text-xs font-medium" style={{ color: "var(--color-critico)" }}>
          Este archivo no es {requerido.formatos.map((f) => `.${f}`).join(" ni ")}.
        </p>
      )}
      {muyGrande && (
        <p role="alert" className="text-xs font-medium" style={{ color: "var(--color-critico)" }}>
          Pesa {formatearTamano(archivo.size)} y el máximo es {formatearTamano(limite)}.
        </p>
      )}
    </div>
  );
}
