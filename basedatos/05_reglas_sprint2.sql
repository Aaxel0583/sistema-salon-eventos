-- =====================================================================
-- PKG-06 Base de datos · Script 05 · Control de aforo y disponibilidad
-- Sprint 2 · Parte 2 (HU-007)
--
-- IB-02  Validación de capacidad ....... RN-01 · código BF001 · RF-25
-- IB-03  Validación de disponibilidad .. RN-02 · código BF002 · RF-26, RF-27
--
-- Decisión DA-01 · RNF-09: las dos reglas viven en la base. Se cumplen
-- aunque el evento se inserte o se edite por SQL directo, sin pasar por
-- la aplicación. La aplicación no las repite: envía la operación y
-- traduce el código BFnnn (Escenario 5, Figura 8).
-- Los mensajes ya incluyen los valores involucrados (RNF-12).
-- Script re-ejecutable: CREATE OR REPLACE + DROP TRIGGER IF EXISTS.
--
-- Orden de evaluación (Figura 19): primero el aforo, después la agenda.
-- PostgreSQL dispara los triggers BEFORE por orden alfabético de nombre:
-- trg_evento_aforo < trg_evento_clave < trg_evento_costo
-- < trg_evento_disponibilidad.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- IB-02 · RN-01 · Los asistentes no exceden la capacidad del salón
--
-- Se evalúa al registrar el evento y al cambiar su salón o su número de
-- asistentes. Un cambio de estatus NO la vuelve a evaluar: si el salón
-- redujo su capacidad después (RN-04 lo permite cuando el evento ya
-- pasó), cerrar ese evento como realizado no debe fallar.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_validar_aforo()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_nombre    salon.nombre%TYPE;
    v_capacidad salon.capacidad_maxima%TYPE;
BEGIN
    IF TG_OP = 'UPDATE'
       AND NEW.id_salon = OLD.id_salon
       AND NEW.num_asistentes = OLD.num_asistentes THEN
        RETURN NEW;
    END IF;

    -- Mismo candado que toma IB-05 (reducción de capacidad): una reserva y
    -- un cambio de aforo simultáneos sobre el mismo salón se atienden uno
    -- después del otro, y el segundo ya ve lo que guardó el primero.
    PERFORM pg_advisory_xact_lock(hashtext('agenda_salon'), NEW.id_salon);

    SELECT s.nombre, s.capacidad_maxima
      INTO v_nombre, v_capacidad
      FROM salon s
     WHERE s.id_salon = NEW.id_salon;

    IF NOT FOUND THEN
        RETURN NEW;                     -- lo reporta la llave foránea fk_evento_salon
    END IF;

    IF NEW.num_asistentes > v_capacidad THEN
        RAISE EXCEPTION '"%" admite % personas y el evento es para %. Reduce los invitados o elige otro salón.',
            v_nombre, v_capacidad, NEW.num_asistentes
            USING ERRCODE = 'BF001';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_evento_aforo ON evento;
CREATE TRIGGER trg_evento_aforo
    BEFORE INSERT OR UPDATE OF id_salon, num_asistentes ON evento
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_aforo();

-- ---------------------------------------------------------------------
-- IB-03 · RN-02 · Un salón no alberga dos eventos con horarios traslapados
--
-- Aparta el salón el evento que ya dio anticipo: CONFIRMADO, y después
-- REALIZADO (D-20, regla precisada con el cliente). Una COTIZACION solo
-- es una solicitud de información: no aparta el horario y puede haber
-- varias para el mismo salón y horario; lo gana la primera que se
-- confirma. Un evento CANCELADO no ocupa el salón.
--
-- Contra los eventos que apartan el salón se valida:
--   · el registro de una cotización (no tiene caso cotizar un horario ya
--     apartado: nunca podría confirmarse);
--   · el cambio de salón, fecha u horario;
--   · el paso de cotización a confirmado o realizado, y la reactivación
--     de uno cancelado.
-- Dos horarios se traslapan cuando uno empieza antes de que el otro
-- termine; los contiguos (uno termina a las 13:00 y el otro empieza a
-- las 13:00) no se traslapan (RF-27). El trigger consulta la tabla
-- EVENTO directamente, sin depender de la sentencia en curso.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_validar_disponibilidad()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_nombre  salon.nombre%TYPE;
    v_clave   evento.clave_proyecto%TYPE;
    v_inicio  evento.hora_inicio%TYPE;
    v_fin     evento.hora_fin%TYPE;
BEGIN
    IF NEW.estado = 'CANCELADO' THEN
        RETURN NEW;                     -- un evento cancelado no ocupa el salón
    END IF;

    IF TG_OP = 'UPDATE'
       AND NEW.id_salon     = OLD.id_salon
       AND NEW.fecha_evento = OLD.fecha_evento
       AND NEW.hora_inicio  = OLD.hora_inicio
       AND NEW.hora_fin     = OLD.hora_fin
       AND (OLD.estado IN ('CONFIRMADO', 'REALIZADO')   -- ya tenía apartado su horario
            OR NEW.estado = OLD.estado) THEN             -- o nada de su agenda cambió
        RETURN NEW;
    END IF;

    -- Dos reservas simultáneas del mismo salón no pueden revisar la agenda
    -- al mismo tiempo: la segunda espera y ve el evento de la primera.
    PERFORM pg_advisory_xact_lock(hashtext('agenda_salon'), NEW.id_salon);

    SELECT e.clave_proyecto, e.hora_inicio, e.hora_fin
      INTO v_clave, v_inicio, v_fin
      FROM evento e
     WHERE e.id_salon     = NEW.id_salon
       AND e.fecha_evento = NEW.fecha_evento
       AND e.estado      IN ('CONFIRMADO', 'REALIZADO')   -- solo el anticipo aparta (D-20)
       AND e.id_evento IS DISTINCT FROM NEW.id_evento
       AND e.hora_inicio  < NEW.hora_fin
       AND NEW.hora_inicio < e.hora_fin
     ORDER BY e.hora_inicio, e.id_evento
     LIMIT 1;

    IF FOUND THEN
        SELECT s.nombre INTO v_nombre FROM salon s WHERE s.id_salon = NEW.id_salon;
        IF TG_OP = 'UPDATE' AND OLD.estado = 'COTIZACION' AND NEW.estado <> 'COTIZACION'
           AND NEW.fecha_evento = OLD.fecha_evento AND NEW.id_salon = OLD.id_salon
           AND NEW.hora_inicio = OLD.hora_inicio AND NEW.hora_fin = OLD.hora_fin THEN
            -- La cotización llegó tarde: otro evento ya dio anticipo por ese horario.
            RAISE EXCEPTION 'No se puede % %: "%" ya está apartado el % de % a % por el evento %, que ya dio anticipo. Cambia el horario, la fecha o el salón de esta cotización, o cancélala.',
                CASE NEW.estado WHEN 'REALIZADO' THEN 'marcar como realizado' ELSE 'confirmar' END,
                NEW.clave_proyecto, v_nombre, to_char(NEW.fecha_evento, 'DD/MM/YYYY'),
                to_char(v_inicio, 'HH24:MI'), to_char(v_fin, 'HH24:MI'), v_clave
                USING ERRCODE = 'BF002';
        END IF;
        RAISE EXCEPTION '"%" ya está ocupado el % de % a % por el evento %. Elige otro horario, otra fecha u otro salón.',
            v_nombre, to_char(NEW.fecha_evento, 'DD/MM/YYYY'),
            to_char(v_inicio, 'HH24:MI'), to_char(v_fin, 'HH24:MI'), v_clave
            USING ERRCODE = 'BF002';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_evento_disponibilidad ON evento;
CREATE TRIGGER trg_evento_disponibilidad
    BEFORE INSERT OR UPDATE OF id_salon, fecha_evento, hora_inicio, hora_fin, estado ON evento
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_disponibilidad();

-- ---------------------------------------------------------------------
-- Revisión de los datos que ya existían
-- Los triggers solo vigilan lo que se guarde de ahora en adelante. Si la
-- base tiene eventos capturados antes de instalar este script (Parte 1
-- del Sprint 2), aquí se avisa cuántos violan cada regla para que el
-- gerente los corrija. No se modifica ningún dato.
-- ---------------------------------------------------------------------
DO $$
DECLARE
    v_sobrecupo INTEGER;
    v_traslapes INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_sobrecupo
      FROM evento e
      JOIN salon s ON s.id_salon = e.id_salon
     WHERE e.estado IN ('COTIZACION', 'CONFIRMADO')
       AND e.fecha_evento >= CURRENT_DATE
       AND e.num_asistentes > s.capacidad_maxima;

    SELECT COUNT(*) INTO v_traslapes
      FROM evento a
      JOIN evento b
        ON b.id_salon     = a.id_salon
       AND b.fecha_evento = a.fecha_evento
       AND b.id_evento    > a.id_evento
       AND b.hora_inicio  < a.hora_fin
       AND a.hora_inicio  < b.hora_fin
     WHERE a.estado IN ('CONFIRMADO', 'REALIZADO')       -- solo el anticipo aparta (D-20)
       AND b.estado IN ('CONFIRMADO', 'REALIZADO')
       AND a.fecha_evento >= CURRENT_DATE;

    IF v_sobrecupo > 0 THEN
        RAISE WARNING 'Hay % evento(s) vigente(s) con más asistentes que la capacidad de su salón (RN-01). Revísalos en Eventos.', v_sobrecupo;
    END IF;
    IF v_traslapes > 0 THEN
        RAISE WARNING 'Hay % par(es) de eventos confirmados próximos que se enciman en el mismo salón (RN-02). Revísalos en Eventos.', v_traslapes;
    END IF;
END;
$$;

COMMIT;
