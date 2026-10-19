CREATE TABLE IF NOT EXISTS embalses (
    id           VARCHAR PRIMARY KEY,
    nombre       VARCHAR NOT NULL,
    region       VARCHAR NOT NULL,
    es_agregado  BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS mediciones (
    embalse_id                   VARCHAR NOT NULL,
    fecha                        DATE NOT NULL,
    volumen_util_mm3             DOUBLE NOT NULL,
    capacidad_util_mm3           DOUBLE NOT NULL,
    energia_util_gwh             DOUBLE,
    capacidad_util_energia_gwh   DOUBLE NOT NULL,
    aportes_m3s                  DOUBLE,
    aportes_media_historica_m3s  DOUBLE,
    vertimientos_m3s             DOUBLE,
    turbinado_m3s                DOUBLE,
    PRIMARY KEY (embalse_id, fecha)
);

CREATE INDEX IF NOT EXISTS idx_mediciones_fecha ON mediciones (fecha);

CREATE TABLE IF NOT EXISTS fuente_datos (
    id              INTEGER PRIMARY KEY,
    fuente          VARCHAR NOT NULL,
    descripcion     VARCHAR NOT NULL,
    fecha_corte     DATE NOT NULL,
    actualizado_en  TIMESTAMP NOT NULL,
    es_real         BOOLEAN NOT NULL
);

-- Proyeccion de largo plazo publicada por el modelo de Outputs (Prophet + XGBoost
-- con escenarios ENSO). No proviene de SIMEM/XM: se carga con
-- infrastructure.ingesta.importar_proyeccion y --reiniciar no la borra.
CREATE TABLE IF NOT EXISTS proyecciones_senda (
    embalse_id       VARCHAR NOT NULL,
    mes              DATE NOT NULL,
    limite_inferior  DOUBLE NOT NULL,
    valor_esperado   DOUBLE NOT NULL,
    limite_superior  DOUBLE NOT NULL,
    origen           VARCHAR NOT NULL,
    PRIMARY KEY (embalse_id, mes)
);

-- Modelo de carbon termico (proyeccion Monte Carlo del consumo de carbon del SIN, su
-- validacion y la comparacion con XM). Se carga con
-- infrastructure.ingesta.importar_modelo_carbon y --reiniciar no lo borra. Cada corrida
-- reemplaza todas estas tablas a la vez, dentro de una transaccion. No llevan PRIMARY KEY
-- porque DuckDB no permite borrar e insertar la misma clave en una transaccion; la unicidad
-- de fechas y claves la valida PaqueteModeloCarbon. Aportes y uso del techo van en % (0-100).
CREATE TABLE IF NOT EXISTS carbon_meta (
    id                       INTEGER NOT NULL,
    origen                   VARCHAR NOT NULL,
    poder_calorifico_mbtu_t  DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_historico (
    fecha              DATE NOT NULL,
    carbon_gbtu_dia    DOUBLE NOT NULL,
    techo_gbtu_dia     DOUBLE,
    uso_techo_pct      DOUBLE,
    aportes_pct_media  DOUBLE,
    roni               DOUBLE,
    fuente             VARCHAR NOT NULL,
    mes_completo       BOOLEAN NOT NULL,
    dias_con_dato      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_proyeccion (
    fecha DATE NOT NULL, dias INTEGER NOT NULL, techo_gbtu_dia DOUBLE NOT NULL,
    roni_p10 DOUBLE NOT NULL, roni_p50 DOUBLE NOT NULL, roni_p90 DOUBLE NOT NULL,
    aportes_p10 DOUBLE NOT NULL, aportes_p50 DOUBLE NOT NULL, aportes_p90 DOUBLE NOT NULL,
    uso_p10 DOUBLE NOT NULL, uso_p50 DOUBLE NOT NULL, uso_p90 DOUBLE NOT NULL,
    carbon_p10 DOUBLE NOT NULL, carbon_p50 DOUBLE NOT NULL, carbon_p90 DOUBLE NOT NULL,
    kt_mes_p10 DOUBLE NOT NULL, kt_mes_p50 DOUBLE NOT NULL, kt_mes_p90 DOUBLE NOT NULL,
    prob_supera_maximo_pct DOUBLE NOT NULL,
    observado_parcial_gbtu_dia DOUBLE
);

CREATE TABLE IF NOT EXISTS carbon_trimestres (
    trimestre VARCHAR NOT NULL, meses INTEGER NOT NULL,
    mt_p10 DOUBLE NOT NULL, mt_p50 DOUBLE NOT NULL, mt_p90 DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_inventario (
    fecha DATE NOT NULL, dias_inventario INTEGER NOT NULL,
    kt_p50 DOUBLE NOT NULL, kt_p90 DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_comparacion_xm (
    fecha DATE NOT NULL, techo_gbtu_dia DOUBLE NOT NULL,
    modelo_p10 DOUBLE NOT NULL, modelo_p50 DOUBLE NOT NULL, modelo_p90 DOUBLE NOT NULL,
    xm_estocastico_gbtu_dia DOUBLE,
    xm_historicas_min_gbtu_dia DOUBLE, xm_historicas_max_gbtu_dia DOUBLE
);

CREATE TABLE IF NOT EXISTS carbon_error_horizonte (
    horizonte_meses INTEGER NOT NULL, pronosticos INTEGER NOT NULL,
    mae_modelo DOUBLE NOT NULL, mae_persistencia DOUBLE NOT NULL,
    mae_estacional DOUBLE NOT NULL, mae_climatologia DOUBLE NOT NULL, sesgo_modelo DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_episodios (
    episodio VARCHAR NOT NULL, inicio DATE NOT NULL, fin DATE NOT NULL, meses INTEGER NOT NULL,
    real_gbtu_dia DOUBLE NOT NULL, p50_gbtu_dia DOUBLE NOT NULL, error_total_pct DOUBLE NOT NULL,
    mae_modelo DOUBLE NOT NULL, mae_ingenuo DOUBLE NOT NULL, cobertura_p10_p90_pct DOUBLE NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_veredicto (
    orden INTEGER NOT NULL, criterio VARCHAR NOT NULL, resultado VARCHAR NOT NULL,
    cumple BOOLEAN NOT NULL, interpretacion VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS carbon_supuestos (
    orden INTEGER NOT NULL, nombre VARCHAR NOT NULL, valor VARCHAR NOT NULL
);
