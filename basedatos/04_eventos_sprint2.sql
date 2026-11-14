-- =====================================================================
-- PKG-06 Base de datos · Script 04 · Motor de reservas y tablero
-- Sprint 2 · Parte 1 (HU-005, HU-006)
--
-- IB-07  Clave de proyecto ............ RN-08 · código BF008 · HU-005
-- (fn)   Función de cotización ........ RN-09 · código BF009 · HU-005
-- IB-01  Detalle de evento (vista) .... RF-33 · base de las demás vistas
-- IB-10  Ocupación por salón (vista) .. HU-006 · IU-03
-- IB-11  Pendientes de cierre (vista) . RN-14 · DA-04 · HU-006 · IU-03
--
-- Las validaciones de aforo (IB-02, BF001) y de traslape de horario
-- (IB-03, BF002) corresponden a HU-007 y se agregan en el script 05
-- (Sprint 2 · Parte 2).
--
-- Decisión DA-01: la clave y el costo los asigna la base. Aunque el
-- evento se inserte por SQL directo, la clave sigue el formato y el
-- costo sigue la fórmula oficial.
-- Script re-ejecutable: CREATE OR REPLACE + DROP ... IF EXISTS.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- IB-07 · RN-08 · Clave de proyecto EVT-AAAA-NNNN
-- AAAA es el año en que se registra el evento; NNNN es el consecutivo
-- de ese año. Se ignora cualquier clave que traiga el INSERT.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_asignar_clave_proyecto()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_anio   TEXT := to_char(CURRENT_DATE, 'YYYY');
    v_ultimo INTEGER;
BEGIN
    -- Dos registros simultáneos no pueden tomar el mismo consecutivo:
    -- el candado se libera al terminar la transacción.
    PERFORM pg_advisory_xact_lock(hashtext('clave_proyecto_' || v_anio));

    SELECT COALESCE(MAX(substring(clave_proyecto FROM 10 FOR 4)::INTEGER), 0)
      INTO v_ultimo
      FROM evento
     WHERE clave_proyecto LIKE 'EVT-' || v_anio || '-____';

    IF v_ultimo >= 9999 THEN
        RAISE EXCEPTION 'Se agotaron las claves de proyecto del año %: el máximo es EVT-%-9999.', v_anio, v_anio
            USING ERRCODE = 'BF008';
    END IF;

    NEW.clave_proyecto := 'EVT-' || v_anio || '-' || lpad((v_ultimo + 1)::TEXT, 4, '0');
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_evento_clave ON evento;
CREATE TRIGGER trg_evento_clave
    BEFORE INSERT ON evento
    FOR EACH ROW
    EXECUTE FUNCTION fn_asignar_clave_proyecto();

-- La clave es irrepetible e inmutable: una vez asignada no se edita.
CREATE OR REPLACE FUNCTION fn_clave_proyecto_inmutable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.clave_proyecto IS DISTINCT FROM OLD.clave_proyecto THEN
        RAISE EXCEPTION 'La clave de proyecto % la asigna el sistema y no se puede modificar.', OLD.clave_proyecto
            USING ERRCODE = 'BF008';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_evento_clave_inmutable ON evento;
CREATE TRIGGER trg_evento_clave_inmutable
    BEFORE UPDATE OF clave_proyecto ON evento
    FOR EACH ROW
    EXECUTE FUNCTION fn_clave_proyecto_inmutable();

-- ---------------------------------------------------------------------
-- RN-09 · Función de cotización
-- costo = renta del salón + precio por persona del paquete × asistentes
-- La usa el trigger del evento y puede consultarse sola:
--     SELECT fn_cotizar(1, 2, 150);
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_cotizar(p_id_salon INTEGER,
                                      p_id_paquete INTEGER,
                                      p_asistentes INTEGER)
RETURNS NUMERIC(12,2)
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_renta  NUMERIC(10,2);
    v_precio NUMERIC(10,2) := 0;
BEGIN
    SELECT costo_renta INTO v_renta FROM salon WHERE id_salon = p_id_salon;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se puede cotizar: el salón seleccionado no existe.'
            USING ERRCODE = 'BF009';
    END IF;

    IF p_id_paquete IS NOT NULL THEN
        SELECT precio_persona INTO v_precio FROM paquete WHERE id_paquete = p_id_paquete;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'No se puede cotizar: el paquete seleccionado no existe.'
                USING ERRCODE = 'BF009';
        END IF;
    END IF;

    RETURN v_renta + v_precio * COALESCE(p_asistentes, 0);
END;
$$;

-- El costo se fija al registrar el evento y se recalcula solo cuando
-- cambian el salón, el paquete o los asistentes. Si después cambia la
-- renta del salón o el precio del paquete, los eventos ya cotizados
-- conservan el precio pactado.
CREATE OR REPLACE FUNCTION fn_calcular_costo_evento()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.costo_total := fn_cotizar(NEW.id_salon, NEW.id_paquete, NEW.num_asistentes);
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_evento_costo ON evento;
CREATE TRIGGER trg_evento_costo
    BEFORE INSERT OR UPDATE OF id_salon, id_paquete, num_asistentes ON evento
    FOR EACH ROW
    EXECUTE FUNCTION fn_calcular_costo_evento();

-- ---------------------------------------------------------------------
-- IB-01 · Detalle de evento
-- Reúne evento, cliente, gerente, salón, paquete, total pagado y saldo.
-- El saldo no se almacena: se calcula (RF-33). Base de IB-08 a IB-11.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_evento_detalle AS
SELECT e.id_evento,
       e.clave_proyecto,
       e.nombre_evento,
       e.fecha_evento,
       e.hora_inicio,
       e.hora_fin,
       e.num_asistentes,
       e.costo_total,
       e.estado,
       e.finiquitado,
       e.fecha_finiquito,
       e.id_cliente,
       c.nombre            AS nombre_cliente,
       c.correo            AS correo_cliente,
       c.telefono          AS telefono_cliente,
       e.id_gerente,
       g.nombre            AS nombre_gerente,
       e.id_salon,
       s.nombre            AS nombre_salon,
       s.capacidad_maxima,
       e.id_paquete,
       p.nombre            AS nombre_paquete,
       COALESCE(pa.total_pagado, 0)                 AS total_pagado,
       e.costo_total - COALESCE(pa.total_pagado, 0) AS saldo
  FROM evento e
  JOIN usuario c      ON c.id_usuario = e.id_cliente
  LEFT JOIN usuario g ON g.id_usuario = e.id_gerente
  JOIN salon s        ON s.id_salon   = e.id_salon
  LEFT JOIN paquete p ON p.id_paquete = e.id_paquete
  LEFT JOIN (SELECT id_evento, SUM(monto) AS total_pagado
               FROM pago
              GROUP BY id_evento) pa ON pa.id_evento = e.id_evento;

-- ---------------------------------------------------------------------
-- IB-10 · Ocupación por salón (tablero IU-03)
-- Solo cuenta eventos vigentes (cotización o confirmado) de hoy en
-- adelante. La ocupación es el promedio del porcentaje de aforo que usa
-- cada uno de esos eventos.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_ocupacion_salon AS
SELECT s.id_salon,
       s.nombre,
       s.capacidad_maxima,
       s.disponible,
       COUNT(e.id_evento)::INTEGER                AS eventos_proximos,
       COALESCE(MAX(e.num_asistentes), 0)::INTEGER AS mayor_aforo,
       COALESCE(ROUND(AVG(e.num_asistentes * 100.0 / s.capacidad_maxima)), 0)::INTEGER
                                                   AS ocupacion_promedio
  FROM salon s
  LEFT JOIN evento e
         ON e.id_salon = s.id_salon
        AND e.estado IN ('COTIZACION', 'CONFIRMADO')
        AND e.fecha_evento >= CURRENT_DATE
 GROUP BY s.id_salon, s.nombre, s.capacidad_maxima, s.disponible;

-- ---------------------------------------------------------------------
-- IB-11 · Pendientes de cierre (RN-14, DA-04)
-- Eventos cuya fecha ya pasó y siguen abiertos. El sistema solo los
-- señala: decidir si se realizaron o se cancelaron le toca al gerente.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_pendientes_cierre AS
SELECT d.*
  FROM vw_evento_detalle d
 WHERE d.estado IN ('COTIZACION', 'CONFIRMADO')
   AND d.fecha_evento < CURRENT_DATE;

COMMIT;
