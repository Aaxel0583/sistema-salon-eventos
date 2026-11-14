# Registro de pruebas · Regresión del Release 3

Entregable *Test Report* del proceso de Implementación de Software (ISO/IEC 29110, perfil Básico) y «Registro de pruebas» del Plan de Proyecto, Anexo A. Corresponde a la tarea «Ejecutar las pruebas de regresión de todo el sistema» del Sprint 3.

| Dato | Valor |
|---|---|
| Fecha de ejecución | 14 de noviembre de 2026 (regresión oficial). Primera corrida en desarrollo: 11 de noviembre |
| Versión probada | Rama `feature/HU-009-HU-012` (Release 3) |
| Entorno | Windows, Python 3.11.9 (versión del plan), pytest 8.3.5, base de pruebas de `TEST_DATABASE_URL` reinstalada desde los scripts 00 a 06 |
| Comando | `pytest -v` |
| Resultado | **228 pruebas ejecutadas · 228 aprobadas · 0 fallidas · 0 omitidas** (641.57 s) |
| Revisión en navegador | Chromium, a 1280 px y a 360 px: ficha con pagos, tres reportes y tablero; flujo de abono, rechazo, finiquito y descarga |

> La regresión se repitió el 14/11/2026 en Python 3.11.9, la versión del plan. La corrida previa del 11/11 (Python 3.12, PostgreSQL local) contó 223 pruebas: la diferencia son las 5 que agregaron las revisiones de diseño 3 a 5 del Sprint 2 (4 en `test_eventos.py`, 1 en `test_unitarias.py`). Las pruebas de aceptación con el cliente (semana 14) se registran aparte, en el acta.

## 1. Resultado por archivo

| Archivo | Tipo | Pruebas | Aprobadas |
|---|---|---|---|
| `test_unitarias.py` | Unitaria | 33 | 33 |
| `test_unitarias_eventos.py` | Unitaria | 22 | 22 |
| `test_unitarias_disponibilidad.py` | Unitaria | 16 | 16 |
| `test_unitarias_finanzas.py` | Unitaria | 14 | 14 |
| `test_reglas_bd.py` | Integración (SQL directo) | 7 | 7 |
| `test_flujos.py` | Integración (web) | 13 | 13 |
| `test_eventos.py` | Integración | 22 | 22 |
| `test_disponibilidad.py` | Integración | 27 | 27 |
| `test_portal.py` | Integración | 12 | 12 |
| `test_pagos.py` | Integración | 34 | 34 |
| `test_reportes.py` | Integración | 22 | 22 |
| `test_conexion.py` | Integración | 1 | 1 |
| `test_zz_rendimiento.py` | Rendimiento | 5 | 5 |
| **Total** | | **228** | **228** |

Por sprint: 33 pruebas al cierre del Release 1, 152 al cierre del Release 2 (`feature/HU-007-HU-008`, 152 de 152 aprobadas el 14/11/2026) y 228 al cierre del Release 3. Ninguna prueba de los sprints anteriores se modificó para pasar: la regresión es limpia.

## 2. Casos de prueba del SRS (Anexo C)

| Caso | Descripción | Requisitos | Prueba automática | Resultado |
|---|---|---|---|---|
| CP-01 | Inicio de sesión por rol | RF-01, RF-02, RF-05 | `test_flujos` | Aprobado |
| CP-02 | Bloqueo al quinto intento | RF-03 | `test_flujos` | Aprobado |
| CP-03 | Alta de cliente y clave inicial | RF-07 a RF-09 | `test_flujos` | Aprobado |
| CP-04 | Rechazo de un cuarto salón (BF003) | RF-15, RN-03 | `test_reglas_bd` | Aprobado |
| CP-05 | Reducción de capacidad (BF004) | RF-16, RN-04 | `test_reglas_bd` | Aprobado |
| CP-06 | Paquete personalizado sin cliente | RF-19, RN-12 | `test_reglas_bd`, `test_flujos` | Aprobado |
| CP-07 | Registro y cotización | RF-20, RF-21 | `test_eventos` | Aprobado |
| CP-08 | Clave única EVT-AAAA-NNNN | RF-22, RN-08 | `test_eventos` | Aprobado |
| CP-09 | Listado con filtros | RF-28 | `test_eventos` | Aprobado |
| CP-10 | Rechazo por sobrecupo (BF001) | RF-23, RF-25, RN-01 | `test_disponibilidad` | Aprobado |
| CP-11 | Rechazo por traslape (BF002) | RF-24, RF-26, RN-02 | `test_disponibilidad` | Aprobado |
| CP-12 | Dos eventos el mismo día sin traslape | RF-27 | `test_disponibilidad` | Aprobado |
| CP-13 | Evento propio y aislamiento entre clientes | RF-39, RF-40, RNF-06 | `test_portal` | Aprobado |
| CP-14 | Pago y finiquito automático | RF-31, RF-33, RF-34, RN-10 | `test_pagos` | Aprobado |
| CP-15 | Rechazo de pago excedido (BF005) | RF-32, RN-05 | `test_pagos` | Aprobado |
| CP-16 | Semáforo de cartera | RF-37, RN-13 | `test_reportes` | Aprobado |
| CP-17 | Reportes de activos y realizados | RF-35, RF-36 | `test_reportes` | Aprobado |
| CP-18 | Descarga en CSV | RF-38 | `test_reportes`, `test_unitarias_finanzas` | Aprobado |
| CP-19 | Atomicidad del alta conjunta | RF-12, RNF-08 | `test_eventos`, `test_disponibilidad` | Aprobado |
| CP-20 | Recuperación de conexión | RNF-11 | `test_conexion` | Aprobado |
| CP-21 | Cambio obligatorio de la clave inicial | RF-04 | `test_flujos` | Aprobado |
| CP-22 | Recuperación de acceso y cierre de sesión | RF-06, RF-10, RF-11 | `test_flujos` | Aprobado |
| CP-23 | Registro en bitácora | RF-41, RNF-18 | `test_pagos`, `test_reglas_bd` | Aprobado |
| CP-24 | Estatus y gerente responsable | RF-29, RF-30, RN-11 | `test_eventos` | Aprobado |
| CP-25 | Administración de catálogos | RF-13, RF-14, RF-17, RF-18 | `test_flujos` | Aprobado |

**25 de 25 casos aprobados.**

## 3. Requisitos no funcionales

| RNF | Cómo se verificó | Resultado |
|---|---|---|
| RNF-01 Cotización en menos de 2 s | Se calcula en el navegador, sin ir al servidor | Cumple |
| RNF-02 Agenda en menos de 3 s | `/api/agenda` con índice por salón y fecha | Cumple |
| RNF-03 Reportes en menos de 5 s con 500 eventos | `test_zz_rendimiento`: cartera, activos, realizados, CSV y tablero con 500 eventos | Cumple (cada uno por debajo de 1 s en local) |
| RNF-04 Claves cifradas con sal | `test_unitarias` | Cumple |
| RNF-05 Consultas parametrizadas | Revisión de código: ningún valor se concatena al SQL | Cumple |
| RNF-06 Aislamiento entre usuarios | CP-13 y pruebas `test_rf05_*` de cada módulo | Cumple |
| RNF-07 Credenciales fuera del repositorio | `.env` en `.gitignore`; `git log` sin secretos | Cumple |
| RNF-08 Transacción única | CP-19 y `test_anticipo_a_horario_ya_apartado_no_guarda_nada` | Cumple |
| RNF-09 Reglas en la base | Pruebas `_bd_` y `_por_sql_directo` (BF001 a BF005, BF0010) | Cumple |
| RNF-10 Disponibilidad en horario operativo | Depende del despliegue; se registra durante el acompañamiento | **Pendiente de despliegue** |
| RNF-11 Reconexión sin perder la sesión | CP-20 | Cumple |
| RNF-12 Mensajes con causa y valores | CP-10, CP-11, CP-15 | Cumple |
| RNF-13 Utilizable a 360 px | Medición en navegador: ninguna pantalla nueva se desborda | Cumple |
| RNF-14 Clave dictable | `test_unitarias` | Cumple |
| RNF-15 Chrome, Firefox y Edge | Probado en Chromium | **Pendiente: Firefox y Edge** |
| RNF-16 Respaldo diario | Función del servicio Neon | **Pendiente: prueba de restauración** |
| RNF-17 Instalación sin tocar el código | `NOMBRE_NEGOCIO` y conexión en `.env` | Cumple |
| RNF-18 Bitácora inalterable | CP-23 y `test_rnf18_*` | Cumple |

## 4. Indicadores del Plan §3.3 al cierre del Sprint 3

| Indicador | Meta | Resultado |
|---|---|---|
| Eventos registrados con sobrecupo | 0 % | 0 %: BF001 lo impide en la base, incluso por SQL directo y con reservas simultáneas |
| Trazabilidad de historias de usuario | 100 % | 12 de 12 historias con requisito, diseño, código y prueba (`trazabilidad_sprint1.md` a `sprint3.md`) |
| Densidad de defectos | Menor a 1 por KLOC | 0 defectos abiertos en 7.4 KLOC de aplicación (más 2.5 KLOC de pruebas). Los defectos encontrados en revisión (R-01 a R-04 del Sprint 2 y los de este sprint) se corrigieron antes del cierre. **El equipo debe confirmar el conteo con su bitácora TSP de defectos** |

## 5. Defectos encontrados y corregidos en el Sprint 3

| # | Hallazgo | Corrección |
|---|---|---|
| S3-01 | La ficha del evento se desbordaba a 360 px cuando el cliente tenía un correo largo (defecto del Sprint 2, detectado al revisar el panel de pagos) | El dato de contacto se parte dentro de su renglón (`estilos.css`, `.datos dd`) |
| S3-02 | En los reportes la clave del evento se partía en tres renglones y la tabla de proyectos activos no cabía a 1280 px | Clave y etiquetas sin corte; tabla más compacta y página de reportes más ancha |
| S3-03 | CP-20 (reconexión) no tenía prueba automática desde el Sprint 1 | Se agregó `test_conexion.py` |
