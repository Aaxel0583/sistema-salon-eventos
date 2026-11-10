-- =====================================================================
-- PKG-06 · Script 00 · Limpieza del esquema (SOLO DESARROLLO)
-- Borra todas las tablas y funciones del sistema para reinstalar desde
-- cero. NUNCA ejecutar sobre la base del cliente.
-- =====================================================================
BEGIN;
DROP VIEW IF EXISTS vw_pendientes_cierre, vw_ocupacion_salon, vw_evento_detalle CASCADE;
DROP TABLE IF EXISTS bitacora, pago, evento, paquete_platillo, paquete,
                     platillo, salon, usuario CASCADE;
DROP FUNCTION IF EXISTS fn_validar_limite_salones() CASCADE;
DROP FUNCTION IF EXISTS fn_validar_reduccion_capacidad() CASCADE;
DROP FUNCTION IF EXISTS fn_bitacora_inalterable() CASCADE;
DROP FUNCTION IF EXISTS fn_asignar_clave_proyecto() CASCADE;
DROP FUNCTION IF EXISTS fn_clave_proyecto_inmutable() CASCADE;
DROP FUNCTION IF EXISTS fn_calcular_costo_evento() CASCADE;
DROP FUNCTION IF EXISTS fn_cotizar(INTEGER, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS fn_validar_aforo() CASCADE;
DROP FUNCTION IF EXISTS fn_validar_disponibilidad() CASCADE;
COMMIT;
