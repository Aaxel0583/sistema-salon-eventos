-- =====================================================================
-- PKG-06 Base de datos · Script 02 · Reglas de negocio del Sprint 1
--
-- IB-04  Límite de salones ............ RN-03 · código BF003 · HU-003
-- IB-05  Reducción de capacidad ....... RN-04 · código BF004 · HU-003
-- (sin ID) Bitácora inalterable ....... RNF-18
--
-- Decisión DA-01: las reglas viven en la base y se cumplen aunque el dato
-- llegue por SQL directo. La aplicación solo traduce el código BFnnn.
-- Los mensajes ya incluyen los valores involucrados (RNF-12).
-- Script re-ejecutable: CREATE OR REPLACE + DROP TRIGGER IF EXISTS.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- IB-04 · RN-03 · La operación queda fijada en tres salones
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_validar_limite_salones()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_total INTEGER;
BEGIN
    -- Serializa las altas concurrentes: sin este candado, dos inserciones
    -- simultáneas podrían ver 2 salones cada una y dejar 4.
    PERFORM pg_advisory_xact_lock(hashtext('salon_limite'));

    SELECT COUNT(*) INTO v_total FROM salon;

    IF v_total >= 3 THEN
        RAISE EXCEPTION 'El sistema opera con tres salones y ya están registrados los tres. No se puede agregar "%".', NEW.nombre
            USING ERRCODE = 'BF003';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_salon_limite ON salon;
CREATE TRIGGER trg_salon_limite
    BEFORE INSERT ON salon
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_limite_salones();

-- ---------------------------------------------------------------------
-- IB-05 · RN-04 · La capacidad no baja del mayor aforo agendado
-- "Agendado" = evento vigente (COTIZACION o CONFIRMADO) de hoy en adelante.
-- Un evento cancelado no ocupa el salón (RN-02) y uno pasado ya no se
-- ve afectado por un cambio de capacidad.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_validar_reduccion_capacidad()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_mayor_aforo INTEGER;
BEGIN
    IF NEW.capacidad_maxima < OLD.capacidad_maxima THEN
        SELECT MAX(e.num_asistentes)
          INTO v_mayor_aforo
          FROM evento e
         WHERE e.id_salon = NEW.id_salon
           AND e.estado IN ('COTIZACION', 'CONFIRMADO')
           AND e.fecha_evento >= CURRENT_DATE;

        IF v_mayor_aforo IS NOT NULL AND NEW.capacidad_maxima < v_mayor_aforo THEN
            RAISE EXCEPTION 'No se puede reducir la capacidad de "%" a % personas: ya hay un evento agendado con % asistentes.',
                OLD.nombre, NEW.capacidad_maxima, v_mayor_aforo
                USING ERRCODE = 'BF004';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_salon_capacidad ON salon;
CREATE TRIGGER trg_salon_capacidad
    BEFORE UPDATE OF capacidad_maxima ON salon
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_reduccion_capacidad();

-- ---------------------------------------------------------------------
-- RNF-18 · La bitácora no admite modificación ni borrado
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_bitacora_inalterable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'La bitácora es evidencia de auditoría: sus registros no se pueden modificar ni eliminar.';
END;
$$;

DROP TRIGGER IF EXISTS trg_bitacora_inalterable ON bitacora;
CREATE TRIGGER trg_bitacora_inalterable
    BEFORE UPDATE OR DELETE ON bitacora
    FOR EACH ROW
    EXECUTE FUNCTION fn_bitacora_inalterable();

COMMIT;
