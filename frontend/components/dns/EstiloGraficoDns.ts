/** Estilo común de ejes y tooltip de los gráficos DNS (mismos valores que el resto de tableros). */
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

export const COLOR_PRONOSTICO = "var(--color-alerta)";
export const COLOR_NO_PROGRAMADA = "var(--color-critico)";
export const COLOR_PROGRAMADA = "var(--chart-volumen)";
