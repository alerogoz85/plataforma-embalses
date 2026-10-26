"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import { SkeletonChart } from "@/components/ui/Skeleton";
import { useValidacionCarbon } from "@/lib/hooks/useCarbon";
import { AYUDAS_CARBON } from "./ayudasCarbon";
import { ErrorBloque } from "@/components/ui/ErrorBloque";

/** Parametros con los que se corrio el modelo y advertencias de uso (siempre visibles, no ocultas en una ayuda). */
export function SupuestosCarbon() {
  const { datos, error } = useValidacionCarbon();

  if (error) return <ErrorBloque que="los supuestos" mensaje={error} />;
  if (!datos) return <SkeletonChart />;

  return (
    <Card>
      <CardHeader title="Supuestos y limitaciones" subtitle="Léelos antes de usar la proyección" ayuda={AYUDAS_CARBON.supuestos} />
      <div className="space-y-4 px-5 pb-5 pt-4">
        <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2">
          {datos.supuestos.map((s) => (
            <div key={s.nombre} className="border-t border-border pt-2">
              <dt className="text-[11px] font-semibold uppercase tracking-wide text-foreground-muted">{s.nombre}</dt>
              <dd>{s.valor}</dd>
            </div>
          ))}
        </dl>
        <ul className="list-disc space-y-1 pl-5 text-xs text-foreground-muted">
          <li>Las bandas P10–P90 son <b>escenarios</b> de ENOS y aportes, no intervalos de confianza estadísticos.</li>
          <li>Es una proyección de apoyo a la decisión: no reemplaza el despacho ni el análisis operativo de XM.</li>
          <li>Si el ENOS o los aportes se desvían de lo supuesto, el resultado cambia; vuelve a correr el modelo con datos nuevos.</li>
        </ul>
      </div>
    </Card>
  );
}
