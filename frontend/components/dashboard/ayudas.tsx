import type { ReactNode } from "react";

export interface Ayuda {
  titulo: string;
  contenido: ReactNode;
}

export const AYUDAS = {
  filtroRegion: {
    titulo: "Filtro de región",
    contenido: (
      <p>
        Limita los indicadores, la distribución regional y la tabla a los embalses de una región
        hidrológica. Al cambiar de región se selecciona automáticamente el primer embalse de esa
        región. La senda de largo plazo tiene su propio selector.
      </p>
    ),
  },
  filtroEmbalse: {
    titulo: "Filtro de embalse",
    contenido: (
      <p>
        Elige el embalse que se muestra en el gráfico principal (serie histórica y proyección).
        Solo lista los embalses de la región seleccionada. También puedes elegirlo haciendo clic en
        una fila de la tabla.
      </p>
    ),
  },
  filtroDesde: {
    titulo: "Fecha inicial",
    contenido: (
      <p>
        Primer día de la serie histórica del gráfico principal. Por defecto son los últimos 180
        días. No afecta los indicadores, que siempre usan el último corte disponible, ni la senda
        mensual.
      </p>
    ),
  },
  filtroHasta: {
    titulo: "Fecha final",
    contenido: (
      <p>
        Último día de la serie histórica del gráfico principal. La proyección ML siempre parte del
        último dato disponible, aunque esta fecha sea anterior.
      </p>
    ),
  },
  pctVolumenUtilNacional: {
    titulo: "% Volumen útil nacional",
    contenido: (
      <>
        <p>
          Porcentaje de la capacidad útil de los embalses que está llena hoy (volumen útil ÷ capacidad
          útil publicados por XM). Coincide con el agregado oficial del SIN.
        </p>
        <p>
          Cada embalse pesa según su capacidad útil en energía (GWh), como hace XM, y no según su
          volumen en Mm³. Incluye el agregado Bogotá. Los deltas son la variación en puntos
          porcentuales (p.p.) frente a ayer y hace 7 días.
        </p>
      </>
    ),
  },
  aportes: {
    titulo: "Aportes (% media histórica)",
    contenido: (
      <>
        <p>
          Aportes hídricos de los ríos que alimentan a los embalses (m³/s) comparados con su media
          histórica: total de aportes ÷ total de la media, solo entre embalses con serie publicada
          (Muna y el agregado Bogotá no la tienen).
        </p>
        <p>100% = año típico; menos de 100% indica un periodo más seco de lo normal.</p>
      </>
    ),
  },
  capacidadGuardada: {
    titulo: "Capacidad guardada",
    contenido: (
      <>
        <p>
          Energía almacenada hoy en el volumen útil de los embalses, en GWh: es la métrica
          &quot;Volumen útil diario energía&quot; que publica XM, sumada entre embalses.
        </p>
        <p>Si XM no publica la energía de un embalse ese día, no se suma.</p>
      </>
    ),
  },
  riesgoSistema: {
    titulo: "Riesgo del sistema",
    contenido: (
      <>
        <p>Clasificación del %V. útil nacional:</p>
        <ul className="list-disc pl-4">
          <li>Óptimo: entre 30% y 95%</li>
          <li>Alerta de sequía: entre 15% y 30%</li>
          <li>Crítico: menos de 15%</li>
          <li>Reboce: 95% o más (riesgo de vertimiento)</li>
        </ul>
      </>
    ),
  },
  graficoPrincipal: {
    titulo: "%V. útil vs. aportes y proyección ML",
    contenido: (
      <>
        <p>
          Serie diaria histórica del embalse seleccionado: % de volumen útil (línea sólida) y
          aportes como % de la media histórica (puede superar 100%).
        </p>
        <p>
          La línea punteada es la proyección a 1, 3, 6 o 12 meses. Es la del modelo de largo plazo
          (Prophet + XGBoost con escenarios climáticos ENSO), la misma de la senda, con sus valores
          mensuales unidos por interpolación lineal (cada valor es el promedio de su mes, situado
          a mitad de mes); la banda son los escenarios P10–P90, angosta al inicio. Nace en el
          último dato y llega hasta donde publica el modelo (unos 12 meses).
        </p>
        <p>
          Si el embalse no tiene proyección publicada (Agregado Bogotá), se usa Holt-Winters
          (tendencia amortiguada, solo ve la serie histórica); su banda es un intervalo de
          confianza del 95% por simulación Monte Carlo.
        </p>
      </>
    ),
  },
  distribucionRegional: {
    titulo: "Distribución regional del %V. útil",
    contenido: (
      <p>
        %V. útil agregado por región hidrológica según la clasificación de XM (Antioquia, Caldas,
        Caribe, Centro, Oriente, Valle), ponderado por capacidad en energía, de menor a mayor. El
        color sigue la clasificación de riesgo: azul óptimo, ámbar alerta, rojo crítico o reboce.
      </p>
    ),
  },
  senda: {
    titulo: "Senda del volumen útil",
    contenido: (
      <>
        <p>
          Trayectoria mensual (promedio de los valores diarios de cada mes) del %V. útil observado y
          su proyección a 1, 3, 6 o 12 meses. &quot;Total nacional&quot; es el agregado ponderado por
          energía, igual al oficial de XM.
        </p>
        <p>
          La proyección es la del modelo de largo plazo (Prophet + XGBoost) que incorpora los
          escenarios climáticos ENSO (El Niño/La Niña) simulados por Monte Carlo; cubre 12 meses. La
          banda muestra los escenarios P10–P90. Para un embalse sin proyección publicada (Agregado
          Bogotá) se usa un respaldo estadístico, Holt-Winters de 12 periodos, que solo ve la serie
          histórica y no incorpora clima: léelo como la forma estacional esperada.
        </p>
      </>
    ),
  },
  ultimoObservado: {
    titulo: "Último observado",
    contenido: <p>Valor mensual más reciente de %V. útil que entra al modelo como dato real.</p>,
  },
  minimoProyectado: {
    titulo: "Mínimo proyectado",
    contenido: (
      <>
        <p>Mes con el %V. útil esperado más bajo dentro del horizonte proyectado.</p>
        <p>Semáforo de la senda: rojo por debajo de 55%, ámbar por debajo de 65%, verde desde 65%.</p>
      </>
    ),
  },
  validacion: {
    titulo: "Validación walk-forward",
    contenido: (
      <>
        <p>
          Solo aplica al respaldo Holt-Winters. Backtest honesto: para cada uno de los últimos 6
          meses se entrena solo con datos previos y se predice ese mes, sin usar información futura.
        </p>
        <p>
          MAE: error absoluto medio en puntos porcentuales (menor es mejor). R²: proporción de la
          variación explicada; 1 es perfecto y un valor negativo es peor que predecir el promedio.
          La persistencia (repetir el último valor) es la línea base que el modelo debe superar.
        </p>
      </>
    ),
  },
  tablaEmbalses: {
    titulo: "Tabla de embalses",
    contenido: (
      <p>
        Último dato publicado por XM para cada embalse. &quot;Agregado&quot; marca el agregado
        Bogotá, que XM publica como una sola entidad. Haz clic en un encabezado para ordenar y en
        una fila para ver su serie y proyección arriba. CSV/JSON descargan la serie histórica.
      </p>
    ),
  },
  horizonteDiario: {
    titulo: "Horizonte del pronóstico",
    contenido: (
      <p>
        Meses hacia adelante que proyecta el modelo desde el último dato: 1, 3, 6 o 12 (meses de
        30 días). A mayor horizonte, más se ensancha la banda de confianza porque crece la
        incertidumbre y, con la tendencia amortiguada, la curva se aplana.
      </p>
    ),
  },
  selectorSenda: {
    titulo: "Embalse de la senda",
    contenido: (
      <p>
        &quot;Total nacional&quot; es el agregado ponderado de todos los embalses; también puedes
        ver la senda de un embalse individual. Este selector es independiente de los filtros de
        arriba.
      </p>
    ),
  },
  horizonteSenda: {
    titulo: "Horizonte de la senda",
    contenido: (
      <p>
        Meses hacia adelante que proyecta la senda: 1, 3, 6 o 12. La proyección arranca en el mes
        siguiente al último mes observado. Si la corrida del modelo de largo plazo publica menos
        meses de los pedidos, se muestran los publicados y se avisa.
      </p>
    ),
  },
  valModelo: {
    titulo: "Modelo",
    contenido: (
      <>
        <p>
          Persistencia: predice que el mes siguiente será igual al último observado; es la línea
          base ingenua.
        </p>
        <p>
          Holt-Winters estacional: el modelo de la senda. Solo aporta valor si supera a la
          persistencia.
        </p>
      </>
    ),
  },
  valMae: {
    titulo: "MAE",
    contenido: (
      <p>
        Error absoluto medio: cuántos puntos porcentuales de %V. útil se equivoca en promedio el
        modelo en los últimos 6 meses. Menor es mejor.
      </p>
    ),
  },
  valR2: {
    titulo: "R²",
    contenido: (
      <p>
        Proporción de la variación real que el modelo explica. 1 es perfecto, 0 equivale a predecir
        siempre el promedio y un valor negativo es peor que eso.
      </p>
    ),
  },
  colEmbalse: {
    titulo: "Embalse",
    contenido: <p>Nombre del embalse. Haz clic en la fila para ver su serie y proyección arriba.</p>,
  },
  colRegion: {
    titulo: "Región",
    contenido: <p>Subsistema hidrológico al que pertenece: Antioquia, Centro, Oriente, Valle o Caribe.</p>,
  },
  colReporte: {
    titulo: "Reporte",
    contenido: (
      <p>
        Descarga la serie histórica diaria del embalse en CSV o JSON: %V. útil, energía
        útil, aportes, vertimientos y turbinado (vacío si XM no publica el dato).
      </p>
    ),
  },
  colPctVolumen: {
    titulo: "% Vol. útil",
    contenido: <p>Porcentaje de agua útil almacenada, con su nivel de riesgo (óptimo, alerta, crítico o reboce).</p>,
  },
  colAportes: {
    titulo: "Aportes (% media)",
    contenido: (
      <p>
        Caudal del día de la serie de río asociada al embalse, como % de su media histórica. &quot;—&quot;
        si XM no publica serie de aportes para ese embalse.
      </p>
    ),
  },
  colVertimientos: {
    titulo: "Vertimientos m³/s",
    contenido: <p>Caudal que se descarga sin generar energía, normalmente cuando el embalse está casi lleno. Dato de XM (m³/día convertido a m³/s).</p>,
  },
  colTurbinado: {
    titulo: "Turbinado m³/s",
    contenido: <p>Caudal que pasa por las turbinas para generar energía en el día. Dato de XM (descarga turbinada, m³/día convertido a m³/s).</p>,
  },
  colEnergiaUtil: {
    titulo: "Energía útil GWh",
    contenido: <p>Energía almacenada en el volumen útil del embalse, según XM. &quot;—&quot; si XM no la publicó ese día.</p>,
  },
  colAutonomia: {
    titulo: "Autonomía (días)",
    contenido: (
      <>
        <p>
          Estimación de los días que tardaría el embalse en agotar su volumen útil si el balance de
          hoy se mantiene: volumen útil ÷ (turbinado + vertimientos − aportes). No incluye
          evaporación porque XM no la publica.
        </p>
        <p>
          &quot;—&quot; significa que los aportes superan las salidas o que falta algún dato. Ojo: los aportes
          son solo los del río asociado; en embalses de una cadena (p. ej. Punchiná, que recibe agua
          turbinada aguas arriba) el resultado puede ser engañosamente bajo.
        </p>
      </>
    ),
  },
} satisfies Record<string, Ayuda>;
