import type { Ayuda } from "@/components/dashboard/ayudas";

/**
 * Textos de ayuda (botón ⓘ) de los tableros de modelos analíticos (gas, optimización, apagón).
 * Son comunes porque estos tableros comparten estructura: ficha documentada + resultados importados.
 */
export const AYUDAS_MODELOS = {
  estado: {
    titulo: "Estado del modelo",
    contenido: (
      <>
        <p>
          Dice honestamente en qué punto está el modelo según sus propios documentos. <b>Sin resultados publicados</b>: hay método
          y código, pero no una corrida final. <b>Prueba técnica</b>: hay corridas de verificación que el propio modelo marca como
          no publicables. <b>Con resultados importados</b>: se cargaron las salidas del modelo y se muestran abajo.
        </p>
        <p className="mt-2">La plataforma nunca completa con cifras inventadas lo que el modelo no entregó.</p>
      </>
    ),
  },
  datosDocumentados: {
    titulo: "Cifras documentadas",
    contenido: (
      <p>
        Datos que ya están escritos en los documentos del modelo (tamaño de los datos, número de pruebas, parámetros). No son resultados
        calculados por esta plataforma; cada tarjeta dice de qué documento sale.
      </p>
    ),
  },
  sinResultados: {
    titulo: "Cómo cargar los resultados",
    contenido: (
      <p>
        Cuando el modelo genere sus archivos de salida, se importan con el comando indicado (con la API local detenida) y luego se
        vuelve a publicar la API. El importador valida los archivos antes de escribir nada: si algo no cuadra, no se importa.
      </p>
    ),
  },
  filtroPeriodo: {
    titulo: "Filtro de período",
    contenido: (
      <p>
        Recorta todas las series mensuales de los gráficos al rango de meses elegido (Desde y Hasta, ambos incluidos). Las tablas muestran
        el resultado completo del modelo.
      </p>
    ),
  },
  indicadores: {
    titulo: "Indicadores del resultado",
    contenido: (
      <p>
        Resumen calculado por el modelo en su última corrida importada. El color indica el nivel: verde normal, ámbar de atención y rojo
        crítico, según la propia salida del modelo.
      </p>
    ),
  },
  series: {
    titulo: "Series del modelo",
    contenido: (
      <p>
        Cada gráfico es una serie que entregó el modelo. Si trae banda (P10-P90) son escenarios simulados, no un intervalo de confianza
        estadístico: P10 es un escenario favorable y P90 uno adverso.
      </p>
    ),
  },
  tablas: {
    titulo: "Tablas del modelo",
    contenido: <p>Tablas tal como las dejó el modelo (con los valores redondeados). Una celda vacía es un dato que el modelo no entregó, no un cero.</p>,
  },
  ficha: {
    titulo: "Ficha del modelo",
    contenido: (
      <p>
        Resume los entregables del modelo (CRISP-DM): qué pregunta responde, cómo lo hace, con qué datos, hasta dónde llega y qué
        limitaciones reconoce. Se redactó a partir de esos documentos y se actualiza cuando ellos cambian.
      </p>
    ),
  },
  advertencias: {
    titulo: "Advertencias",
    contenido: <p>Condiciones que cambian cómo se debe leer el resultado. Léelas antes de usar las cifras.</p>,
  },
} satisfies Record<string, Ayuda>;
