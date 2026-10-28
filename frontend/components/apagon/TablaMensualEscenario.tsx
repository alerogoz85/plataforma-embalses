import type { MesEscenario } from "@/lib/api/types";
import { COLOR_SEMAFORO, rotuloMes } from "@/lib/utils/gemelo";

const entero = (v: number) => Math.round(v).toLocaleString("es-CO");
const pct1 = (v: number) => `${(v * 100).toFixed(1)} %`;

const COLUMNAS: { titulo: string; celda: (m: MesEscenario) => string }[] = [
  { titulo: "Mes", celda: (m) => rotuloMes(m.mes) },
  { titulo: "Índice (0-100)", celda: (m) => m.indice_riesgo.toFixed(1) },
  { titulo: "Prob. déficit", celda: (m) => pct1(m.probabilidad_deficit) },
  { titulo: "Prob. apagón severo", celda: (m) => pct1(m.probabilidad_apagon_severo) },
  { titulo: "Margen de reserva P50", celda: (m) => pct1(m.margen_reserva_pct_p50) },
  { titulo: "ONI P10 / P50 / P90", celda: (m) => `${m.oni_p10.toFixed(1)} / ${m.oni_p50.toFixed(1)} / ${m.oni_p90.toFixed(1)}` },
  { titulo: "Embalse % P10 / P50 / P90", celda: (m) => `${m.embalse_pct_p10.toFixed(0)} / ${m.embalse_pct_p50.toFixed(0)} / ${m.embalse_pct_p90.toFixed(0)}` },
  { titulo: "Demanda MWh P10 / P50 / P90", celda: (m) => `${entero(m.demanda_mwh_p10)} / ${entero(m.demanda_mwh_p50)} / ${entero(m.demanda_mwh_p90)}` },
  { titulo: "Oferta MWh P10 / P50 / P90", celda: (m) => `${entero(m.oferta_mwh_p10)} / ${entero(m.oferta_mwh_p50)} / ${entero(m.oferta_mwh_p90)}` },
  { titulo: "Déficit MWh P50 / P90", celda: (m) => `${entero(m.deficit_mwh_p50)} / ${entero(m.deficit_mwh_p90)}` },
];

/** «Ver tabla mensual completa»: todo lo que calcula el modelo para cada mes, plegado como en el visor. */
export function TablaMensualEscenario({ meses }: { meses: MesEscenario[] }) {
  return (
    <details className="rounded-2xl border border-border bg-background-elevated px-5 py-3">
      <summary className="cursor-pointer text-sm font-medium text-foreground">Ver tabla mensual completa (P10/P50/P90, probabilidades, índice)</summary>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[900px] border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-border text-foreground-muted">
              {COLUMNAS.map((c) => (
                <th key={c.titulo} scope="col" className="px-3 py-2 font-medium">{c.titulo}</th>
              ))}
              <th scope="col" className="px-3 py-2 font-medium">Semáforo</th>
            </tr>
          </thead>
          <tbody>
            {meses.map((m) => (
              <tr key={m.mes} className="border-b border-border/60">
                {COLUMNAS.map((c) => (
                  <td key={c.titulo} className="px-3 py-2 tabular-nums">{c.celda(m)}</td>
                ))}
                <td className="px-3 py-2">
                  <span className="inline-flex rounded-full px-2 py-0.5 font-semibold" style={{ color: COLOR_SEMAFORO[m.semaforo], backgroundColor: `color-mix(in srgb, ${COLOR_SEMAFORO[m.semaforo]} 14%, transparent)` }}>
                    {m.semaforo.charAt(0) + m.semaforo.slice(1).toLowerCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
