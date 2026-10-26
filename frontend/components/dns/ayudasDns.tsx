import type { Ayuda } from "@/components/dashboard/ayudas";

/**
 * Textos de ayuda (botón ⓘ) del tablero de demanda no atendida (DNS). Están separados de los
 * componentes para poder revisarlos y editarlos sin tocar la lógica.
 */
export const AYUDAS_DNS = {
  filtroPeriodo: {
    titulo: "Filtro de período",
    contenido: (
      <p>
        Cuántos meses de historia se analizan, contados hacia atrás desde el mes del último evento (12, 36, 60 o todo el
        histórico desde 2013). Aplica a las tarjetas, la serie mensual, los patrones y las causas. No cambia el índice de
        zonas, los cambios de reporte ni el modelo, que son resultados sobre todo el histórico.
      </p>
    ),
  },
  filtroRegion: {
    titulo: "Filtro de región",
    contenido: (
      <p>
        Limita el tablero a las subáreas operativas de una región. Al cambiarla, el filtro de subárea vuelve a «Todas». «Sin
        asignar» agrupa subáreas que SIMEM no ubica en una región.
      </p>
    ),
  },
  filtroSubarea: {
    titulo: "Filtro de subárea",
    contenido: (
      <p>
        Una subárea operativa del sistema (la unidad con que XM reporta los eventos). Solo lista las de la región elegida;
        también puedes elegirla con un clic en una barra del ranking de zonas.
      </p>
    ),
  },
  filtroOrigen: {
    titulo: "Filtro de origen",
    contenido: (
      <p>
        <b>Programada</b>: el evento estaba planeado (p. ej. mantenimiento con consignación). <b>No programada</b>: ocurrió
        sin aviso (disparos, fallas). Afecta a los gráficos de eventos; el pronóstico del modelo no se separa por origen y
        no se muestra cuando este filtro está activo.
      </p>
    ),
  },
  eventos: {
    titulo: "Eventos DNS",
    contenido: (
      <p>
        Cantidad de eventos de demanda no atendida (DNS) en el período, según los filtros. La variación compara con el período
        anterior de igual duración: un aumento es desfavorable. Los eventos EDAC (desconexión automática de carga) son otra
        cosa y se cuentan aparte.
      </p>
    ),
  },
  energia: {
    titulo: "Energía no atendida",
    contenido: (
      <p>
        Suma de la energía que el sistema dejó de suministrar en los eventos (GWh = millones de kWh). Unos pocos eventos
        grandes pesan mucho: por eso se muestra también el porcentaje de eventos críticos.
      </p>
    ),
  },
  criticos: {
    titulo: "Eventos críticos",
    contenido: (
      <p>
        Porcentaje de eventos que dejaron sin atender <b>100 MWh (100.000 kWh) o más</b>. Es el umbral que usa el modelo para
        marcar un evento como crítico.
      </p>
    ),
  },
  noProgramados: {
    titulo: "Eventos no programados",
    contenido: (
      <p>
        Porcentaje de eventos que no estaban planeados, sobre los que informan su origen. Los programados son sobre todo
        mantenimientos; los no programados son los que sorprenden a la operación.
      </p>
    ),
  },
  serie: {
    titulo: "Serie mensual y pronóstico",
    contenido: (
      <>
        <p>
          Barras: eventos o energía de cada mes (el mes del corte está atenuado porque aún no termina). El punto del{" "}
          <b>pronóstico</b> es lo que el modelo predictivo estima para ese mes, sumando las subáreas del filtro.
        </p>
        <p className="mt-2">
          Un salto en 2024-2025 viene en buena parte de cambios en la forma de reportar de varias subáreas (ver «Cambios en la
          forma de reportar»), no necesariamente de más fallas.
        </p>
      </>
    ),
  },
  zonas: {
    titulo: "Priorización de zonas",
    contenido: (
      <>
        <p>
          Índice 0-100 que combina magnitud de la energía no atendida (40 %), frecuencia de eventos (20 %), criticidad (20 %) y
          tendencia reciente (20 %). Los pesos son una decisión editorial documentada, no un resultado estadístico.
        </p>
        <p className="mt-2">
          Rojo: la energía de los últimos 24 meses empeoró frente a los 24 anteriores. Se calcula sobre todo el histórico y no
          cambia con el período ni el origen.
        </p>
      </>
    ),
  },
  patrones: {
    titulo: "Patrones en el tiempo",
    contenido: (
      <p>
        Cuándo ocurren los eventos: por hora, por día de la semana y por franja del día. Se excluyen los eventos con «hora
        desconocida» (00:00:00 exacto), que SIMEM guarda cuando no se capturó la hora real y no son un pico de medianoche.
      </p>
    ),
  },
  causas: {
    titulo: "Causas de los eventos",
    contenido: (
      <p>
        Causa de cada evento: la reportada por el operador o, si falta, inferida del texto de la descripción con reglas y un
        modelo TF-IDF (validado contra lectura manual). Los «sin clasificar» no se pudieron inferir y se muestran como
        causa desconocida.
      </p>
    ),
  },
  cambiosReporte: {
    titulo: "Cambios en la forma de reportar",
    contenido: (
      <p>
        Subáreas cuyo reporte cambió de metodología: aparecen muchas más descripciones genéricas y se sabe menos de la causa.
        Un aumento de eventos después de ese mes puede ser un cambio de registro y no un deterioro real del sistema.
      </p>
    ),
  },
  modelo: {
    titulo: "Modelo predictivo",
    contenido: (
      <p>
        Pronostica, por subárea, cuántos eventos y cuánta energía habrá el mes siguiente. Se evalúa contra la persistencia
        (suponer que el mes siguiente será igual al actual): un modelo que no la supera no se reporta como exitoso. MAE es el
        error medio absoluto y RMSE penaliza más los errores grandes.
      </p>
    ),
  },
} satisfies Record<string, Ayuda>;
