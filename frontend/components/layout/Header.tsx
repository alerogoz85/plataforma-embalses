import Image from "next/image";

import { ThemeToggle } from "./ThemeToggle";

export function Header({ fechaCorte }: { fechaCorte?: string }) {
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
                Plataforma de Monitoreo y Predicción de Embalses
              </h1>
              <p className="text-xs text-foreground-muted">
                {fechaCorte ? `Corte al ${fechaCorte}` : "Cargando corte de información…"}
              </p>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
