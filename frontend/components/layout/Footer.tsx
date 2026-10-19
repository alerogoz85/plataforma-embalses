import Image from "next/image";
import type { ReactNode } from "react";

/** Pie comun a todos los tableros: logo del Ministerio y la linea de procedencia de cada uno. */
export function Footer({ children }: { children: ReactNode }) {
  return (
    <footer
      className="flex flex-col items-center gap-2 border-t-[3px] bg-background-elevated px-4 py-4 text-center text-xs text-foreground-muted sm:px-6"
      style={{ borderTopColor: "var(--color-institucional)" }}
    >
      <span className="rounded-lg bg-white px-2 py-1">
        <Image src="/marca/logo-mme.png" alt="Ministerio de Minas y Energía" width={600} height={407} className="h-10 w-auto" />
      </span>
      <p>{children}</p>
    </footer>
  );
}
