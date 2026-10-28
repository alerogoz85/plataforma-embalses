import { Card, CardHeader } from "@/components/ui/Card";
import type { ResultadoCarga } from "@/lib/api/types";

/** Resultado de revisar (o aplicar) los archivos: qué se va a cargar, los errores (con su motivo) y las advertencias. */
export function InformeCarga({ resultado, errores }: { resultado: ResultadoCarga | null; errores?: string[] }) {
  const lista = errores ?? resultado?.errores ?? [];
  const valido = resultado?.valido === true && lista.length === 0;
  const color = valido ? "var(--color-optimo)" : "var(--color-critico)";
  const fondo = valido ? "var(--color-optimo-bg)" : "var(--color-critico-bg)";

  return (
    <Card aria-live="polite">
      <CardHeader
        title={resultado?.aplicada ? "Tablero actualizado" : valido ? "Los archivos son válidos" : "Hay que corregir los archivos"}
        subtitle={resultado?.aplicada ? "Los datos nuevos ya se ven en el tablero." : valido ? "Revisa el resumen y, si es lo esperado, aplica la actualización." : "No se guardó nada."}
      />
      <div className="flex flex-col gap-4 px-5 pb-5 pt-3">
        <span className="inline-flex w-fit rounded-full px-2.5 py-1 text-xs font-semibold" style={{ color, backgroundColor: fondo }}>
          {resultado?.aplicada ? "Aplicada" : valido ? "Válidos" : `${lista.length} problema${lista.length === 1 ? "" : "s"}`}
        </span>
        {lista.length > 0 && (
          <ul className="list-disc space-y-1.5 pl-5 text-sm" style={{ color: "var(--color-critico)" }}>
            {lista.map((e, i) => (
              <li key={`${i}-${e}`}>{e}</li>
            ))}
          </ul>
        )}
        {resultado && resultado.resumen.length > 0 && (
          <dl className="grid grid-cols-1 gap-x-6 gap-y-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
            {resultado.resumen.map((d) => (
              <div key={d.etiqueta} className="border-t border-border pt-2">
                <dt className="text-[11px] font-semibold uppercase tracking-wide text-foreground-muted">{d.etiqueta}</dt>
                <dd className="break-words">{d.valor}</dd>
              </div>
            ))}
          </dl>
        )}
        {resultado && resultado.advertencias.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-foreground-muted">Advertencias del modelo</p>
            <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
              {resultado.advertencias.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Card>
  );
}
