import Image from "next/image";
import Link from "next/link";

import { RUTAS } from "@/lib/rutas";
import { ThemeToggle } from "./ThemeToggle";

interface HeaderProps {
  /** Fecha de corte de los datos (tablero de embalses). Se ignora si se pasa `subtitulo`. */
  fechaCorte?: string;
  /** Título del tablero; por defecto el de embalses. El nombre del sistema («Tableros Analíticos») es el del panel principal. */
  titulo?: string;
  /** Segunda linea del encabezado; sustituye al "Corte al ..." de embalses. */
  subtitulo?: string;
  /** Muestra el enlace "Tableros" que vuelve al panel principal (false en el propio panel). */
  enlacePanel?: boolean;
}

const ENLACE = "flex h-9 items-center gap-1.5 rounded-xl border border-border bg-background-elevated px-3 text-xs font-semibold text-foreground-muted transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]";

export function Header({
  fechaCorte,
  titulo = "Monitoreo y predicción de embalses",
  subtitulo,
  enlacePanel = true,
}: HeaderProps) {
  return (
    <header className="sticky top-0 z-10">
      {/* Franja superior GOV.CO, como en minenergia.gov.co */}
      <div style={{ backgroundColor: "var(--color-marca)" }}>
        <div className="mx-auto flex max-w-7xl items-center px-4 py-1.5 sm:px-6">
          <Image src="/marca/govco.webp" alt="GOV.CO" width={200} height={61} className="h-6 w-auto" priority />
        </div>
      </div>
      <div
        className="border-b-[3px] bg-background-elevated/95 backdrop-blur"
        style={{ borderBottomColor: "var(--color-institucional)" }}
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-2 sm:px-6">
          <div className="flex min-w-0 items-center gap-3 sm:gap-4">
            {/* El logo es de fondo claro: va sobre una pastilla blanca tambien en modo oscuro */}
            <span className="shrink-0 rounded-lg bg-white px-2 py-1">
              <Image
                src="/marca/logo-mme.png"
                alt="Ministerio de Minas y Energía"
                width={600}
                height={407}
                className="h-11 w-auto sm:h-14"
                priority
              />
            </span>
            <span className="hidden h-10 w-px shrink-0 bg-border-strong sm:block" aria-hidden="true" />
            <div className="min-w-0">
              <h1
                className="text-sm font-bold leading-tight sm:text-base"
                style={{ color: "var(--color-marca-oscuro)" }}
              >
                {titulo}
              </h1>
              <p className="text-xs text-foreground-muted">
                {subtitulo ?? (fechaCorte ? `Corte al ${fechaCorte}` : "Cargando corte de información…")}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            {/* Guia de la plataforma (documentacion tecnica y manual de usuario), en una pestana aparte
                para no perder los filtros del tablero. Es una pagina estatica: public/informacion.html */}
            {enlacePanel && (
              <Link href={RUTAS.panel} className={ENLACE}>
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <rect x="3" y="3" width="7" height="7" rx="1" />
                  <rect x="14" y="3" width="7" height="7" rx="1" />
                  <rect x="3" y="14" width="7" height="7" rx="1" />
                  <rect x="14" y="14" width="7" height="7" rx="1" />
                </svg>
                Tableros
              </Link>
            )}
            <a href={RUTAS.informacion} target="_blank" rel="noopener" className={ENLACE}>
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                <circle cx="12" cy="12" r="9" />
                <path d="M12 11v5" />
                <path d="M12 8h.01" />
              </svg>
              Información
            </a>
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>
  );
}
