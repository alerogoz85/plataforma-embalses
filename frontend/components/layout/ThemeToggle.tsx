"use client";

import { useSyncExternalStore } from "react";

type Tema = "light" | "dark";

const EVENTO_CAMBIO_TEMA = "tema-cambiado";

function leerSnapshotCliente(): Tema {
  const guardado = window.localStorage.getItem("tema");
  if (guardado === "light" || guardado === "dark") return guardado;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function leerSnapshotServidor(): Tema {
  return "light";
}

function suscribirseATema(notificar: () => void): () => void {
  const consultaSistema = window.matchMedia("(prefers-color-scheme: dark)");
  consultaSistema.addEventListener("change", notificar);
  window.addEventListener("storage", notificar);
  window.addEventListener(EVENTO_CAMBIO_TEMA, notificar);
  return () => {
    consultaSistema.removeEventListener("change", notificar);
    window.removeEventListener("storage", notificar);
    window.removeEventListener(EVENTO_CAMBIO_TEMA, notificar);
  };
}

function alternarTema(temaActual: Tema) {
  const siguiente: Tema = temaActual === "dark" ? "light" : "dark";
  window.localStorage.setItem("tema", siguiente);
  document.documentElement.classList.toggle("dark", siguiente === "dark");
  window.dispatchEvent(new Event(EVENTO_CAMBIO_TEMA));
}

export function ThemeToggle() {
  const tema = useSyncExternalStore(suscribirseATema, leerSnapshotCliente, leerSnapshotServidor);

  return (
    <button
      type="button"
      onClick={() => alternarTema(tema)}
      aria-label={tema === "dark" ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className="flex h-9 w-9 items-center justify-center rounded-xl border border-border bg-background-elevated text-foreground-muted transition-colors hover:text-foreground"
    >
      {tema === "dark" ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" />
        </svg>
      )}
    </button>
  );
}
