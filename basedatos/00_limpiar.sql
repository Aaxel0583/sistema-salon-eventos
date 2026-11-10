-- =====================================================================
-- PKG-06 · Script 00 · Limpieza del esquema (SOLO DESARROLLO)
-- Borra todas las tablas y funciones del sistema para reinstalar desde
-- cero. NUNCA ejecutar sobre la base del cliente.
-- =====================================================================
BEGIN;
DROP TABLE IF EXISTS bitacora, pago, evento, paquete_platillo, paquete,
                     platillo, salon, usuario CASCADE;
DROP FUNCTION IF EXISTS fn_validar_limite_salones() CASCADE;
DROP FUNCTION IF EXISTS fn_validar_reduccion_capacidad() CASCADE;
DROP FUNCTION IF EXISTS fn_bitacora_inalterable() CASCADE;
COMMIT;
