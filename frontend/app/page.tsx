import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { TableroCard } from "@/components/panel/TableroCard";
import { RUTAS } from "@/lib/rutas";
import { GRUPOS, tablerosDelGrupo, type GrupoTablero } from "@/lib/tableros";

const ORDEN_GRUPOS: readonly GrupoTablero[] = ["datos", "desarrollo"];

/**
 * Panel principal («Tableros Analíticos»): punto de entrada a todos los tableros. Página de servidor sin datos dinámicos.
 *
 * Estructura de contenido: 1) qué es y cómo se usa, en dos frases; 2) los tableros con datos; 3) los modelos en desarrollo,
 * separados para no dar el mismo peso a lo que ya muestra resultados y a lo que aún no; 4) la guía. La lista sale de `lib/tableros.ts`.
 */
export default function PanelPage() {
  return (
    <div className="flex min-h-full flex-col">
      <Header titulo="Tableros Analíticos" subtitulo="Ministerio de Minas y Energía" enlacePanel={false} />

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-10 px-4 py-10 sm:px-6">
        <section aria-labelledby="titulo-panel" className="flex flex-col gap-3">
          <h2 id="titulo-panel" className="text-3xl font-extrabold" style={{ color: "var(--color-marca-oscuro)" }}>
            Elige un tablero
          </h2>
          <p className="max-w-2xl text-base leading-relaxed text-foreground-muted">
            Cada tablero tiene sus filtros, ayudas ⓘ y la fecha de corte de sus datos. Los filtros quedan en la dirección de la página:
            copia el enlace para compartir la vista exacta que estás viendo.
          </p>
        </section>

        {ORDEN_GRUPOS.map((grupo) => (
          <section key={grupo} aria-labelledby={`grupo-${grupo}`} className="flex flex-col gap-4">
            <div>
              <h2 id={`grupo-${grupo}`} className="text-lg font-bold">
                {GRUPOS[grupo].titulo}
              </h2>
              <p className="mt-0.5 max-w-2xl text-sm text-foreground-muted">{GRUPOS[grupo].descripcion}</p>
            </div>
            <ul className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3" aria-label={GRUPOS[grupo].titulo}>
              {tablerosDelGrupo(grupo).map((tablero) => (
                <li key={tablero.id}>
                  <TableroCard tablero={tablero} />
                </li>
              ))}
            </ul>
          </section>
        ))}

        <aside className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-background-elevated px-5 py-4">
          <p className="max-w-xl text-sm text-foreground-muted">
            ¿Primera vez? La guía explica cómo se cargan y calculan los datos y cómo leer cada tablero, con capturas.
          </p>
          <a
            href={RUTAS.informacion}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-9 items-center rounded-lg border px-3 text-xs font-semibold transition-colors hover:bg-marca hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
            style={{ borderColor: "var(--color-marca)", color: "var(--color-marca)" }}
          >
            Abrir la guía técnica y el manual
          </a>
        </aside>
      </main>

      <Footer>Tableros Analíticos del Ministerio de Minas y Energía · Datos públicos de XM y SIMEM y modelos propios</Footer>
    </div>
  );
}
