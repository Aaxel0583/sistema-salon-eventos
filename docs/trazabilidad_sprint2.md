# Registro de trazabilidad · Sprint 2

Complementa el entregable *Traceability Record* (ISO/IEC 29110, SI) con el código: HU → RF/RN → elemento de diseño → archivo → prueba. Cubre HU-005 a HU-008.

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
| HU-007 | RF-24 consulta de agenda del salón en la fecha capturada | C-04 · `/api/agenda` · índice `ix_evento_salon_fecha` | `repositorio_eventos.py::agenda` · `servicio_eventos.py::ServicioReservaciones.agenda`, `Agenda` · `rutas/agenda.py` · bloque `data-agenda` de `eventos/nuevo.html` y `app.js` | `test_disponibilidad::test_cp11_...` (CP-11) · `test_rf24_...` · `test_unitarias_disponibilidad::TestAgenda` |
| HU-007 | RF-25 rechazo por sobrecupo con ambos valores · RN-01 | C-11 · IB-02 · BF001 · DA-01 | `05_reglas_sprint2.sql::fn_validar_aforo`, `trg_evento_aforo` | `test_disponibilidad::test_cp10_bd_...`, `test_cp10_pantalla_...` (CP-10) · `test_bf001_...` |
| HU-007 | RF-26 rechazo por traslape · RN-02 | C-11 · IB-03 · BF002 · DA-01 | `05_reglas_sprint2.sql::fn_validar_disponibilidad`, `trg_evento_disponibilidad` | `test_disponibilidad::test_cp11_bd_...` (CP-11) · `test_bf002_...` · `test_rn02_...` |
| HU-007 | RN-02 precisada (D-20): solo el anticipo aparta el salón; las cotizaciones compiten hasta que una se confirma | IB-03 · BF002 | `fn_validar_disponibilidad` (solo cuenta confirmados y realizados) · `modelos.py::ESTADOS_QUE_APARTAN`, `Evento.ocupa_salon` · `Agenda.cotizaciones_encimadas` · aviso «También cotizado» en `app.js` | `test_disponibilidad::test_d20_...` (SQL y pantalla) · `test_unitarias_disponibilidad::test_solo_el_anticipo_...`, `test_cotizaciones_compiten_...` |
| HU-007 | RF-27 dos eventos el mismo día sin traslape | IB-03 | `fn_validar_disponibilidad` (horarios contiguos permitidos) | `test_disponibilidad::test_cp12_...` (CP-12) |
| HU-007 | Las reglas se aplican en la base (criterio de aceptación) · RNF-09 | DA-01 · Escenario 5, Figura 8 | Triggers `BEFORE INSERT OR UPDATE` sobre EVENTO; candado por salón compartido con IB-05 | Pruebas `_bd_` por SQL directo · `test_bf002_dos_confirmaciones_simultaneas_...` |
| HU-007 | Mensaje de rechazo con causa y valores · RNF-12 | C-10 traducción de errores | `datos/errores.py::traducir_error` (códigos BF) · aviso rojo en IU-06 | `test_cp10_pantalla_...` · `test_cp11_agenda_...` |
| HU-007 | RF-12 atomicidad del alta conjunta ante un rechazo de aforo · RNF-08 | DA-05 · Escenario 2 | `servicio_eventos.py::registrar` (una sola transacción) | `test_disponibilidad::test_cp19_...` (CP-19) |
| HU-008 | RF-39 solo los eventos del titular autenticado | C-07 · IU-09 · Escenario 7, Figura 10 | `repositorio_eventos.py::de_cliente` · `servicio_portal.py::ServicioPortal.mis_eventos` · `rutas/portal.py` · `portal/mis_eventos.html` | `test_portal::test_cp13_cliente_ve_solo_sus_eventos` (CP-13) |
| HU-008 | RF-40 detalle con menú, pagos y saldo | C-07 · IU-10 · vista IB-01 · tabla PAGO | `repositorio_eventos.py::por_clave_de_cliente`, `pagos` · `servicio_portal.py::detalle` · `dominio/modelos.py::Pago` · `portal/detalle.html` | `test_portal::test_cp13_detalle_...` (CP-13) |
| HU-008 | Impide consultar el evento de otro cliente · RNF-06 | Filtro por titular tomado de la sesión (C-01) | `rutas/portal.py` (`usuario_actual()`), consulta con clave **y** titular | `test_portal::test_cp13_evento_ajeno_...` (CP-13) · `test_claves_mal_formadas_...` |
| HU-007/008 | RF-05 la agenda es del gerente y el portal del cliente | Decoradores `solo_gerente`, `solo_cliente` | `rutas/agenda.py` · `rutas/portal.py` | `test_rf05_la_agenda_...` · `test_portal_exige_sesion_...` |
| HU-005/006 | RF-41 bitácora de alta, estatus y responsable | BITACORA | `ALTA_EVENTO`, `CAMBIO_ESTATUS`, `ASIGNAR_GERENTE` | `test_eventos::test_cp07_...` · `test_cp24_...` (CP-23 parcial) |
| HU-005/006 | RF-05 solo el gerente gestiona eventos · RNF-06 | Decorador `solo_gerente` | `rutas/eventos.py` | `test_eventos::test_rf05_...` |

Requisitos no funcionales atendidos en esta parte: RNF-01 (cotización en el navegador), RNF-05 (filtros como fragmentos fijos con parámetros), RNF-06, RNF-08, RNF-09 (clave y costo en la base), RNF-12 (rechazos con valores), RNF-13 (panel, listado, reservación, ficha y directorio verificados a 360 px sin desplazamiento horizontal).

En la Parte 2: RNF-02 (agenda apoyada en el índice de salón y fecha), RNF-05, RNF-06 (titular desde la sesión), RNF-08 (CP-19), RNF-09 (reglas en la base), RNF-12 (rechazos con salón, fecha, horario, clave y cifras) y RNF-13 (reservación con agenda, Mis eventos y Detalle verificados a 360 px).

## Casos del SRS, Anexo C

| Caso | Estado |
|---|---|
| CP-07 Registro y cotización | Automatizado y aprobado |
| CP-08 Clave de proyecto | Automatizado y aprobado |
| CP-09 Filtrado del listado | Automatizado y aprobado |
| CP-24 Estatus y gerente responsable | Automatizado y aprobado |
| CP-10 Rechazo por sobrecupo | Automatizado y aprobado (SQL directo y pantalla) |
| CP-11 Rechazo por traslape | Automatizado y aprobado (SQL directo, agenda y pantalla) |
| CP-12 Horarios contiguos | Automatizado y aprobado |
| CP-13 Evento propio y aislamiento entre clientes | Automatizado y aprobado |
| CP-19 Atomicidad del alta conjunta | Automatizado y aprobado con el rechazo de aforo BF001 |
| CP-23 Bitácora | Parcial: alta y cambio de estatus. El registro de pago llega en el Sprint 3 |

Resultado: 147 pruebas aprobadas (52 del Sprint 1, 40 de la Parte 1 con la corrección R-01 y 55 de la Parte 2 con la precisión D-20).
