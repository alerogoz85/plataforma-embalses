import type { ReactNode } from "react";

type Ayuda = { titulo: string; contenido: ReactNode };

/** Textos de los botones ⓘ del visor de riesgo de apagón. */
export const AYUDAS_APAGON = {
  modoOni: {
    titulo: "Modo de ONI",
    contenido: (
      <p>
        <b>Pronóstico ENOS (NOAA/CPC)</b> usa el pronóstico probabilístico del fenómeno de El Niño que el modelo trae incorporado.{" "}
        <b>Manual</b> fija el ONI que elijas con el deslizador, para ver «qué pasaría si» el fenómeno fuera de esa intensidad.
      </p>
    ),
  },
  oni: {
    titulo: "ONI objetivo (°C)",
    contenido: (
      <p>
        El ONI es la anomalía de temperatura del Pacífico que define El Niño (positivo) y La Niña (negativo). Aquí va de −2,5 a +2,5 °C. Cada valor
        tiene su propia corrida del modelo Monte Carlo, ya calculada.
      </p>
    ),
  },
  simulaciones: {
    titulo: "Simulaciones Monte Carlo",
    contenido: <p>Cuántas trayectorias simula el modelo en cada corrida. Con más simulaciones las probabilidades son más estables y la corrida es más pesada.</p>,
  },
  horizonte: {
    titulo: "Horizonte (meses)",
    contenido: <p>Cuántos meses hacia adelante muestra el escenario, contados desde el mes siguiente al último dato de demanda.</p>,
  },
  peorIndice: {
    titulo: "Peor índice de riesgo",
    contenido: (
      <p>
        El índice (0-100) combina la probabilidad de déficit, la de apagón severo, el déficit relativo y el estrés del margen de reserva. Aquí se muestra el mes
        con el valor más alto del horizonte.
      </p>
    ),
  },
  mesesRojo: {
    titulo: "Meses en ROJO",
    contenido: <p>Meses del horizonte en que el semáforo del modelo (margen de reserva y probabilidad de déficit) queda en rojo.</p>,
  },
  mapaCalor: {
    titulo: "Mapa de calor",
    contenido: (
      <p>
        Déficit esperado de energía (MWh) por mes y franja horaria. El modelo reparte el balance mensual con perfiles históricos de la forma del día; sirve para ver{" "}
        <b>en qué franja</b> se concentra el riesgo, no para predecir un evento puntual.
      </p>
    ),
  },
} satisfies Record<string, Ayuda>;
