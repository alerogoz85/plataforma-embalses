import type { HTMLAttributes, ReactNode } from "react";

import { InfoButton } from "./InfoButton";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ children, className = "", ...props }: CardProps) {
  return (
    <div
      className={`rounded-2xl border border-border bg-background-elevated shadow-sm shadow-black/[0.02] dark:shadow-black/20 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  ayuda?: { titulo: string; contenido: ReactNode };
}

export function CardHeader({ title, subtitle, action, ayuda }: CardHeaderProps) {
  return (
    <div className="flex items-start justify-between gap-3 px-5 pt-5">
      <div>
        <h2 className="text-sm font-semibold tracking-wide text-foreground">{title}</h2>
        {subtitle && <p className="mt-0.5 text-xs text-foreground-muted">{subtitle}</p>}
      </div>
      {(action || ayuda) && (
        <div className="flex shrink-0 items-center gap-2">
          {action}
          {ayuda && <InfoButton titulo={ayuda.titulo}>{ayuda.contenido}</InfoButton>}
        </div>
      )}
    </div>
  );
}
