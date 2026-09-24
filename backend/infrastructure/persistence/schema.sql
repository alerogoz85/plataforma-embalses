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
