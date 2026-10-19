import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { TableroCard } from "@/components/panel/TableroCard";
import { TABLEROS } from "@/lib/tableros";

/**
 * Panel principal: punto de entrada a los tableros de la plataforma.
 * Es una pagina de servidor sin datos dinamicos; la lista sale de `lib/tableros.ts`.
 */
export default function PanelPage() {
  return (
    <div className="flex min-h-full flex-col">
      <Header
        titulo="Plataforma de Tableros Analíticos"
        subtitulo="Ministerio de Minas y Energía"
        enlacePanel={false}
      />

      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-4 py-10 sm:px-6">
        <section aria-labelledby="titulo-panel" className="flex flex-col gap-3">
          <h1 id="titulo-panel" className="text-3xl font-extrabold" style={{ color: "var(--color-marca-oscuro)" }}>
            Tableros
          </h1>
          <p className="max-w-2xl text-base leading-relaxed text-foreground-muted">
            Elige un tablero para consultar su información. Cada uno tiene sus propios filtros, ayudas contextuales y
            la fecha de corte de sus datos. La guía técnica y el manual de usuario están en «Información», arriba a la
            derecha.
          </p>
        </section>

        <section aria-label="Tableros disponibles" className="grid grid-cols-1 gap-5 md:grid-cols-2">
          {TABLEROS.map((tablero) => (
            <TableroCard key={tablero.id} tablero={tablero} />
          ))}
        </section>
      </main>

      <Footer>Tableros analíticos del Ministerio de Minas y Energía · Datos públicos de XM y SIMEM y modelos propios</Footer>
    </div>
  );
}
