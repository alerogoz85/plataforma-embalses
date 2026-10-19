/** Estilo comun de ejes y tooltip de los graficos de carbon (mismos valores que el tablero de embalses). */
export const ESTILO_TICK = { fontSize: 11, fill: "var(--foreground-muted)" } as const;

export const ESTILO_TOOLTIP = {
  contentStyle: {
    background: "var(--background-elevated)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    fontSize: 12,
  },
  labelStyle: { color: "var(--foreground)", fontWeight: 600 },
} as const;

/** Colores de lo que solo existe en este tablero (el resto reutiliza los --chart-* de embalses). */
export const COLOR_TECHO = "var(--color-critico)";
export const COLOR_RECORD = "var(--color-alerta)";
export const COLOR_XM = "var(--chart-aportes)";
