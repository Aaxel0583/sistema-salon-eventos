-- =====================================================================
-- PKG-06 Base de datos · Script 06 · Control financiero y reportes
-- Sprint 3 (HU-009 a HU-012)
--
-- IB-06  Registro de pago .............. RN-05 · código BF005 · RF-31, RF-32
--        Finiquito automático .......... RN-10 · código BF010 · RF-34
-- IB-08  Cartera con semáforo (vista) .. RN-13 · RF-37 · HU-010
-- IB-09  Proyectos activos (vista) ..... RF-35 · HU-011
--        Proyectos realizados (vista) .. RF-36 · HU-012
--
-- Decisión DA-01 · RNF-09: las reglas del dinero viven en la base. Se
-- cumplen aunque el abono se inserte por SQL directo, sin pasar por la
-- aplicación ni por fn_registrar_pago. La aplicación no las repite:
-- envía la operación y traduce el código BFnnn (Escenario 6, Figura 9).
-- Los mensajes ya incluyen los valores involucrados (RNF-12).
--
-- PostgreSQL exige que un código de error tenga cinco caracteres: el
-- BF0010 del SRS se emite como BF010 y la capa C-10 lo presenta con su
-- nombre del SRS (ver docs/desviaciones_sprint3.md, D-30).
-- Script re-ejecutable: CREATE OR REPLACE + DROP TRIGGER IF EXISTS.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- IB-06 · RN-05 · Un pago no excede el saldo pendiente del evento
--
-- El saldo se consulta ANTES de insertar: un abono mayor al pendiente se
-- rechaza sin dejar rastro (Escenario 6). La fila del evento se toma con
-- FOR UPDATE, de modo que dos abonos simultáneos al mismo evento se
-- atienden uno después del otro y el segundo ya ve lo que guardó el
-- primero: no pueden sumar, entre los dos, más que el saldo.
--
-- Un evento cancelado no tiene nada por cobrar: no admite abonos.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_validar_pago()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_clave  evento.clave_proyecto%TYPE;
    v_estado evento.estado%TYPE;
    v_costo  evento.costo_total%TYPE;
    v_pagado NUMERIC(12,2);
    v_saldo  NUMERIC(12,2);
BEGIN
    SELECT e.clave_proyecto, e.estado, e.costo_total
      INTO v_clave, v_estado, v_costo
      FROM evento e
     WHERE e.id_evento = NEW.id_evento
       FOR UPDATE;

    IF NOT FOUND THEN
        RETURN NEW;                     -- lo reporta la llave foránea fk_pago_evento
    END IF;

    IF v_estado = 'CANCELADO' THEN
        RAISE EXCEPTION 'El evento % está cancelado y no admite abonos.', v_clave
            USING ERRCODE = 'BF005';
    END IF;

    SELECT COALESCE(SUM(p.monto), 0) INTO v_pagado FROM pago p WHERE p.id_evento = NEW.id_evento;
    v_saldo := v_costo - v_pagado;

    IF v_saldo <= 0 THEN
        RAISE EXCEPTION 'El evento % ya está liquidado: no tiene saldo pendiente.', v_clave
            USING ERRCODE = 'BF005';
    END IF;

    IF NEW.monto > v_saldo THEN
        RAISE EXCEPTION 'El abono de $% excede el saldo pendiente de $% del evento %. Captura $% o menos.',
            trim(to_char(NEW.monto, 'FM999,999,999,990.00')), trim(to_char(v_saldo, 'FM999,999,999,990.00')),
            v_clave, trim(to_char(v_saldo, 'FM999,999,999,990.00'))
            USING ERRCODE = 'BF005';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_pago_saldo ON pago;
CREATE TRIGGER trg_pago_saldo
    BEFORE INSERT ON pago
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_pago();

-- ---------------------------------------------------------------------
-- IB-06 · RN-10 · Finiquito automático
--
-- Cuando la suma de los pagos iguala el costo total, el evento queda
-- finiquitado con la fecha del día. Ocurre en la misma operación que el
-- abono (misma transacción): no puede quedar a medias.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_aplicar_finiquito()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE evento e
       SET finiquitado = 'S',
           fecha_finiquito = CURRENT_DATE
     WHERE e.id_evento = NEW.id_evento
       AND e.finiquitado = 'N'
       AND e.costo_total = (SELECT COALESCE(SUM(p.monto), 0) FROM pago p WHERE p.id_evento = e.id_evento);
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS trg_pago_finiquito ON pago;
CREATE TRIGGER trg_pago_finiquito
    AFTER INSERT ON pago
    FOR EACH ROW
    EXECUTE FUNCTION fn_aplicar_finiquito();

-- ---------------------------------------------------------------------
-- Un abono registrado no se modifica ni se elimina
--
-- Editar el monto de un abono sería otra forma de rebasar el saldo
-- (RN-05) o de deshacer un finiquito (SDD §5.3: «no existe transición de
-- regreso»). Mismo criterio que la bitácora (RNF-18). Como PAGO depende
-- de EVENTO con borrado en cascada, tampoco puede eliminarse un evento
-- que ya tiene abonos.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_pago_inalterable()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Un abono registrado no se puede modificar ni eliminar: forma parte del estado de cuenta del evento.'
        USING ERRCODE = 'BF005';
END;
$$;

DROP TRIGGER IF EXISTS trg_pago_inalterable ON pago;
CREATE TRIGGER trg_pago_inalterable
    BEFORE UPDATE OR DELETE ON pago
    FOR EACH ROW
    EXECUTE FUNCTION fn_pago_inalterable();

-- ---------------------------------------------------------------------
-- RN-10 · La marca de finiquito la asigna el sistema, no el usuario
--
-- Un evento nace sin finiquitar. La marca solo puede levantarse cuando el
-- saldo es exactamente cero (lo hace trg_pago_finiquito) y, una vez
-- puesta, no se retira ni se le cambia la fecha.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_proteger_finiquito()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_pagado NUMERIC(12,2);
BEGIN
    IF TG_OP = 'INSERT' THEN
        NEW.finiquitado := 'N';
        NEW.fecha_finiquito := NULL;
        RETURN NEW;
    END IF;

    IF NEW.finiquitado = OLD.finiquitado
       AND NEW.fecha_finiquito IS NOT DISTINCT FROM OLD.fecha_finiquito THEN
        RETURN NEW;
    END IF;

    IF OLD.finiquitado = 'S' THEN
        RAISE EXCEPTION 'El evento % quedó finiquitado el %: la marca no se puede retirar ni modificar.',
            OLD.clave_proyecto, to_char(OLD.fecha_finiquito, 'DD/MM/YYYY')
            USING ERRCODE = 'BF010';
    END IF;

    IF NEW.finiquitado = 'S' THEN
        SELECT COALESCE(SUM(p.monto), 0) INTO v_pagado FROM pago p WHERE p.id_evento = NEW.id_evento;
        IF v_pagado <> NEW.costo_total THEN
            RAISE EXCEPTION 'El evento % no se puede marcar como finiquitado: aún debe $%. El finiquito lo asigna el sistema cuando el saldo llega a cero.',
                NEW.clave_proyecto, trim(to_char(NEW.costo_total - v_pagado, 'FM999,999,999,990.00'))
                USING ERRCODE = 'BF010';
        END IF;
        NEW.fecha_finiquito := COALESCE(NEW.fecha_finiquito, CURRENT_DATE);
    ELSE
        NEW.fecha_finiquito := NULL;    -- sin finiquito no hay fecha de finiquito
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_evento_finiquito ON evento;
CREATE TRIGGER trg_evento_finiquito
    BEFORE INSERT OR UPDATE OF finiquitado, fecha_finiquito ON evento
    FOR EACH ROW
    EXECUTE FUNCTION fn_proteger_finiquito();

-- ---------------------------------------------------------------------
-- El costo de un evento no baja de lo que ya se cobró
--
-- La aplicación no edita salón, paquete ni asistentes de un evento ya
-- registrado; esta regla cubre el cambio por SQL directo. Se llama
-- trg_evento_costo_pagado para dispararse después de trg_evento_costo,
-- que es el que recalcula el costo (PostgreSQL sigue el orden alfabético).
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_validar_costo_contra_pagos()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_pagado NUMERIC(12,2);
BEGIN
    IF NEW.costo_total = OLD.costo_total THEN
        RETURN NEW;
    END IF;

    IF OLD.finiquitado = 'S' THEN
        RAISE EXCEPTION 'El evento % ya está finiquitado: su costo de $% no se puede cambiar.',
            OLD.clave_proyecto, trim(to_char(OLD.costo_total, 'FM999,999,999,990.00'))
            USING ERRCODE = 'BF010';
    END IF;

    SELECT COALESCE(SUM(p.monto), 0) INTO v_pagado FROM pago p WHERE p.id_evento = NEW.id_evento;
    IF NEW.costo_total < v_pagado THEN
        RAISE EXCEPTION 'El evento % ya tiene $% pagados: su costo no puede quedar en $%.',
            OLD.clave_proyecto, trim(to_char(v_pagado, 'FM999,999,999,990.00')),
            trim(to_char(NEW.costo_total, 'FM999,999,999,990.00'))
            USING ERRCODE = 'BF005';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_evento_costo_pagado ON evento;
CREATE TRIGGER trg_evento_costo_pagado
    BEFORE UPDATE OF id_salon, id_paquete, num_asistentes, costo_total ON evento
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_costo_contra_pagos();

-- ---------------------------------------------------------------------
-- IB-06 · Punto de entrada del registro de pago
-- Lo invoca la aplicación (C-05). Valida que el evento exista, registra
-- el abono y devuelve su identificador; el control de saldo y el
-- finiquito los aplican los triggers de arriba en la misma invocación.
--     SELECT fn_registrar_pago(12, 5000.00, 'TRANSFERENCIA', 'SPEI 4471');
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_registrar_pago(p_id_evento  INTEGER,
                                             p_monto      NUMERIC,
                                             p_tipo       VARCHAR,
                                             p_referencia VARCHAR DEFAULT NULL)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_pago INTEGER;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM evento WHERE id_evento = p_id_evento) THEN
        RAISE EXCEPTION 'No se puede registrar el abono: el evento no existe.'
            USING ERRCODE = 'BF005';
    END IF;
    IF p_monto IS NULL OR p_monto <= 0 THEN
        RAISE EXCEPTION 'El monto del abono debe ser mayor a cero.'
            USING ERRCODE = 'BF005';
    END IF;

    INSERT INTO pago (id_evento, monto, tipo, referencia)
    VALUES (p_id_evento, round(p_monto, 2), upper(trim(p_tipo)), NULLIF(trim(p_referencia), ''))
    RETURNING id_pago INTO v_id_pago;

    RETURN v_id_pago;
END;
$$;

-- ---------------------------------------------------------------------
-- IB-08 · RN-13 · Cartera con semáforo (HU-010)
--
-- Una cuenta por cobrar es el saldo de un evento CONFIRMADO o REALIZADO
-- (mismo criterio que el indicador «por cobrar» del tablero, D-14): una
-- cotización todavía no es un compromiso y un cancelado ya no lo es.
--   VENCIDA  la fecha del evento ya transcurrió
--   PROXIMA  el evento es hoy o dentro de los 21 días siguientes
--   VIGENTE  faltan más de 21 días
-- El semáforo se calcula aquí para que el reporte, su descarga y el
-- tablero muestren siempre lo mismo (SDD IU-08).
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_cartera AS
SELECT d.*,
       (d.fecha_evento - CURRENT_DATE)::INTEGER AS dias_para_evento,
       CASE WHEN d.fecha_evento <  CURRENT_DATE      THEN 'VENCIDA'
            WHEN d.fecha_evento <= CURRENT_DATE + 21 THEN 'PROXIMA'
            ELSE 'VIGENTE'
       END                                      AS semaforo
  FROM vw_evento_detalle d
 WHERE d.estado IN ('CONFIRMADO', 'REALIZADO')
   AND d.saldo > 0;

-- ---------------------------------------------------------------------
-- IB-09 · Proyectos activos (HU-011, RF-35)
-- Eventos en cotización o confirmados: la carga de trabajo comprometida.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_proyectos_activos AS
SELECT d.*,
       ROUND(d.num_asistentes * 100.0 / d.capacidad_maxima)::INTEGER AS porcentaje_aforo
  FROM vw_evento_detalle d
 WHERE d.estado IN ('COTIZACION', 'CONFIRMADO');

-- ---------------------------------------------------------------------
-- IB-09 · Proyectos realizados (HU-012, RF-36)
-- Histórico de eventos que el gerente marcó como realizados (RN-14).
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_proyectos_realizados AS
SELECT d.*
  FROM vw_evento_detalle d
 WHERE d.estado = 'REALIZADO';

-- ---------------------------------------------------------------------
-- Revisión de los datos que ya existían
-- Los triggers solo vigilan lo que se guarde de ahora en adelante. Si la
-- base ya tenía abonos (capturados a mano antes de este script):
--   · los eventos cuyo saldo ya es cero reciben su finiquito, con la
--     fecha de su último abono;
--   · se avisa de los eventos con más pagos que costo. No se modifican.
-- ---------------------------------------------------------------------
DO $$
DECLARE
    v_finiquitados INTEGER;
    v_excedidos    INTEGER;
BEGIN
    UPDATE evento e
       SET finiquitado = 'S',
           fecha_finiquito = t.ultimo_pago
      FROM (SELECT p.id_evento, SUM(p.monto) AS pagado, MAX(p.fecha_pago)::DATE AS ultimo_pago
              FROM pago p
             GROUP BY p.id_evento) t
     WHERE t.id_evento = e.id_evento
       AND e.finiquitado = 'N'
       AND e.costo_total = t.pagado;
    GET DIAGNOSTICS v_finiquitados = ROW_COUNT;

    SELECT COUNT(*) INTO v_excedidos
      FROM evento e
      JOIN (SELECT id_evento, SUM(monto) AS pagado FROM pago GROUP BY id_evento) t
        ON t.id_evento = e.id_evento
     WHERE t.pagado > e.costo_total;

    IF v_finiquitados > 0 THEN
        RAISE WARNING 'Se marcaron como finiquitados % evento(s) que ya tenían su costo cubierto (RN-10).', v_finiquitados;
    END IF;
    IF v_excedidos > 0 THEN
        RAISE WARNING 'Hay % evento(s) con más pagos que su costo total (RN-05). Revísalos en Eventos.', v_excedidos;
    END IF;
END;
$$;

COMMIT;
