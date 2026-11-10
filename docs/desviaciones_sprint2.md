# Desviaciones del Sprint 2 respecto a la línea base

Parte 1 (HU-005, HU-006): D-10 a D-19. Parte 2 (HU-007, HU-008): D-20 a D-27. Continúa la numeración de `desviaciones_sprint1.md`. Conforme al Plan §11 e ISO/IEC 29110 (*Change Request* y *Correction Register*), cada una debe registrarse antes del cierre del sprint. Las marcadas «validar con el cliente» precisan reglas que el SRS deja abiertas.

| # | Documento y apartado | Lo que dice la línea base | Lo que hace el código | Justificación | Acción sugerida |
|---|---|---|---|---|---|
| D-10 | SRS RN-08 | Clave EVT-AAAA-NNNN, sin decir de qué año | AAAA es el año en que se **registra** el evento; NNNN reinicia cada año | Una boda de 2027 cotizada en 2026 recibe EVT-2026-… y la clave no cambia nunca, aunque cambie la fecha | Validar con el cliente y precisar RN-08 |
| D-11 | SRS RN-09, SDD §8.4 | «Se recalcula al editar el evento» | Se recalcula solo si cambian salón, paquete o asistentes. Un cambio posterior de renta o de precio del paquete **no** altera eventos ya cotizados | Lo pactado con el cliente no debe moverse por una actualización del catálogo | Validar con el cliente · Correction Register |
| D-12 | Matriz del SRS §9 | RF-30 (cambio de estatus) pertenece a HU-009, Sprint 3 | Se construye en el Sprint 2 junto con HU-006 | El criterio de aceptación de HU-006 pide «modificar el estatus» y el tablero (Figura 29) cierra eventos con un clic | CRQ · mover RF-30 a HU-006 o declararlo compartido |
| D-13 | SDD §5.3 (Figura 25) | Transiciones descritas sin condiciones de fecha | Realizado solo desde el día del evento; Confirmado solo si la fecha no ha pasado; Realizado y Cancelado son finales | Evita marcar como realizado un evento futuro y confirmar uno vencido | Correction Register · agregar las guardas al diagrama |
| D-14 | SDD §6.1.3, IU-03 | Indicador «Por cobrar» sin definición | Suma el saldo de eventos **confirmados y realizados** no finiquitados; una cotización no cuenta | Una cotización aún no es un compromiso del cliente | Validar con el cliente |
| D-15 | SDD IB-10 | «Cuenta los eventos futuros de cada salón» | Además del conteo, muestra el % de aforo promedio que ocupan esos eventos (rojo arriba de 80 %) | El wireframe de la Figura 29 muestra un porcentaje de aforo que IB-10 no definía | Correction Register · completar la definición de IB-10 |
| D-16 | SDD IU-03, Figura 29 | Cuatro tarjetas de indicadores y un aviso de eventos por cerrar debajo de la ocupación | Los indicadores (eventos activos, por cobrar, finiquitados) van en la línea de conteos bajo el título; los eventos vencidos van dentro de «Pendientes», y en celular cada uno es una tarjeta con sus dos acciones. «Vencen en 21 días» aún no se muestra | Sigue `DESIGN.md` («Panel»), que el equipo adoptó después del SDD. «Vencen en 21 días» depende de la vista de cartera IB-08 (HU-010, Sprint 3) | Correction Register · actualizar la Figura 29 con el panel vigente |
| D-17 | SRS RF-13 | El salón tiene «disponibilidad», sin efecto definido | Un salón marcado como no disponible no recibe reservaciones nuevas; las existentes no se tocan | Es el uso natural del campo (mantenimiento, remodelación) | Validar con el cliente |
| D-18 | SDD Anexo A | `/eventos/<id>` con GET y POST, sin decir qué hace el POST | El POST asigna el gerente responsable (RF-29) | Se mantiene dentro del catálogo de rutas en vez de crear una ruta nueva | Correction Register |
| D-19 | Cronograma / Plan Anexo A | Sprint 2 del 23 de octubre al 5 de noviembre | Parte 1 terminada el 6 de noviembre; Parte 2 pendiente | Arrastre del inicio tardío del Sprint 1 (D-09) | Progress Status Record · registrar la variación y el plan de recuperación antes del cierre del 20 de noviembre |

## Parte 2 · HU-007 y HU-008

| # | Documento y apartado | Lo que dice la línea base | Lo que hace el código | Justificación | Acción sugerida |
|---|---|---|---|---|---|
| D-20 | SRS RN-02, RF-26 | Traslape contra «otro evento vigente»; solo aclara que un cancelado no ocupa el salón | Ocupa el salón todo evento **no cancelado**: cotización, confirmado o realizado. Una cotización aparta el horario | Coincide con BF004, que ya trataba la cotización como agendada, y un evento realizado ocupó físicamente el salón | **Validar con el cliente**: ¿una cotización debe apartar la fecha? · precisar RN-02 |
| D-21 | SRS RN-01, SDD IB-02 | El aforo no se excede, sin decir cuándo se evalúa | BF001 se evalúa al registrar y al cambiar salón o asistentes; **no** al cambiar el estatus | RN-04 permite bajar la capacidad cuando el evento grande ya pasó; cerrar ese evento como realizado no debe fallar | Correction Register · precisar IB-02 |
| D-22 | SDD IB-05 (script 02, Sprint 1) | Trigger de reducción de capacidad, línea base del Release 1 | Se le agregó un candado por salón que comparte con IB-02 e IB-03 | Sin él, una reserva y una reducción de capacidad simultáneas podían dejar un evento con sobrecupo, contra el objetivo de 0 % | Correction Register · las bases instaladas vuelven a ejecutar el script 02 |
| D-23 | SDD Anexo A, `/api/agenda` | «Alimenta la consulta de agenda y la cotización en vivo» | Solo entrega la agenda (`salon`, `fecha` y, opcionales, `inicio` y `fin`). La cotización en vivo se calcula en el navegador | RNF-01: la cotización no debe esperar al servidor; así quedó desde la Parte 1 | Correction Register · corregir la descripción de la ruta |
| D-24 | SDD §4.1, Figura 3 | La clase Pago pertenece al módulo financiero (Sprint 3) | Se adelantó en modo de **solo lectura** para el portal | RF-40 (Sprint 2) pide mostrar los pagos al cliente. El registro de abonos (IB-06, BF005) sigue en el Sprint 3 | Correction Register |
| D-25 | SDD IU-09 e IU-10, Figuras 35 y 36 | Lista de eventos con clave, fecha y estatus; detalle con resumen, menú, pagos y saldo | La lista son tarjetas separadas en «Próximos» y «Anteriores»; el detalle agrega «Te atiende» (gerente responsable) | Sigue `DESIGN.md`: el cliente consulta desde el celular y una tabla no cabe en 360 px | Correction Register · actualizar las Figuras 35 y 36 |
| D-26 | SRS CP-13 | El evento ajeno «se niega y el sistema lo devuelve a su propio panel» | Además, un evento ajeno y uno inexistente responden exactamente igual | No revelar qué claves existen (RNF-06) | Ninguna: precisa el caso de prueba |
| D-27 | Cronograma / Plan Anexo A | Sprint 2 del 23 de octubre al 5 de noviembre | Parte 2 terminada el 10 de noviembre: 5 días después de lo planeado | Arrastre de D-09 y D-19 | Progress Status Record · registrar la fecha real y el plan de recuperación del Sprint 3 |

## Cierre del hueco entre la Parte 1 y la Parte 2

La Parte 1 advertía el sobrecupo en pantalla pero la base aún no lo rechazaba. Con el script `05_reglas_sprint2.sql` las reglas RN-01 y RN-02 ya se imponen en la base, por lo que el Release 2 puede fusionarse a `main` y etiquetarse.

Al instalar el script 05 sobre una base con datos de la Parte 1, el instalador avisa cuántos eventos vigentes exceden el aforo o se enciman. No los modifica: el gerente debe corregirlos.

## Alineación con `DESIGN.md`

Esta parte se construyó sobre el commit de diseño `e80db72` y sigue sus reglas: un solo azul de acción, ámbar solo para advertencias (por eso «Cotización» va en marino), confirmaciones con título, consecuencia y verbo propios, botones sin «+» como ícono, clave generada con «Copiar mensaje para el cliente» y «Ya la entregué», contexto oculto en acciones repetidas y ninguna pantalla con desplazamiento horizontal a 360 px.

## Correcciones de la revisión del PR #2

| # | Hallazgo | Corrección | Verificación |
|---|---|---|---|
| R-01 | Al cambiar el estatus en la ficha, el diálogo era genérico («¿Cambiar el estatus…?») y su botón rojo decía «Cambiar estatus» aunque se estuviera confirmando el evento. Contradecía el PR y DESIGN.md («Modal de confirmación»: título y verbo propios; rojo lleno solo para lo destructivo). | Cada opción del estatus trae su título, consecuencia, verbo y tono: «Confirmar evento» y «Marcar como realizado» en azul; «Cancelar evento» en rojo. En el panel, «Se realizó» confirma en azul y «Se canceló» en rojo. El diálogo (`app.js`) toma los textos de la opción elegida (`data-confirmar-segun`) y el color de `data-tono`; sin tono sigue en rojo, así que las confirmaciones del Sprint 1 no cambian. | `test_eventos::test_confirmacion_propia_por_estatus` y revisión en navegador de los cinco diálogos (color real del botón y que «Cancelar» no envía nada). |
| R-02 | En el diálogo de cancelación quedaban juntos «Cancelar» y «Cancelar evento». | El botón de salida dice «Mantener evento» en ese caso (`data-volver`); el foco inicia en él. | Misma prueba y revisión en navegador. |
