"use client";

import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { ErrorBloque } from "@/components/ui/ErrorBloque";
import { SkeletonChart } from "@/components/ui/Skeleton";
import type { ModeloAnalitico } from "@/lib/api/types";
import { useFichaModelo, useResultadosModelo } from "@/lib/hooks/useModelos";
import { ETIQUETA_ESTADO } from "@/lib/utils/modelos";
import { DatosDocumentados } from "./DatosDocumentados";
import { EstadoModeloCard } from "./EstadoModeloCard";
import { FichaPanel } from "./FichaPanel";
import { ResultadosPanel } from "./ResultadosPanel";
import { SinResultadosCard } from "./SinResultadosCard";

/**
 * Tablero de un modelo analítico con ficha (gas, optimización o apagón). Misma estructura que los demás tableros:
 * encabezado -> estado -> (resultados con filtros | cifras documentadas + cómo cargarlos) -> ficha.
 * El contenido sale de la API: la ficha de los documentos del modelo y, si se importaron, sus resultados.
 */
export function TableroModelo({ modeloId, titulo }: { modeloId: ModeloAnalitico; titulo: string }) {
  const ficha = useFichaModelo(modeloId);
  const resultados = useResultadosModelo(modeloId);
  const f = ficha.datos;
  const hay = resultados.datos?.disponible ? resultados.datos.resultado : null;

  return (
    <div className="flex min-h-full flex-col">
      <Header titulo={titulo} subtitulo={f ? ETIQUETA_ESTADO[f.estado] : "Cargando modelo…"} />

      <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col gap-5 px-4 py-6 sm:px-6">
        {ficha.error && <ErrorBloque que="la ficha del modelo" mensaje={ficha.error} />}
        {!f && !ficha.error && <SkeletonChart />}

        {f && (
          <>
            <EstadoModeloCard ficha={f} />

            {resultados.error && <ErrorBloque que="los resultados" mensaje={resultados.error} />}
            {!resultados.datos && !resultados.error && <SkeletonChart />}

            {resultados.datos && (hay ? <ResultadosPanel resultado={hay} /> : (
              <>
                <DatosDocumentados datos={f.datos_documentados} />
                <SinResultadosCard ficha={f} />
              </>
            ))}

            {hay && <DatosDocumentados datos={f.datos_documentados} />}
            <FichaPanel ficha={f} />
          </>
        )}
      </main>

      <Footer>
        Fuente: documentos y salidas del modelo (CRISP-DM) del Ministerio de Minas y Energía. La plataforma muestra solo lo que el modelo entregó.
      </Footer>
    </div>
  );
}
