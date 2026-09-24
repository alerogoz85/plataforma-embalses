import { ThemeToggle } from "./ThemeToggle";

export function Header({ fechaCorte }: { fechaCorte?: string }) {
  return (
    <header className="sticky top-0 z-10 border-b border-border bg-background/85 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2.5">
          <span
            className="flex h-9 w-9 items-center justify-center rounded-xl text-white"
            style={{ backgroundColor: "var(--color-optimo)" }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 16c1.5-2 3-2 4.5 0s3 2 4.5 0 3-2 4.5 0 3 2 4.5 0" />
              <path d="M3 21h18" />
              <path d="M12 3v9" strokeLinecap="round" />
              <path d="M8 7l4-4 4 4" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <div>
            <h1 className="text-sm font-semibold leading-tight text-foreground">
              Plataforma de Monitoreo y Predicción de Embalses
            </h1>
            <p className="text-xs text-foreground-muted">
              {fechaCorte ? `Corte al ${fechaCorte}` : "Cargando corte de información…"}
            </p>
          </div>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
