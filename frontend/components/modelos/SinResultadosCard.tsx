"use client";

import { Card, CardHeader } from "@/components/ui/Card";
import type { FichaModelo } from "@/lib/api/types";
import { AYUDAS_MODELOS } from "./ayudasModelos";

/**
 * Lo que se muestra mientras el modelo no tiene resultados importados: qué archivos de salida se esperan y el comando
 * para cargarlos. Es un estado normal del tablero, no un error.
 */
export function SinResultadosCard({ ficha }: { ficha: FichaModelo }) {
  return (
    <Card>
      <CardHeader title="Aún no hay resultados cargados" subtitle="Esta plataforma solo muestra lo que el modelo entregó" ayuda={AYUDAS_MODELOS.sinResultados} />
      <div className="space-y-4 px-5 pb-5 pt-3 text-sm">
        <div>
          <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Archivos que se esperan</h3>
          <ul className="space-y-2">
            {ficha.archivos_esperados.map((a) => (
              <li key={a.ruta}>
                <code className="rounded bg-[var(--color-marca-bg)] px-1.5 py-0.5 text-xs">{a.ruta}</code>
                <span className="block text-xs text-foreground-muted">{a.contenido}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-foreground-muted">Para cargarlos (desde la carpeta backend, con la API detenida)</h3>
          <pre className="overflow-x-auto rounded-lg border border-border bg-background p-3 text-xs" tabIndex={0} aria-label="Comando de importación">
            <code>{ficha.comando_importacion}</code>
          </pre>
          <p className="mt-1.5 text-xs text-foreground-muted">
            El importador valida todo antes de escribir y reemplaza solo el resultado de este modelo. Después hay que volver a publicar la API.
          </p>
        </div>
      </div>
    </Card>
  );
}
