"use client";

import { TableroModelo } from "@/components/modelos/TableroModelo";
import { CargandoTablero } from "@/components/ui/CargandoTablero";
import { useCatalogoEscenariosApagon, useFichaModelo } from "@/lib/hooks/useModelos";
import { GemeloApagon } from "./GemeloApagon";

const TITULO = "Riesgo de apagón condicionado por ENOS";

/**
 * Tablero de riesgo de apagón. Con los escenarios del modelo importados es el visor interactivo (controles a la izquierda);
 * sin ellos —o si el catálogo no responde— queda el tablero genérico de modelos, que dice qué falta y cómo cargarlo.
 */
export function TableroApagon() {
  const catalogo = useCatalogoEscenariosApagon();
  const ficha = useFichaModelo("apagon");

  if (catalogo.cargando) return <CargandoTablero titulo={TITULO} />;
  if (catalogo.datos?.disponible) return <GemeloApagon catalogo={catalogo.datos} ficha={ficha.datos} />;
  return <TableroModelo modeloId="apagon" titulo={TITULO} />;
}
