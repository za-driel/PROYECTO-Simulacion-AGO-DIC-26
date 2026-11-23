-- =====================================================================
-- Simulador de examen de inglés - Esquema de base de datos (SQLite)
-- Versión corregida a partir del diagrama original.
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---------- Catálogos ------------------------------------------------
CREATE TABLE niveles (
    nivel_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_nivel  TEXT    NOT NULL UNIQUE,          -- Básico / Intermedio / Avanzado
    orden         INTEGER NOT NULL UNIQUE           -- 1 = más bajo
);

CREATE TABLE usuarios (
    usuario_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    correo          TEXT NOT NULL UNIQUE,           -- identificador de login
    password_hash   TEXT NOT NULL,                  -- NUNCA la contraseña en claro
    fecha_registro  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------- Banco de preguntas ---------------------------------------
CREATE TABLE preguntas (
    pregunta_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nivel_id        INTEGER NOT NULL
                    REFERENCES niveles(nivel_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    texto_pregunta  TEXT NOT NULL UNIQUE,
    imagen_url      TEXT                            -- opcional (apoyo visual)
);
CREATE INDEX ix_preguntas_nivel ON preguntas(nivel_id);

-- Opciones separadas (antes: opcion_a..opcion_d dentro de preguntas = grupo repetitivo)
CREATE TABLE opciones (
    opcion_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    pregunta_id  INTEGER NOT NULL
                 REFERENCES preguntas(pregunta_id) ON DELETE CASCADE,
    letra        TEXT    NOT NULL CHECK (letra IN ('a','b','c','d')),
    texto        TEXT    NOT NULL,
    es_correcta  INTEGER NOT NULL DEFAULT 0 CHECK (es_correcta IN (0,1)),
    UNIQUE (pregunta_id, letra)
);
-- Exactamente una opción correcta por pregunta
CREATE UNIQUE INDEX ux_opciones_una_correcta ON opciones(pregunta_id) WHERE es_correcta = 1;

-- ---------- Simulador de práctica (20 preguntas, máx. 5 intentos) -----
CREATE TABLE intentos_practica (
    intento_practica_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id           INTEGER NOT NULL
                         REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
    numero_intento       INTEGER NOT NULL CHECK (numero_intento BETWEEN 1 AND 5),
    fecha_intento        TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,   -- inicio
    fecha_fin            TEXT,                                          -- NULL = en curso
    calificacion         REAL    CHECK (calificacion IS NULL OR calificacion BETWEEN 0 AND 100),
    aprobado             INTEGER CHECK (aprobado IN (0,1)),
    nivel_resultado_id   INTEGER REFERENCES niveles(nivel_id),
    UNIQUE (usuario_id, numero_intento),
    CHECK (aprobado IS NULL OR calificacion IS NOT NULL),
    CHECK (aprobado IS NULL OR aprobado = (calificacion >= 70))
);

CREATE TABLE detalle_intentos_practica (
    detalle_practica_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    intento_practica_id  INTEGER NOT NULL
                         REFERENCES intentos_practica(intento_practica_id) ON DELETE CASCADE,
    pregunta_id          INTEGER NOT NULL REFERENCES preguntas(pregunta_id),
    orden                INTEGER NOT NULL CHECK (orden BETWEEN 1 AND 20),
    respuesta_dada       TEXT    CHECK (respuesta_dada IN ('a','b','c','d')),  -- NULL = sin responder / tiempo agotado
    es_correcta          INTEGER CHECK (es_correcta IN (0,1)),
    tiempo_respuesta     INTEGER CHECK (tiempo_respuesta BETWEEN 0 AND 60),   -- segundos
    fecha_presentada     TEXT,
    UNIQUE (intento_practica_id, pregunta_id),   -- no repetir pregunta en la misma prueba
    UNIQUE (intento_practica_id, orden)
);
CREATE INDEX ix_detalle_practica_pregunta ON detalle_intentos_practica(pregunta_id);

-- ---------- Simulador final (40 preguntas, máx. 2 intentos) -----------
CREATE TABLE intentos_finales (
    intento_final_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id           INTEGER NOT NULL
                         REFERENCES usuarios(usuario_id) ON DELETE CASCADE,
    numero_intento       INTEGER NOT NULL CHECK (numero_intento BETWEEN 1 AND 2),
    fecha_intento        TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin            TEXT,
    calificacion         REAL    CHECK (calificacion IS NULL OR calificacion BETWEEN 0 AND 100),
    aprobado             INTEGER CHECK (aprobado IN (0,1)),
    nivel_resultado_id   INTEGER REFERENCES niveles(nivel_id),
    UNIQUE (usuario_id, numero_intento),
    CHECK (aprobado IS NULL OR calificacion IS NOT NULL),
    CHECK (aprobado IS NULL OR aprobado = (calificacion >= 70))
);

CREATE TABLE detalle_intentos_finales (
    detalle_final_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    intento_final_id   INTEGER NOT NULL
                       REFERENCES intentos_finales(intento_final_id) ON DELETE CASCADE,
    pregunta_id        INTEGER NOT NULL REFERENCES preguntas(pregunta_id),
    orden              INTEGER NOT NULL CHECK (orden BETWEEN 1 AND 40),
    respuesta_dada     TEXT    CHECK (respuesta_dada IN ('a','b','c','d')),
    es_correcta        INTEGER CHECK (es_correcta IN (0,1)),
    tiempo_respuesta   INTEGER CHECK (tiempo_respuesta BETWEEN 0 AND 60),
    fecha_presentada   TEXT,
    UNIQUE (intento_final_id, pregunta_id),
    UNIQUE (intento_final_id, orden)
);
CREATE INDEX ix_detalle_finales_pregunta ON detalle_intentos_finales(pregunta_id);
