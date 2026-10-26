"""Fichas de los modelos analiticos, redactadas a partir de sus propios documentos (CRISP-DM).

Todo lo que dice una ficha sale de los entregables del modelo: aqui no se calcula ni se estima nada.
Cuando un documento aclara que no hay resultados, la ficha lo dice. Si cambia un documento, se edita
la ficha; si el modelo entrega resultados, se importan con `importar_resultado_modelo` y el tablero los
muestra junto a la ficha."""
from __future__ import annotations

from typing import Optional

from domain.entities.modelo_analitico import (
    ESTADO_PRUEBA_TECNICA,
    ESTADO_SIN_RESULTADOS,
    ArchivoEsperado,
    DatoDocumentado,
    FichaModelo,
    SeccionFicha,
)
from domain.repositories.modelo_analitico_repository import FichaModeloRepository

_COMANDO = (
    'python -m infrastructure.ingesta.importar_resultado_modelo --modelo {modelo} --carpeta "{carpeta}"'
)

GAS = FichaModelo(
    id="gas",
    titulo="Gas natural: oferta declarada frente a gas fiscalizado",
    resumen=(
        "Compara la oferta de gas que los agentes declaran al Ministerio con el gas que la ANH fiscaliza y "
        "comercializa por campo, y evalúa si las curvas de declinación de Arps sirven para anticipar esa oferta."
    ),
    estado=ESTADO_SIN_RESULTADOS,
    estado_detalle=(
        "El análisis de curvas de declinación (Arps) está implementado y se probó a nivel nacional para validar la mecánica, "
        "pero los insumos entregados no incluyen el libro de resultados ni las gráficas de una ejecución. El documento de "
        "modelamiento reconoce que el nivel nacional «no representa una unidad física de declinación» y que no se emiten "
        "métricas ni se selecciona un modelo final sin fabricar resultados numéricos."
    ),
    estado_detalle_con_resultados=(
        "Hay resultados importados de la corrida más reciente: pronóstico coherente por campo y nacional (v2), curvas de declinación de las "
        "declaraciones y backtesting de las declaraciones frente al gas observado. Los documentos (18 de septiembre de 2026) son anteriores a esos "
        "resultados y solo describían el prototipo nacional; las cifras de abajo salen de los archivos de resultados, no de los documentos."
    ),
    documentos="Actividades 1 a 5 (definición, negocio, datos, preparación y modelamiento), 18 de septiembre de 2026",
    pregunta=(
        "¿En qué medida las declaraciones mensuales de oferta de gas natural anticipan el comportamiento del gas fiscalizado "
        "y comercializado por campo, y qué capacidad adicional ofrecen las curvas de declinación para evaluar y proyectar esa oferta?"
    ),
    secciones=(
        SeccionFicha("Qué se busca", (
            "Integrar la producción fiscalizada de la ANH y las declaraciones de oferta del MME conservando la dimensión de campo.",
            "Medir la magnitud, dirección y persistencia de la brecha entre lo declarado y lo comercializado.",
            "Ajustar modelos exponencial, hiperbólico y armónico de Arps a la fase de declinación de cada campo y compararlos con las declaraciones mediante MAE, MAPE, RMSE y BIAS con validación temporal.",
            "Producir resultados por campo y agregados nacionales para el seguimiento de la oferta y la planeación energética.",
        )),
        SeccionFicha("Método", (
            "Variable observada: gas comercializado de la ANH en MPCD (suma de ENVIADO A PLANTA, GAS TRANSFORMADO y ENTREGADO A GASEODUCTOS, dividida por los días del mes).",
            "Referencia prospectiva: oferta declarada al MME en MPCD, por cohorte de declaración (cada una proyecta hasta 120 meses).",
            "Curvas de Arps (b = 0 exponencial, 0 < b < 1 hiperbólica, b = 1 armónica) ajustadas sobre el gas comercializado observado y proyectadas hasta completar el horizonte de cada cohorte.",
            "La validación real solo usa meses con dato fiscalizado observado fuera de la ventana de ajuste.",
            "Pronóstico (script 4, v2): una sola variable base, el gas fiscalizado, con ETS de tendencia amortiguada para el total nacional y los 15 campos de mayor producción; el comercializado y el entregado a gasoducto se derivan con proporciones fijas (p1 y p2) para que las tres variables sean coherentes y comparables. Intervalo empírico al 80 % tomado del backtest.",
            "Validación: backtest de origen móvil que mide MAE, WAPE, MASE y sesgo frente al pronóstico ingenuo; las curvas de Arps hiperbólicas se reportan solo como referencia de declinación.",
            "Backtesting de las declaraciones: se compara lo declarado por cada cohorte con el gas comercializado observado, por año de declaración y por horizonte.",
        )),
        SeccionFicha("Datos y fuentes", (
            "ANH — producción fiscalizada (Producción Mpcpd) y Campos Mpcpd: mensual por campo, desde enero de 2013 hasta julio de 2026.",
            "MME — declaración de gas (declaracionGas) y ficha de campo: cohortes de 2015 a 2026 con periodos mensuales hasta diciembre de 2035.",
            "Catálogo maestro de campos entre ANH y MME: aún por construir y validar.",
            "Los meses posteriores a julio de 2026 son valores declarados o proyectados, nunca observados.",
        )),
        SeccionFicha("Alcance", (
            "Unidad de análisis: campo por mes; el total nacional es una vista de referencia, no el nivel definitivo de ajuste.",
            "No se modelan demanda, precios, capacidad de transporte, reservas certificadas ni variables petrofísicas.",
            "No se asumen ceros donde una fuente no reporta información.",
        )),
        SeccionFicha("Limitaciones documentadas", (
            "La brecha entre fuentes no es automáticamente un error de pronóstico: el gas comercializado excluye gas lift, reinyección, quema y consumo en campo, mientras que la declaración se aproxima a la oferta total.",
            "Incluir GAS TRANSFORMADO en el gas comercializado tiene riesgo de doble conteo y está pendiente de validación.",
            "El poder calorífico mezcla valores cercanos a 1 y a 1.000, y cidv llega a 50.000.000: hay que normalizarlos antes de comparar.",
            "Hay 200 registros negativos en ENVIADO A PLANTA y duplicados por socio y cohorte en declaracionGas.",
            "Sin identificador maestro de campos no se puede cruzar con certeza ANH y MME (cambios de nombre, contrato y codificación).",
        )),
        SeccionFicha("Siguientes pasos", (
            "Construir y validar el catálogo de equivalencias de campos.",
            "Definir criterios mínimos de historia y estabilidad para ajustar cada campo.",
            "Ejecutar el ajuste por campo y consolidar de abajo hacia arriba el agregado nacional.",
            "Entregar el libro de resultados de la ejecución para importarlo a esta plataforma.",
        )),
    ),
    datos_documentados=(
        DatoDocumentado("Registros de origen", "1.176.419", "En cuatro conjuntos de datos, antes de la preparación (declaracionGas concentra el 91,2 %).", "Actividad 3"),
        DatoDocumentado("Producción fiscalizada", "ene-2013 a jul-2026", "Serie mensual de la ANH por campo.", "Actividad 1"),
        DatoDocumentado("Cohortes de declaración", "12", "Años 2015 a 2026, cada una con hasta 120 meses.", "Actividad 5"),
        DatoDocumentado("Modelos de declinación", "3", "Exponencial, hiperbólico y armónico (Arps).", "Actividad 5"),
    ),
    archivos_esperados=(
        ArchivoEsperado("Resultados/pronostico_v2/Pronostico_Gas_v2.xlsx",
                        "Hojas Info, Resumen, Pronostico, Proporciones, Backtest, Arps hiperbolica, Declarado nacional e Historico (script 4 v2): pronóstico por campo y nacional."),
        ArchivoEsperado("Resultados/pronostico_dca/Pronostico_DCA_Declaraciones.xlsx",
                        "Hojas Info, Parametros, Proyeccion mensual, Metricas vs MME, Metricas vs ANH real y Resumen (script 8). Opcional."),
        ArchivoEsperado("Resultados/backtesting/backtest_resumen_global.csv",
                        "Backtesting de las declaraciones: resumen global y por año de declaración (backtest_por_anio_declaracion.csv). Opcional."),
        ArchivoEsperado("Resultados/comparacion/resumen_comparacion_por_anio.csv", "Comparación entre lo declarado y lo comercializado por año de declaración. Opcional."),
    ),
    comando_importacion=_COMANDO.format(modelo="gas", carpeta="../../3. Modelo gas fiscalizado y declarado"),
    carpeta_proyecto="3. Modelo gas fiscalizado y declarado",
)

OPTIMIZACION = FichaModelo(
    id="optimizacion",
    titulo="Optimización hidrotérmica estocástica (SDDP)",
    resumen=(
        "Implementación agregada de planeación hidro-térmica con Programación Dinámica Dual Estocástica (SDDP) y riesgo CVaR, "
        "con escenarios condicionados por ENOS, para explorar cuánta térmica usar, cuánta agua conservar y qué costo y riesgo implica."
    ),
    estado=ESTADO_PRUEBA_TECNICA,
    estado_detalle=(
        "La evaluación técnica (versión del 2 de septiembre de 2026) es favorable para el alcance actual: análisis exploratorio, "
        "metodológico y de sensibilidad. Pero la corrida de modelamiento del 30 de julio de 2026 es una prueba técnica clasificada "
        "INSUFFICIENT_RISK_SAMPLE y publishable = false: usa escenarios de aportes idénticos, una sola iteración y una cola efectiva "
        "de una observación (mínimo provisional: 40). Por eso E[costo], VaR y CVaR no son evidencia económica ni soportan una recomendación de despacho."
    ),
    estado_detalle_con_resultados=(
        "Hay una corrida importada. Sigue valiendo la advertencia de los documentos: la evaluación técnica (2 de septiembre de 2026) respalda el "
        "análisis exploratorio, metodológico y de sensibilidad, y una corrida marcada como no publicable no es evidencia económica ni soporte de "
        "despacho. Mira las advertencias de abajo."
    ),
    documentos="Documento 4 de modelamiento (30 de julio de 2026) y evaluación técnica del estado actual (2 de septiembre de 2026)",
    pregunta="Ante un escenario ENOS, ¿cuánta generación térmica conviene utilizar, cuánta agua conservar y qué costo y riesgo implica?",
    secciones=(
        SeccionFicha("Qué se busca", (
            "Evolucionar de un prototipo exploratorio a un núcleo SDDP formal y agregado del Sistema Interconectado Nacional.",
            "Relacionar aportes, almacenamiento equivalente, generación hidráulica y térmica, energía no servida (ENS), costo y riesgo bajo escenarios ENOS.",
        )),
        SeccionFicha("Método", (
            "Programación lineal multietapa resuelta con SDDP: estado intertemporal, decisiones hidro-térmicas agregadas y restricciones de balance.",
            "Función de costo futuro aproximada con cortes tipo Benders, con pasadas forward y backward e información dual.",
            "Riesgo con CVaR anidado y escenarios de aportes condicionados por ENOS.",
            "Evaluación fuera de muestra (OOS) y un wrapper v002 que formaliza entradas, validaciones, procedencia (manifiesto y hashes) y contrato de salida.",
        )),
        SeccionFicha("Datos y trazabilidad", (
            "Carga histórica con 1.230 fechas comunes entre el 31 de enero de 2023 y el 13 de julio de 2026, sin nulos en las métricas de salida, sin fechas duplicadas y sin volúmenes superiores a la capacidad.",
            "Hay una discontinuidad temporal de 31 días que debe considerarse al elegir ventanas.",
            "La prueba de modelamiento usó 570 días (31 de enero de 2023 a 22 de agosto de 2024) y construyó 82 etapas semanales; los balances energético e hídrico cerraron dentro de tolerancia.",
        )),
        SeccionFicha("Alcance", (
            "Escala agregada del sistema: no representa centrales individuales, costos de combustible por unidad, restricciones de gas, rampas ni red.",
            "No es una orden vinculante de despacho; los resultados representan el sistema parametrizado, no costos u ofertas oficiales por recurso.",
            "La capa de consulta (dashboard y API) lee resultados ya calculados y no ejecuta el modelo durante una solicitud.",
        )),
        SeccionFicha("Limitaciones documentadas", (
            "Parte de los parámetros económicos y físicos son supuestos o proxies.",
            "Pruebas: de una muestra controlada de 50 casos en 13 módulos, 41 finalizaron y 9 no se completaron por dependencias ausentes, datos locales requeridos o compatibilidad de versión (no son evidencia de falla del algoritmo).",
            "La evaluación OOS usa 10 caminos; los 800 caminos configurados no se reportan como resultado final ejecutado, así que las métricas de cola no son estables.",
            "El archivo de datos por embalse no está incorporado en la ruta actual.",
            "Los alias de la capa de consulta apuntan sobre todo a salidas v001 mientras existen salidas v002.",
        )),
        SeccionFicha("Oportunidades de evolución", (
            "Aumentar la escala de evaluación OOS para estimar métricas de cola con estabilidad estadística.",
            "Alinear los alias del dashboard y la API con las salidas más recientes.",
            "Reconstruir de forma controlada el archivo por embalse si se amplía el análisis a esa granularidad.",
            "Mantener una matriz que distinga valores observados, supuestos y proxies.",
        )),
    ),
    datos_documentados=(
        DatoDocumentado("Casos de prueba satisfactorios", "41 de 50", "Muestra controlada de 13 módulos; los 9 restantes fueron bloqueos del entorno.", "Evaluación técnica"),
        DatoDocumentado("Suite de pruebas", "26 módulos · 176 métodos", "Capa de verificación automatizada identificada en el producto.", "Evaluación técnica"),
        DatoDocumentado("Etapas del modelo", "82 semanales", "Referencia de escala; configuración con 50 caminos de entrenamiento y 800 de evaluación.", "Documento 4"),
        DatoDocumentado("Fechas comunes de datos", "1.230", "Del 31-ene-2023 al 13-jul-2026, sin nulos ni duplicados.", "Evaluación técnica"),
    ),
    archivos_esperados=(
        ArchivoEsperado("05_resultados/resumen.json", "Resumen de la corrida (indicadores y clasificación, p. ej. publishable)."),
        ArchivoEsperado("05_resultados/validacion_tecnica.json", "Verificaciones técnicas y balances de la corrida. Opcional."),
        ArchivoEsperado("05_resultados/manifest.json", "Manifiesto con procedencia y hashes. Opcional."),
    ),
    comando_importacion=_COMANDO.format(modelo="optimizacion", carpeta="../../4. Modelo optimización/ENTREGA_DOCUMENTO_4_MODELAMIENTO_20260730"),
    carpeta_proyecto="4. Modelo optimización",
)

APAGON = FichaModelo(
    id="apagon",
    titulo="Riesgo de apagón condicionado por ENOS",
    resumen=(
        "Modelo Monte Carlo nacional que estima, mes a mes, el riesgo de déficit de generación del SIN bajo escenarios El Niño/La Niña, "
        "con probabilidad de déficit, margen de reserva, un índice de riesgo de 0 a 100 y un semáforo."
    ),
    estado=ESTADO_SIN_RESULTADOS,
    estado_detalle=(
        "El modelo (script 6) y su evaluación (script 7) están implementados, pero los documentos aclaran que no se dispone de una corrida "
        "final con el detalle mensual de probabilidades y semáforos, ni de un reporte de ejecución de la evaluación. Por eso no se atribuyen "
        "valores de riesgo a meses concretos."
    ),
    estado_detalle_con_resultados=(
        "Hay una corrida importada (modo probabilístico, 3.000 simulaciones, 18 meses desde septiembre de 2026). Los documentos (actividades 1 a 6) "
        "describen el modelo pero no reportan esta corrida; el semáforo y las probabilidades de abajo salen de sus archivos de resultados. Sigue sin haber "
        "un reporte de ejecución de la evaluación (script 7)."
    ),
    documentos="Actividades 1 a 6 del estudio (definición, contexto sectorial, exploración, base analítica, modelamiento y evaluación)",
    pregunta=(
        "¿Qué probabilidad tiene el SIN de no cubrir la demanda con su generación disponible en cada mes del horizonte, según la evolución del fenómeno ENOS?"
    ),
    secciones=(
        SeccionFicha("Qué se busca", (
            "Construir escenarios ENOS probabilísticos y proyectar generación por tecnología condicionada por el estado hídrico.",
            "Recalcular la demanda combinando historia, proyección UPME y sensibilidad a ONI.",
            "Estimar el déficit mensual, su concentración por franjas horarias y un índice de riesgo con semáforo mensual.",
        )),
        SeccionFicha("Método", (
            "Simulación Monte Carlo (3.000 trayectorias, horizonte de 18 meses, semilla 20260729) que genera una distribución por mes, no una sola trayectoria.",
            "ENOS: cadena de Markov de tres regímenes anclada al pronóstico categórico de NOAA/CPC cuando existe; modo manual con un ONI fijo para explorar escenarios.",
            "Embalses y generación hidráulica por regresión sobre ONI y estacionalidad; renovables por factor de capacidad estacional; disponibilidad térmica con distribución Beta(6,3).",
            "Demanda: tendencia log-lineal más proyección UPME con peso creciente (de 30 % en el mes 1 a 80 % desde el mes 12).",
            "Balance: hidro y renovables cubren primero, la térmica cubre el residual hasta su techo y el déficit es el máximo entre cero y demanda menos oferta.",
            "Riesgo: probabilidad de déficit (> 3 %), de déficit severo (> 15 %), margen de reserva, índice ponderado 0-100 y semáforo VERDE / AMARILLO / ROJO.",
        )),
        SeccionFicha("Datos y fuentes", (
            "ONI histórico de 317 meses (enero de 2000 a mayo de 2026) y pronósticos de NOAA/CPC.",
            "Demanda histórica (66 meses de observaciones reales para calibrar) y proyección de la UPME.",
            "Embalses, generación por tecnología y capacidad vigente, tomados de las fuentes integradas en la base analítica del estudio.",
        )),
        SeccionFicha("Alcance", (
            "Nivel nacional agregado: mide adecuación de generación, no probabilidad nodal de racionamiento por restricciones de red.",
            "La desagregación horaria reparte un balance mensual ya cerrado: sirve para ver en qué franja se concentra el riesgo de un mes de estrés, no para predecir un evento puntual.",
        )),
        SeccionFicha("Limitaciones documentadas", (
            "Sin restricciones de transporte ni datos de red: un déficit nacional en cero no descarta racionamientos localizados.",
            "La disponibilidad térmica está calibrada con muy pocos episodios históricos de estrés real: es uno de los supuestos más fuertes.",
            "La sensibilidad de la demanda a ONI suele ser débil; si no pasa la prueba de significancia se fija en cero.",
            "La capacidad vigente se asume constante en todo el horizonte; no hay calendario de festivos.",
            "Los umbrales del semáforo son un punto de partida, no una réplica de la metodología de Cargo por Confiabilidad de la CREG.",
        )),
        SeccionFicha("Siguientes pasos", (
            "Conservar el resumen mensual, el detalle por franjas y los metadatos de cada corrida que se quiera publicar.",
            "Ejecutar la evaluación (script 7) y guardar su reporte para documentar los criterios aprobados.",
            "Importar los resultados a esta plataforma cada vez que haya una corrida nueva (hoy hay una importada).",
        )),
    ),
    datos_documentados=(
        DatoDocumentado("Simulaciones por corrida", "3.000", "Trayectorias Monte Carlo; horizonte por defecto de 18 meses.", "Actividad 5"),
        DatoDocumentado("Historia de ONI", "317 meses", "Enero de 2000 a mayo de 2026; persistencia de régimen de 87 % a 90 %.", "Actividad 5"),
        DatoDocumentado("Demanda para calibrar", "66 meses", "Sensibilidad a ONI positiva y significativa en la corrida de referencia (β ≈ +0,0104; p ≈ 7×10⁻⁵).", "Actividad 5"),
        DatoDocumentado("Franjas horarias", "5", "Madrugada, mañana, tarde, pico de la noche y noche.", "Actividad 6"),
    ),
    archivos_esperados=(
        ArchivoEsperado("Resultados/resultados_modelo_riesgo_apagon/resumen_mensual.csv",
                        "Percentiles de ONI, embalse, demanda y oferta; probabilidades de déficit; margen de reserva, índice y semáforo por mes."),
        ArchivoEsperado("Resultados/resultados_modelo_riesgo_apagon/detalle_franjas_horarias.csv", "Probabilidad y déficit esperado por mes y franja. Opcional."),
        ArchivoEsperado("Resultados/resultados_modelo_riesgo_apagon/metadatos_corrida.json", "Metadatos de la corrida (modo ONI, capacidad vigente, calibraciones). Opcional."),
        ArchivoEsperado("Resultados/resultados_modelo_riesgo_apagon/configuracion_corrida.json", "Parámetros de la corrida. Opcional."),
    ),
    comando_importacion=_COMANDO.format(modelo="apagon", carpeta="../../5. Modelo apagón"),
    carpeta_proyecto="5. Modelo apagón",
)

FICHAS: dict[str, FichaModelo] = {f.id: f for f in (GAS, OPTIMIZACION, APAGON)}


class FichasEnCodigo(FichaModeloRepository):
    """Fichas del catalogo de este modulo (solo lectura)."""

    def obtener(self, modelo_id: str) -> Optional[FichaModelo]:
        return FICHAS.get(modelo_id)
