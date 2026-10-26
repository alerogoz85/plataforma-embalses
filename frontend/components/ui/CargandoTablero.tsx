import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { SkeletonChart, SkeletonKpiCard } from "@/components/ui/Skeleton";

/**
 * Se muestra mientras el navegador lee la dirección (los filtros viven en la URL). Next exige un `Suspense` por encima de
 * cualquier componente que lea los parámetros; así el encabezado y el pie ya aparecen y el contenido se rellena enseguida.
 */
export function CargandoTablero({ titulo }: { titulo: string }) {
  return (
    <div className="flex min-h-full flex-col">
      <Header titulo={titulo} subtitulo="Cargando…" />
      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 px-4 py-6 sm:px-6" aria-busy="true">
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonKpiCard key={i} />
          ))}
        </section>
        <SkeletonChart />
      </main>
      <Footer>Tableros Analíticos · Ministerio de Minas y Energía</Footer>
    </div>
  );
}
