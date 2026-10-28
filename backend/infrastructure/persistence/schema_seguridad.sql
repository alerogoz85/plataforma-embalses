-- Seguridad del modulo de actualizacion: usuarios, sesiones y bitacora. SQL comun a DuckDB y Postgres.
-- Las contraseñas se guardan solo como hash (scrypt) y las sesiones solo como huella (sha256) del token.
CREATE TABLE IF NOT EXISTS seg_usuarios (
    nombre_usuario VARCHAR NOT NULL, nombre VARCHAR NOT NULL, rol VARCHAR NOT NULL, tableros VARCHAR NOT NULL,
    activo BOOLEAN NOT NULL, hash_contrasena VARCHAR NOT NULL, intentos_fallidos INTEGER NOT NULL, bloqueado_hasta TIMESTAMP
);

CREATE TABLE IF NOT EXISTS seg_sesiones (
    huella_token VARCHAR NOT NULL, nombre_usuario VARCHAR NOT NULL, token_csrf VARCHAR NOT NULL,
    creada_en TIMESTAMP NOT NULL, ultima_actividad TIMESTAMP NOT NULL, ip VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS seg_auditoria (
    momento TIMESTAMP NOT NULL, nombre_usuario VARCHAR NOT NULL, accion VARCHAR NOT NULL, tablero VARCHAR,
    resultado VARCHAR NOT NULL, detalle VARCHAR NOT NULL, ip VARCHAR NOT NULL
);
