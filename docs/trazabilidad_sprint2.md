# Registro de trazabilidad · Sprint 2 · Parte 1

Complementa el entregable *Traceability Record* (ISO/IEC 29110, SI) con el código: HU → RF/RN → elemento de diseño → archivo → prueba. Cubre HU-005 y HU-006; HU-007 y HU-008 se agregan en la Parte 2.

| HU | Requisito | Diseño | Implementación | Prueba |
|---|---|---|---|---|
| HU-005 | RF-20 registrar evento con cliente, salón, paquete, fecha, horario y asistentes | C-04 · IU-06 · tabla EVENTO | `servicios/servicio_eventos.py::ServicioReservaciones.registrar` · `eventos/nuevo.html` | `test_eventos::test_cp07_...` (CP-07) |
| HU-005 | Estado inicial Cotización (criterio de aceptación) · RN-11 | EVENTO.estado DEFAULT | `01_esquema.sql` · `repositorio_eventos.py::insertar` | `test_eventos::test_cp07_...` |
| HU-005 | RF-21 costo = renta + precio × asistentes · RN-09 | Función de cotización | `04_eventos_sprint2.sql::fn_cotizar`, `trg_evento_costo` | `test_eventos::test_cp07_...` · `test_rn09_...` |
| HU-005 | RF-22 clave EVT-AAAA-NNNN única · RN-08 | IB-07 · BF008 | `04_eventos_sprint2.sql::fn_asignar_clave_proyecto`, `fn_clave_proyecto_inmutable` | `test_eventos::test_cp08_...` (CP-08) |
| HU-005 | Cotización sin recargar la pantalla · RNF-01 | IU-06 panel de cotización | `static/js/app.js` (bloque IU-06) · atributos `data-renta`, `data-precio`, `data-capacidad` | `test_eventos::test_formulario_trae_datos_...` · revisión visual |
| HU-005 | RF-23 lugares disponibles y aviso de aforo excedido | IU-06 · Figura 32 | `static/js/app.js` · `eventos/nuevo.html` (`data-aviso-aforo`) | Revisión visual (150 invitados en salón de 90 → −60, botón deshabilitado) · CP-10 completo en Parte 2 |
| HU-005 | Hora de término posterior a la de inicio | `ck_evento_horario` | `servicio_eventos.py::_validar_captura` · `datos/errores.py` | `test_unitarias_eventos::test_termino_posterior_...` · `test_eventos::test_rechazos_...` |
| HU-005 | RF-12 alta del cliente en la misma pantalla · DA-05 · RNF-08 | C-04 + C-02 en una transacción · Escenario 2 | `servicio_eventos.py::registrar` → `servicio_clientes.py::registrar_en(cur, …)` · `eventos/registrado.html` | `test_eventos::test_rf12_...` · `test_da05_...` (CP-19 parcial; completo con BF001 en Parte 2) |
| HU-005 | RF-08 clave del cliente mostrada una vez | IU-06 respuesta del POST | `rutas/eventos.py::registrar` (sin guardar la clave en sesión) | `test_eventos::test_rf12_...` |
| HU-005 | RN-12 paquete personalizado solo para su dueño | C-04 | `servicio_eventos.py::_validar_catalogos` · filtro de opciones en `app.js` | `test_eventos::test_da05_...` |
| HU-006 | RF-28 listado con filtros por estatus, salón y texto | C-08 · listado de eventos | `repositorio_eventos.py::listar` · `eventos/listado.html` | `test_eventos::test_cp09_...` (CP-09) |
| HU-006 | RF-29 gerente responsable | EVENTO.id_gerente | `servicio_eventos.py::asignar_gerente` · `eventos/ficha.html` | `test_eventos::test_cp24_...` (CP-24) |
| HU-006 | Modificar estatus (criterio de aceptación) · RF-30 · RN-11 | Diagrama de estados, SDD §5.3 | `dominio/modelos.py::Evento.estados_siguientes` · `servicio_eventos.py::cambiar_estado` | `test_unitarias_eventos::TestCicloDeVida` · `test_eventos::test_cp24_...` |
| HU-006 | Indicadores de ocupación por salón | IB-10 · IU-03 | `04_eventos_sprint2.sql::vw_ocupacion_salon` · `panel.html` | `test_eventos::test_ib10_...` |
| HU-006 | Aviso de eventos por cerrar · RN-14 · DA-04 | IB-11 · IU-03 · Escenario 8 | `vw_pendientes_cierre` · `panel.html` (botones «Se realizó» / «Se canceló») | `test_eventos::test_tablero_pendientes_...` |
| HU-006 | Indicadores del tablero | IB-01 · IU-03 | `vw_evento_detalle` · `repositorio_eventos.py::indicadores` | `test_eventos::test_indicadores_...` |
| HU-005/006 | RF-41 bitácora de alta, estatus y responsable | BITACORA | `ALTA_EVENTO`, `CAMBIO_ESTATUS`, `ASIGNAR_GERENTE` | `test_eventos::test_cp07_...` · `test_cp24_...` (CP-23 parcial) |
| HU-005/006 | RF-05 solo el gerente gestiona eventos · RNF-06 | Decorador `solo_gerente` | `rutas/eventos.py` | `test_eventos::test_rf05_...` |

Requisitos no funcionales atendidos en esta parte: RNF-01 (cotización en el navegador), RNF-05 (filtros como fragmentos fijos con parámetros), RNF-06, RNF-08, RNF-09 (clave y costo en la base), RNF-12 (rechazos con valores), RNF-13 (panel, listado, reservación, ficha y directorio verificados a 360 px sin desplazamiento horizontal).

## Casos del SRS, Anexo C

| Caso | Estado |
|---|---|
| CP-07 Registro y cotización | Automatizado y aprobado |
| CP-08 Clave de proyecto | Automatizado y aprobado |
| CP-09 Filtrado del listado | Automatizado y aprobado |
| CP-24 Estatus y gerente responsable | Automatizado y aprobado |
| CP-19 Atomicidad del alta conjunta | Parcial: se prueba con un rechazo de paquete. Con el aforo (BF001) en la Parte 2 |
| CP-10, CP-11, CP-12 | Parte 2 (HU-007) |
| CP-23 Bitácora | Parcial: alta y cambio de estatus. El registro de pago llega en el Sprint 3 |

Resultado: 91 pruebas aprobadas (52 del Sprint 1, incluida la del panel del commit de diseño, y 39 nuevas).
