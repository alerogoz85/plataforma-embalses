import type { Ayuda } from "@/components/dashboard/ayudas";

/**
 * Textos de ayuda (boton ⓘ) del tablero de carbon termico. Estan separados de los componentes
 * para poder revisarlos y editarlos sin tocar la logica, igual que las ayudas del tablero de embalses.
 */
export const AYUDAS_CARBON = {
  filtroHistoria: {
    titulo: "Filtro de historia",
    contenido: (
      <p>
        Cuántos meses de consumo observado se dibujan antes de la proyección en el gráfico principal: 12, 36, 60 o toda la
        historia disponible. No cambia la proyección, las tarjetas ni los demás gráficos.
      </p>
    ),
  },
  filtroHorizonte: {
    titulo: "Filtro de horizonte",
    contenido: (
      <p>
        Cuántos meses hacia adelante se proyectan (1, 3, 6 o 9; el modelo publica como máximo 9: oct-2026 a jun-2027).
        Aplica a las tarjetas, al gráfico principal, a los trimestres, al inventario y a la comparación con XM. El pico y
        la probabilidad se calculan solo dentro del horizonte elegido.
      </p>
    ),
  },
  filtroUnidad: {
    titulo: "Unidad del consumo",
    contenido: (
      <p>
        El modelo estima la <b>energía</b> del carbón (GBTU/día). Para verla como <b>masa</b> (kt/día) se divide por el poder
        calorífico del carbón (26,27 MBTU/t). Cambia las tarjetas y los gráficos de consumo; el inventario siempre está en
        kt (miles de toneladas).
      </p>
    ),
  },
  filtroInventario: {
    titulo: "Días de inventario",
    contenido: (
      <p>
        Días de consumo que se quieren tener almacenados como reserva (15, 30, 45 o 60). El inventario requerido de cada mes
        es el consumo diario esperado multiplicado por estos días; se muestra el escenario central (P50) y el adverso (P90).
      </p>
    ),
  },
  picoEsperado: {
    titulo: "Pico esperado de consumo",
    contenido: (
      <p>
        Mes de mayor consumo de carbón térmico esperado (escenario central P50) dentro del horizonte. Debajo se muestra su
        rango P10–P90: son <b>escenarios</b> (de ENOS y de aportes), no un intervalo de confianza estadístico.
      </p>
    ),
  },
  usoTecho: {
    titulo: "Uso del techo térmico",
    contenido: (
      <>
        <p>
          Porcentaje de la capacidad máxima de consumo (techo) que usaría el sistema en el mes del pico, en el escenario P50.
          Semáforo: <b>holgado</b> por debajo de 85 %, <b>ajustado</b> de 85 a 100 % y <b>supera el techo</b> por encima de 100 %.
        </p>
        <p className="mt-2">El techo físico se muestra como línea en el gráfico principal.</p>
      </>
    ),
  },
  probabilidadRecord: {
    titulo: "Probabilidad de superar el récord",
    contenido: (
      <p>
        De las simulaciones Monte Carlo del modelo, qué porcentaje supera el máximo mensual observado en la historia en el
        mes del pico. Es una probabilidad condicionada a los supuestos del modelo (ENOS y aportes), no una predicción cierta.
      </p>
    ),
  },
  inventarioPico: {
    titulo: "Inventario requerido en el pico",
    contenido: (
      <p>
        Toneladas de carbón (en kt) que habría que tener almacenadas en el mes del pico para cubrir los días de inventario
        elegidos. Se indica el valor del escenario central (P50) y el del adverso (P90).
      </p>
    ),
  },
  graficoPrincipal: {
    titulo: "Consumo de carbón: historia y proyección",
    contenido: (
      <>
        <p>
          Línea azul: consumo mensual observado. Línea oscura: proyección central (P50). Banda: escenarios entre P10 y P90.
        </p>
        <p className="mt-2">
          Las dos líneas horizontales son el <b>techo</b> térmico y el <b>récord histórico</b> mensual. Si la banda las cruza,
          existe un escenario en que el consumo las supera.
        </p>
      </>
    ),
  },
  trimestres: {
    titulo: "Consumo por trimestre",
    contenido: (
      <p>
        Carbón total esperado en cada trimestre (millones de toneladas, escenario P50) con su rango P10–P90. Los trimestres
        que no caben completos en el horizonte elegido se muestran atenuados porque su total es parcial.
      </p>
    ),
  },
  inventario: {
    titulo: "Inventario de carbón requerido",
    contenido: (
      <p>
        Por mes: kt de carbón necesarios para sostener los días de inventario elegidos, según el consumo del escenario
        central (P50) y del adverso (P90). Sirve para dimensionar compras y almacenamiento.
      </p>
    ),
  },
  comparacionXm: {
    titulo: "Comparación con la proyección de XM",
    contenido: (
      <p>
        Pone el consumo del modelo (P50 y banda) junto al caso estocástico de XM. Si el caso de XM supera el techo físico,
        conviene consultar con XM el supuesto detrás de esa cifra antes de usarla como referencia.
      </p>
    ),
  },
  validacion: {
    titulo: "Validación del modelo",
    contenido: (
      <p>
        Resultado de evaluar el modelo contra lo ocurrido: error medio (MAE) frente a métodos ingenuos, episodios críticos
        pasados y una lista de criterios de validez. Un criterio «no cumple» es una limitación real que hay que conocer al
        usar la proyección.
      </p>
    ),
  },
  supuestos: {
    titulo: "Supuestos y limitaciones",
    contenido: (
      <p>
        Parámetros con los que se corrió el modelo y advertencias de uso. Las proyecciones dependen de la trayectoria del
        fenómeno ENOS y de los aportes hídricos: si esas condiciones cambian, el resultado cambia.
      </p>
    ),
  },
} satisfies Record<string, Ayuda>;
