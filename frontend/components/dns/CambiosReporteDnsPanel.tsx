"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { CambioReporteDns } from "@/lib/api/types";
import { etiquetaMesDns } from "@/lib/utils/dns";
import { formatearNumero } from "@/lib/utils/formatters";
import { AYUDAS_DNS } from "./ayudasDns";

/** Subáreas cuya forma de reportar cambió: una explicación de los saltos en el número de eventos. */
export function CambiosReporteDnsPanel({ cambios }: { cambios: { datos: { cambios: CambioReporteDns[] } | null; error: string | null } }) {
  if (cambios.error) return <ErrorBloque que="los cambios de reporte" mensaje={cambios.error} />;
  if (!cambios.datos) return <SkeletonChart />;
  const filas = cambios.datos.cambios;

  return (
    <Card>
      <CardHeader
        title="Cambios en la forma de reportar"
        subtitle="Más descripciones genéricas y menos causa conocida a partir de un mes"
        ayuda={AYUDAS_DNS.cambiosReporte}
      />
      <div className="overflow-x-auto px-5 pb-5 pt-3">
        {filas.length === 0 ? (
          <p className="py-6 text-center text-sm text-foreground-muted">El modelo no detectó cambios de reporte en este ámbito.</p>
        ) : (
          <table className="w-full text-sm tabular-nums">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wide text-foreground-muted">
                <th className="py-1.5 pr-3 font-semibold">Subárea</th>
                <th className="py-1.5 pr-3 font-semibold">Desde</th>
                <th className="py-1.5 pr-3 text-right font-semibold">Descripción genérica</th>
                <th className="py-1.5 text-right font-semibold">Causa conocida</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((c) => (
                <tr key={`${c.codigo}-${c.periodo_quiebre}`} className="border-t border-border">
                  <td className="py-1.5 pr-3 font-medium">
                    {c.nombre}
                    <span className="block text-[11px] font-normal text-foreground-muted">{c.region}</span>
                  </td>
                  <td className="py-1.5 pr-3">{etiquetaMesDns(c.periodo_quiebre)}</td>
                  <td className="py-1.5 pr-3 text-right">
                    {formatearNumero(c.pct_generica_antes, 0)} % → <b>{formatearNumero(c.pct_generica_despues, 0)} %</b>
                  </td>
                  <td className="py-1.5 text-right">
                    {formatearNumero(c.pct_causa_conocida_antes, 0)} % → <b>{formatearNumero(c.pct_causa_conocida_despues, 0)} %</b>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Card>
  );
}
