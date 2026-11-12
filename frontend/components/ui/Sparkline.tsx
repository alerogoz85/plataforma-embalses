import { Area, AreaChart, ResponsiveContainer } from "recharts";

interface SparklineProps {
  datos: readonly number[];
  /** Descripcion para lectores de pantalla (p. ej. «Volumen util, ultimos 12 meses»). */
  etiqueta: string;
  color?: string;
  className?: string;
}

/** Minigrafico de tendencia para tarjetas de KPI: sin ejes ni tooltip; la lectura exacta va en el valor de la tarjeta. */
export function Sparkline({ datos, etiqueta, color = "var(--color-marca)", className = "h-10 w-24" }: SparklineProps) {
  const validos = datos.filter((v) => Number.isFinite(v));
  if (validos.length < 2) return null;
  const puntos = validos.map((v, i) => ({ i, v }));
  const primero = validos[0];
  const ultimo = validos[validos.length - 1];
  return (
    <div className={className} role="img" aria-label={`${etiqueta}: de ${primero} a ${ultimo}`}>
      <ResponsiveContainer>
        <AreaChart data={puntos} margin={{ top: 2, right: 0, bottom: 2, left: 0 }}>
          <Area dataKey="v" stroke={color} strokeWidth={2} fill={color} fillOpacity={0.14} dot={false} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
