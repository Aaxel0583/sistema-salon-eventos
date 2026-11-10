-- =====================================================================
-- Sistema de Reservaciones y Gestión para Salón de Eventos
-- PKG-06 Base de datos · Script 01 · Esquema (tablas y restricciones)
--
-- Referencias: SDD v2.0 §4.2 (modelo de datos, 3FN)
--              SRS v2.0 §8 (RN-06, RN-07, RN-11, RN-12)
-- Sprint 1 · Se crean las ocho tablas del modelo completo porque la regla
-- RN-04 (Sprint 1) necesita consultar EVENTO. Los triggers de EVENTO
-- (BF001, BF002, BF008) y el procedimiento de pago (BF005) se agregan en
-- los scripts de los Sprints 2 y 3.
--
-- Convenciones: nombres en español y en singular (SDD §1.4); restricciones
-- con nombre explícito (pk_, fk_, uq_, ck_, ix_) para que la capa C-10 pueda
-- traducirlas a mensajes comprensibles (RNF-12).
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- USUARIO · gerentes y clientes (HU-001, HU-002)
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
    id_usuario            SERIAL        NOT NULL,
    nombre                VARCHAR(120)  NOT NULL,
    correo                VARCHAR(120),
    telefono              VARCHAR(20),
    rol                   VARCHAR(10)   NOT NULL,
    clave_hash            VARCHAR(255)  NOT NULL,
    requiere_cambio_clave CHAR(1)       NOT NULL DEFAULT 'S',
    intentos_fallidos     SMALLINT      NOT NULL DEFAULT 0,
    estado                VARCHAR(10)   NOT NULL DEFAULT 'ACTIVO',
    CONSTRAINT pk_usuario            PRIMARY KEY (id_usuario),
    CONSTRAINT uq_usuario_correo     UNIQUE (correo),                       -- RN-07
    CONSTRAINT uq_usuario_telefono   UNIQUE (telefono),                     -- RN-07
    CONSTRAINT ck_usuario_contacto   CHECK (correo IS NOT NULL
                                            OR telefono IS NOT NULL),      -- RN-06
    CONSTRAINT ck_usuario_correo_min CHECK (correo = LOWER(correo)),       -- unicidad sin distinguir mayúsculas
    CONSTRAINT ck_usuario_rol        CHECK (rol IN ('GERENTE', 'CLIENTE')),
    CONSTRAINT ck_usuario_cambio     CHECK (requiere_cambio_clave IN ('S', 'N')),
    CONSTRAINT ck_usuario_intentos   CHECK (intentos_fallidos >= 0),
    CONSTRAINT ck_usuario_estado     CHECK (estado IN ('ACTIVO', 'BLOQUEADO'))
);

-- ---------------------------------------------------------------------
-- SALON · los tres espacios autorizados (HU-003, RD-04)
-- ---------------------------------------------------------------------
CREATE TABLE salon (
    id_salon         SERIAL         NOT NULL,
    nombre           VARCHAR(80)    NOT NULL,
    descripcion      VARCHAR(255),                                          -- RF-14 (ver docs/desviaciones)
    capacidad_maxima INTEGER        NOT NULL,
    costo_renta      NUMERIC(10,2)  NOT NULL,
    disponible       CHAR(1)        NOT NULL DEFAULT 'S',
    CONSTRAINT pk_salon            PRIMARY KEY (id_salon),
    CONSTRAINT uq_salon_nombre     UNIQUE (nombre),
    CONSTRAINT ck_salon_capacidad  CHECK (capacidad_maxima > 0),
    CONSTRAINT ck_salon_costo      CHECK (costo_renta >= 0),
    CONSTRAINT ck_salon_disponible CHECK (disponible IN ('S', 'N'))
);

-- ---------------------------------------------------------------------
-- PLATILLO · elementos del menú por categoría (HU-004, RF-17)
-- ---------------------------------------------------------------------
CREATE TABLE platillo (
    id_platillo SERIAL       NOT NULL,
    nombre      VARCHAR(80)  NOT NULL,
    categoria   VARCHAR(20)  NOT NULL,
    CONSTRAINT pk_platillo           PRIMARY KEY (id_platillo),
    CONSTRAINT uq_platillo_nombre    UNIQUE (nombre),
    CONSTRAINT ck_platillo_categoria CHECK (categoria IN
        ('ENTRADA', 'PLATO_FUERTE', 'GUARNICION', 'POSTRE', 'BEBIDA'))
);

-- ---------------------------------------------------------------------
-- PAQUETE · banquete con precio por persona (HU-004, RF-18, RF-19)
-- ---------------------------------------------------------------------
CREATE TABLE paquete (
    id_paquete     SERIAL         NOT NULL,
    nombre         VARCHAR(80)    NOT NULL,                                 -- ver docs/desviaciones
    precio_persona NUMERIC(10,2)  NOT NULL,
    tipo           VARCHAR(15)    NOT NULL DEFAULT 'ESTANDAR',
    id_cliente     INTEGER,
    CONSTRAINT pk_paquete         PRIMARY KEY (id_paquete),
    CONSTRAINT fk_paquete_cliente FOREIGN KEY (id_cliente)
        REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    CONSTRAINT ck_paquete_precio  CHECK (precio_persona >= 0),
    CONSTRAINT ck_paquete_tipo    CHECK (tipo IN ('ESTANDAR', 'PERSONALIZADO')),
    CONSTRAINT ck_paquete_dueno   CHECK (                                    -- RN-12
        (tipo = 'ESTANDAR'      AND id_cliente IS NULL) OR
        (tipo = 'PERSONALIZADO' AND id_cliente IS NOT NULL))
);

-- PAQUETE_PLATILLO · resuelve la relación N:M (RF-18)
CREATE TABLE paquete_platillo (
    id_paquete  INTEGER NOT NULL,
    id_platillo INTEGER NOT NULL,
    CONSTRAINT pk_paquete_platillo PRIMARY KEY (id_paquete, id_platillo),
    CONSTRAINT fk_pp_paquete  FOREIGN KEY (id_paquete)
        REFERENCES paquete (id_paquete) ON DELETE CASCADE,
    CONSTRAINT fk_pp_platillo FOREIGN KEY (id_platillo)
        REFERENCES platillo (id_platillo) ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------
-- EVENTO · compromiso contratado (HU-005 a HU-009 · reglas en Sprint 2)
-- ---------------------------------------------------------------------
CREATE TABLE evento (
    id_evento       SERIAL         NOT NULL,
    clave_proyecto  VARCHAR(13)    NOT NULL,                                -- EVT-AAAA-NNNN (RN-08)
    nombre_evento   VARCHAR(120),                                           -- RF-28 (ver docs/desviaciones)
    id_cliente      INTEGER        NOT NULL,
    id_gerente      INTEGER,
    id_salon        INTEGER        NOT NULL,
    id_paquete      INTEGER,
    fecha_evento    DATE           NOT NULL,
    hora_inicio     TIME           NOT NULL,
    hora_fin        TIME           NOT NULL,
    num_asistentes  INTEGER        NOT NULL,
    costo_total     NUMERIC(12,2)  NOT NULL,
    estado          VARCHAR(15)    NOT NULL DEFAULT 'COTIZACION',
    finiquitado     CHAR(1)        NOT NULL DEFAULT 'N',
    fecha_finiquito DATE,
    CONSTRAINT pk_evento             PRIMARY KEY (id_evento),
    CONSTRAINT uq_evento_clave       UNIQUE (clave_proyecto),
    CONSTRAINT fk_evento_cliente     FOREIGN KEY (id_cliente)
        REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    CONSTRAINT fk_evento_gerente     FOREIGN KEY (id_gerente)
        REFERENCES usuario (id_usuario) ON DELETE RESTRICT,
    CONSTRAINT fk_evento_salon       FOREIGN KEY (id_salon)
        REFERENCES salon (id_salon) ON DELETE RESTRICT,
    CONSTRAINT fk_evento_paquete     FOREIGN KEY (id_paquete)
        REFERENCES paquete (id_paquete) ON DELETE RESTRICT,
    CONSTRAINT ck_evento_horario     CHECK (hora_fin > hora_inicio),
    CONSTRAINT ck_evento_asistentes  CHECK (num_asistentes > 0),
    CONSTRAINT ck_evento_costo       CHECK (costo_total >= 0),
    CONSTRAINT ck_evento_estado      CHECK (estado IN                        -- RN-11
        ('COTIZACION', 'CONFIRMADO', 'REALIZADO', 'CANCELADO')),
    CONSTRAINT ck_evento_finiquitado CHECK (finiquitado IN ('S', 'N'))
);

-- Índice de la agenda: criterio de búsqueda por salón y fecha (RNF-02)
CREATE INDEX ix_evento_salon_fecha ON evento (id_salon, fecha_evento);
CREATE INDEX ix_evento_cliente     ON evento (id_cliente);

-- ---------------------------------------------------------------------
-- PAGO · abonos de un evento (composición con EVENTO) (HU-009)
-- ---------------------------------------------------------------------
CREATE TABLE pago (
    id_pago    SERIAL         NOT NULL,
    id_evento  INTEGER        NOT NULL,
    monto      NUMERIC(12,2)  NOT NULL,
    tipo       VARCHAR(20)    NOT NULL,
    referencia VARCHAR(60),
    fecha_pago TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_pago        PRIMARY KEY (id_pago),
    CONSTRAINT fk_pago_evento FOREIGN KEY (id_evento)
        REFERENCES evento (id_evento) ON DELETE CASCADE,
    CONSTRAINT ck_pago_monto  CHECK (monto > 0)
);

CREATE INDEX ix_pago_evento ON pago (id_evento);

-- ---------------------------------------------------------------------
-- BITACORA · operaciones sensibles (RF-41, RNF-18)
-- ---------------------------------------------------------------------
CREATE TABLE bitacora (
    id_bitacora SERIAL       NOT NULL,
    id_usuario  INTEGER,
    accion      VARCHAR(40)  NOT NULL,
    entidad     VARCHAR(60)  NOT NULL,
    fecha       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_bitacora         PRIMARY KEY (id_bitacora),
    CONSTRAINT fk_bitacora_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuario (id_usuario) ON DELETE RESTRICT
);

CREATE INDEX ix_bitacora_fecha ON bitacora (fecha);

COMMIT;
