import Link from "next/link";

import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { RUTAS } from "@/lib/rutas";
import { TABLEROS } from "@/lib/tableros";

/**
 * Página 404 de toda la aplicación: una dirección que no existe lleva aquí, con el camino de vuelta al panel y la lista de
 * tableros disponibles (sale del registro, así que nunca queda desactualizada).
 */
export default function NoEncontrada() {
  return (
    <div className="flex min-h-full flex-col">
      <Header titulo="Tableros Analíticos" subtitulo="Ministerio de Minas y Energía" enlacePanel={false} />
      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-14 sm:px-6">
        <div>
          <p className="text-sm font-semibold" style={{ color: "var(--color-marca)" }}>
            Error 404
          </p>
          <h2 className="mt-1 text-3xl font-extrabold" style={{ color: "var(--color-marca-oscuro)" }}>
            No encontramos esa página
          </h2>
          <p className="mt-3 text-base leading-relaxed text-foreground-muted">
            La dirección no corresponde a ningún tablero. Puede que esté mal escrita o que el enlace haya cambiado.
          </p>
        </div>
        <nav aria-label="Tableros disponibles" className="flex flex-col gap-2">
          <Link
            href={RUTAS.panel}
            className="inline-flex h-10 w-fit items-center rounded-lg px-4 text-sm font-semibold text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-marca)]"
            style={{ backgroundColor: "var(--color-marca)" }}
          >
            Ir al panel de tableros
          </Link>
          <p className="mt-3 text-sm font-semibold">O ir directo a un tablero:</p>
          <ul className="grid grid-cols-1 gap-1.5 text-sm sm:grid-cols-2">
            {TABLEROS.map((t) => (
              <li key={t.id}>
                <Link href={t.ruta} className="underline-offset-2 hover:underline" style={{ color: "var(--color-marca-oscuro)" }}>
                  {t.titulo}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </main>
      <Footer>Tableros Analíticos del Ministerio de Minas y Energía</Footer>
    </div>
  );
}
