# Registro de trazabilidad · Sprint 3

Complementa el entregable *Traceability Record* (ISO/IEC 29110, SI) con el código: HU → RF/RN → elemento de diseño → archivo → prueba. Cubre HU-009 a HU-012. Con este sprint las doce historias quedan trazadas (indicador del Plan §3.3: 100 %).

| HU | Requisito | Diseño | Implementación | Prueba |
|---|---|---|---|---|
| HU-009 | RF-30 modificar el estatus · RN-11 | C-05/C-08 · IU-07 · SDD §5.3 | `servicio_eventos.py::cambiar_estado` (Sprint 2, D-12) · casilla «Es el anticipo» en `servicio_pagos.py::registrar` (D-33) | `test_eventos::test_cp24_...` (CP-24) · `test_pagos::test_anticipo_confirma_...` |
| HU-009 | RF-31 registrar pago con monto, tipo y referencia | C-05 · IU-07 · tabla PAGO · ruta `/eventos/<id>/pagos` | `rutas/pagos.py` · `servicio_pagos.py::ServicioPagos.registrar` · `repositorio_pagos.py` · panel «Pagos» de `eventos/ficha.html` | `test_pagos::test_cp14_abono_parcial_...` (CP-14) · `test_abono_mal_capturado_...` |
| HU-009 | RF-32 rechazar el pago mayor al saldo · RN-05 | C-11 · IB-06 · BF005 · Escenario 6 | `06_finanzas_sprint3.sql::fn_validar_pago`, `trg_pago_saldo`, `fn_registrar_pago` | `test_pagos::test_cp15_pago_excedido_...`, `test_cp15_la_base_responde_bf005` (CP-15) · `test_pago_excedido_por_sql_directo` · `test_dos_abonos_simultaneos_...` |
| HU-009 | RF-33 saldo = costo − pagos | IB-01 | `04_eventos_sprint2.sql::vw_evento_detalle` (columna `saldo`, sin almacenar) | `test_pagos::test_cp14_abono_parcial_...` |
| HU-009 | RF-34 finiquito automático con fecha · RN-10 | C-11 · IB-06 · BF0010 · SDD §5.3 | `fn_aplicar_finiquito`, `trg_pago_finiquito` · `fn_proteger_finiquito`, `trg_evento_finiquito` | `test_pagos::test_cp14_pago_exacto_finiquita_...` (CP-14) · `test_finiquito_automatico_por_sql_directo` · `test_rn10_...` |
| HU-009 | El finiquito no es editable (IU-07) | IU-07 | `eventos/ficha.html` sin control de finiquito · `fn_proteger_finiquito` | `test_pagos::test_ficha_ofrece_abono_...` · `test_rn10_el_finiquito_no_se_marca_a_mano` |
| HU-009 | Abonos inalterables (D-31) | SDD §5.3 | `fn_pago_inalterable`, `fn_validar_costo_contra_pagos` | `test_pagos::test_un_abono_no_se_modifica_...` · `test_el_costo_no_baja_de_lo_pagado` |
| HU-009 | RF-41 bitácora de pago y de estatus · RNF-18 | C-10 · BITACORA | `servicio_pagos.py` (`REGISTRO_PAGO`, `FINIQUITO`) · `servicio_eventos.py` (`CAMBIO_ESTATUS`) | `test_pagos::test_cp23_...` (CP-23) · `test_abono_rechazado_no_deja_bitacora` |
| HU-009 | Mensaje con causa y valores · RNF-12 | C-10 | `datos/errores.py` (BF005, BF010→BF0010) · la ficha se devuelve con lo capturado (`rutas/eventos.py::presentar_ficha`) | `test_pagos::test_cp15_pago_excedido_...` · `test_bf010_se_presenta_...` |
| HU-009 | Atomicidad · RNF-08 | DA-05 | Una transacción por abono en `ServicioPagos.registrar` | `test_pagos::test_anticipo_a_horario_ya_apartado_no_guarda_nada` |
| HU-009 | Acceso solo del gerente · RF-05 | C-01 | `@solo_gerente` en `rutas/pagos.py` | `test_pagos::test_rf05_...` · `test_sin_sesion_...` |
| HU-010 | RF-37 cartera con semáforo y total por categoría · RN-13 | C-06 · IB-08 · IU-08 | `06_finanzas_sprint3.sql::vw_cartera` · `repositorio_reportes.py::cartera`, `totales_cartera` · `servicio_reportes.py::cartera` · `reportes/reporte.html` | `test_reportes::test_cp16_...` (CP-16, cinco pruebas) |
| HU-010 | Corte de 21 días previos al evento | IB-08 | `vw_cartera` (`CURRENT_DATE + 21`) · `modelos.py::DIAS_CORTE_CARTERA` | `test_reportes::test_cp16_bordes_del_corte_de_21_dias` |
| HU-010 | Misma cifra en el reporte y en el tablero (SDD IU-08) | IB-08 · IU-03 | `repositorio_eventos.py::indicadores` (lee `vw_cartera`) · «Pendientes» de `panel.html` | `test_reportes::test_tablero_y_reporte_muestran_la_misma_cartera` |
| HU-011 | RF-35 proyectos activos por fecha con cliente, salón, paquete, aforo, costo y saldo | C-06 · IB-09 · IU-08 | `vw_proyectos_activos` · `repositorio_reportes.py::activos` · `servicio_reportes.py::activos` | `test_reportes::test_cp17_activos_...` (CP-17) |
| HU-012 | RF-36 proyectos realizados con costo, pagado y saldo | C-06 · IB-09 · IU-08 | `vw_proyectos_realizados` · `repositorio_reportes.py::realizados` · `servicio_reportes.py::realizados` | `test_reportes::test_cp17_realizados_...` (CP-17) |
| HU-010 a HU-012 | RF-38 descarga en CSV con las columnas de la pantalla | C-06 · IE-02 · Escenario 9 | `servicio_reportes.py::Reporte.a_csv` (misma lista de columnas que la plantilla) · `rutas/reportes.py` (`?formato=csv`) | `test_reportes::test_cp18_...` (CP-18, cinco pruebas) · `test_unitarias_finanzas::TestCsv` |
| HU-010 a HU-012 | RNF-03 reportes en menos de 5 s con 500 eventos | — | Vistas sobre `vw_evento_detalle`; índices `ix_pago_evento`, `ix_evento_salon_fecha` | `test_zz_rendimiento::test_rnf03_...` (cinco rutas) |
| HU-010 a HU-012 | RNF-05 consultas parametrizadas | C-10 | `repositorio_reportes.py` (filtros como fragmentos fijos) | Revisión de código · `test_reportes` con filtros no válidos |
| HU-010 a HU-012 | Acceso solo del gerente · RF-05 · RNF-06 | C-01 | `@solo_gerente` en `rutas/reportes.py` | `test_reportes::test_rf05_...` · `test_sin_sesion_...` |

## Casos de prueba del SRS (Anexo C) cubiertos en este sprint

| Caso | Resultado | Prueba automática |
|---|---|---|
| CP-14 Registro de pago y finiquito automático | Aprobado | `test_pagos::test_cp14_*` |
| CP-15 Rechazo de pago excedido (BF005) | Aprobado | `test_pagos::test_cp15_*` |
| CP-16 Semáforo de cartera | Aprobado | `test_reportes::test_cp16_*` |
| CP-17 Reportes de activos y realizados | Aprobado | `test_reportes::test_cp17_*` |
| CP-18 Descarga en CSV | Aprobado | `test_reportes::test_cp18_*` |
| CP-23 Registro en bitácora | Aprobado | `test_pagos::test_cp23_*` |

Con esto los 25 casos del Anexo C tienen al menos una prueba automática aprobada (ver `registro_pruebas.md`).
