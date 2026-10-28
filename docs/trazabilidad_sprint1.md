# Registro de trazabilidad · Sprint 1

Complementa el entregable *Traceability Record* (ISO/IEC 29110, SI) con el código: HU → RF/RN → elemento de diseño → archivo → prueba.

| HU | Requisito | Diseño | Implementación | Prueba |
|---|---|---|---|---|
| HU-001 | RF-01 un campo para correo o celular | C-01 · IU-01 | `servicios/validaciones.py::interpretar_identificador` · `acceso/login.html` | `test_unitarias::test_un_solo_campo_acepta_correo_o_celular` · CP-01 |
| HU-001 | RF-02 validación contra hash · RNF-04 | C-01 | `seguridad/claves.py` (scrypt con sal) | `test_unitarias::test_cifrado_con_sal` |
| HU-001 | RF-03 bloqueo al quinto intento | C-01 · USUARIO.intentos_fallidos | `servicio_acceso.py::autenticar` · `repositorio_usuarios.py::registrar_fallo` | `test_flujos::test_cp02_bloqueo_al_quinto_intento` (CP-02) |
| HU-001 | RF-04 cambio obligatorio de clave inicial | C-01 · IU-02 | `app/__init__.py::cargar_usuario` · `rutas/acceso.py::cambiar_clave` | `test_flujos::test_cp21_...` (CP-21) |
| HU-001 | RF-05 acceso por rol · RNF-06 | Decorador de control por rol | `seguridad/decoradores.py` | `test_flujos::test_rf05_...` · CP-01 |
| HU-001 | RF-06 cierre de sesión | C-01 | `rutas/acceso.py::logout` · `seguridad/sesion.py` | `test_flujos::test_cp22_...` (CP-22) |
| HU-001 | RF-41 bitácora · RNF-18 | BITACORA | `repositorio_bitacora.py` · `trg_bitacora_inalterable` | `test_reglas_bd::test_rnf18_...` |
| HU-002 | RF-07 alta con nombre y un contacto · RN-06 | C-02 · IU-04 · `ck_usuario_contacto` | `servicio_clientes.py::registrar_en` | `test_flujos::test_cp03_...` · `test_reglas_bd::test_rn06_...` |
| HU-002 | RF-08 clave legible mostrada una vez · RNF-14 | Generador sin caracteres ambiguos | `seguridad/claves.py::generar_clave_legible` · `clientes/directorio.html` | `test_unitarias::test_clave_legible_...` · CP-03 |
| HU-002 | RF-09 unicidad del contacto · RN-07 | `uq_usuario_correo`, `uq_usuario_telefono` | `datos/errores.py::traducir_error` | `test_flujos::test_cp03_...` · `test_reglas_bd::test_rn07_...` |
| HU-002 | RF-10 regenerar clave y reactivar | C-02 · C-09 | `servicio_clientes.py::regenerar_clave` · `administracion/admin.py` | `test_flujos::test_cp22_...` (CP-22) |
| HU-002 | RF-11 búsqueda en el directorio | C-02 · IU-04 | `repositorio_usuarios.py::buscar_clientes` | `test_flujos::test_cp22_...` |
| HU-002 | RF-12 alta conjunta (preparación) · DA-05 | C-02 participa en transacción de C-04 | `servicio_clientes.py::registrar_en(cur, ...)` | CP-19 (Sprint 2) |
| HU-003 | RF-13, RF-14 consultar y editar salones | C-03 · IU-05 | `servicio_catalogos.py::ServicioSalones` · `catalogos/salones.html` | `test_flujos::test_cp25_catalogos` (CP-25) |
| HU-003 | RF-15 sin cuarto salón · RN-03 | IB-04 · BF003 | `02_reglas_sprint1.sql::fn_validar_limite_salones` | `test_reglas_bd::test_cp04_...` (CP-04) |
| HU-003 | RF-16 capacidad ≥ mayor aforo · RN-04 | IB-05 · BF004 | `02_reglas_sprint1.sql::fn_validar_reduccion_capacidad` | `test_reglas_bd::test_cp05_...` (CP-05) |
| HU-004 | RF-17 platillos por categoría | C-03 · PLATILLO.categoria | `dominio/modelos.py::agrupar_por_categoria` | `test_unitarias::test_agrupacion_...` · CP-25 |
| HU-004 | RF-18 paquetes con platillos y precio | PAQUETE_PLATILLO · Escenario 4 | `servicio_catalogos.py::ServicioPaquetes.guardar` (una transacción) | `test_flujos::test_cp25_catalogos` |
| HU-004 | RF-19 personalizado con cliente · RN-12 | `ck_paquete_dueno` | `servicio_catalogos.py::_validar` + restricción en BD | `test_reglas_bd::test_cp06_...` · CP-25 (CP-06) |

Requisitos no funcionales atendidos en este sprint: RNF-04, RNF-05 (todas las consultas con `%s`), RNF-06, RNF-07, RNF-08, RNF-09 (para BF003 y BF004), RNF-11 (pool con verificación de conexión), RNF-12, RNF-13, RNF-14, RNF-17, RNF-18.
