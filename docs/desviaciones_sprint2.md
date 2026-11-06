# Desviaciones del Sprint 2 · Parte 1 respecto a la línea base

Continúa la numeración de `desviaciones_sprint1.md`. Conforme al Plan §11 e ISO/IEC 29110 (*Change Request* y *Correction Register*), cada una debe registrarse antes del cierre del sprint. Las marcadas «validar con el cliente» precisan reglas que el SRS deja abiertas.

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

## Hueco temporal entre la Parte 1 y la Parte 2

En esta parte la pantalla advierte el sobrecupo y deshabilita el botón, pero la base todavía no rechaza un evento que exceda el aforo o que se traslape: eso lo hacen los triggers BF001 y BF002 de HU-007 (DA-01). Por eso la rama de esta parte **no debe fusionarse a `main`** ni desplegarse para el cliente hasta terminar la Parte 2; sí puede fusionarse a `develop`.

## Alineación con `DESIGN.md`

Esta parte se construyó sobre el commit de diseño `e80db72` y sigue sus reglas: un solo azul de acción, ámbar solo para advertencias (por eso «Cotización» va en marino), confirmaciones con título, consecuencia y verbo propios, botones sin «+» como ícono, clave generada con «Copiar mensaje para el cliente» y «Ya la entregué», contexto oculto en acciones repetidas y ninguna pantalla con desplazamiento horizontal a 360 px.
