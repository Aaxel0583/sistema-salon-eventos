# Manual de usuario

Sistema de Reservaciones y Gestión para Salón de Eventos · versión 1.0 (Release 3)

Este manual tiene dos partes: una para el **gerente** del salón y otra para el **cliente**. El sistema funciona en Chrome, Firefox y Edge, en computadora y en celular, sin instalar nada.

---

## Parte 1 · Gerente

### 1. Entrar al sistema

1. Abre la dirección del sistema que te dio quien lo instaló.
2. Escribe tu **correo o celular** y tu **clave**, y pulsa **Entrar**.
3. La primera vez el sistema te pide definir tu propia clave: mínimo 8 caracteres y distinta de la inicial.

Si te equivocas cinco veces seguidas la cuenta se bloquea. Otro gerente no puede desbloquearte: se hace desde la consola del sistema (ver el manual técnico, apartado 6).

Para salir, abre el menú con tu nombre (arriba a la derecha) y pulsa **Cerrar sesión**. En ese menú también está **Cambiar mi clave**.

### 2. Panel

Es la primera pantalla. De arriba hacia abajo:

- **Conteos:** eventos activos, total por cobrar, finiquitados, clientes y paquetes. Cada uno te lleva a su listado.
- **Pendientes:** lo que necesita tu atención hoy.
  - *Cuentas vencidas:* eventos que ya pasaron y todavía deben. **Ver cuentas vencidas** abre el reporte.
  - *Cuentas que vencen en 21 días:* eventos próximos con saldo. Es el momento de cobrar.
  - *Clientes bloqueados:* **Darle clave nueva** los lleva al directorio.
  - *Salones no disponibles.*
  - *Eventos que ya pasaron y siguen abiertos:* indica con **Se realizó** o **Se canceló** qué ocurrió. El sistema nunca lo decide por ti.
- **Ocupación por salón** y **Actividad reciente**.

### 3. Clientes

Los clientes no se registran solos: tú los das de alta.

1. **Clientes → Nuevo cliente.** Captura el nombre y al menos un dato de contacto (correo o celular). Ninguno puede repetirse entre clientes.
2. Al guardar aparece la **clave inicial** en un recuadro verde. **Se muestra una sola vez.** Usa **Copiar mensaje para el cliente** para enviársela o díctala, y después pulsa **Ya la entregué**.
3. Si un cliente olvida su clave o se bloquea, búscalo en el directorio y pulsa **Clave nueva**. La clave anterior deja de servir.

### 4. Catálogos

- **Salones:** son tres y no se pueden agregar más. De cada uno editas descripción, capacidad, costo de renta y si está disponible. No puedes bajar la capacidad por debajo del evento más grande que ya tenga agendado: el sistema te dice cuál es.
- **Platillos:** alta y baja por categoría (entrada, plato fuerte, guarnición, postre, bebida). Un platillo que forma parte de un paquete no se elimina.
- **Paquetes:** **Armar paquete** combina platillos y fija el precio por persona. Un paquete *estándar* sirve para cualquier cliente; uno *personalizado* pertenece a un cliente y solo se le puede cotizar a él.

### 5. Cotizar y reservar un evento

1. **Nueva reservación** (en el Panel o en Eventos).
2. Elige al cliente. Si es nuevo, dalo de alta ahí mismo: al guardar, el sistema te muestra también su clave inicial.
3. Elige salón, paquete, fecha, horario y número de invitados. A la derecha ves la **cotización** recalcularse (renta del salón + precio por persona × invitados) y los lugares disponibles.
4. Debajo aparece la **agenda del salón** en esa fecha: qué eventos ya lo tienen apartado y cuáles están solo cotizados.
5. **Guardar reservación.** El evento queda en estatus **Cotización** y recibe su clave, por ejemplo `EVT-2026-0042`.

El sistema rechaza la reservación, y te explica por qué, cuando:

- los invitados exceden la capacidad del salón;
- el horario se encima con un evento que ya apartó el salón.

> **Una cotización no aparta el salón.** Puede haber varias cotizaciones para el mismo horario. El salón lo aparta el evento que da su anticipo y queda **Confirmado**: el primero que lo hace se queda con la fecha.

### 6. Dar seguimiento a un evento

En **Eventos** buscas por clave, nombre o cliente y filtras por estatus y salón. Al abrir un evento ves su **ficha**:

- **Datos del evento** y **Estado de cuenta** (costo, pagado y saldo pendiente).
- **Pagos:** el historial de abonos y la captura de uno nuevo.
- **Gestión:** estatus y gerente responsable.
- **Menú contratado.**

Los estatus son:

| Estatus | Significado | Puede pasar a |
|---|---|---|
| Cotización | Se le dio precio al cliente; no aparta el salón | Confirmado, Cancelado (y Realizado si la fecha ya llegó) |
| Confirmado | Dio anticipo; aparta el salón | Realizado (desde el día del evento), Cancelado |
| Realizado | El evento se llevó a cabo | — |
| Cancelado | No se llevará a cabo; libera el salón | — |

Realizado y Cancelado son definitivos.

### 7. Registrar un abono

1. Abre la ficha del evento y ve a **Pagos → Registrar abono**.
2. Escribe el **monto**. **Todo el saldo** lo llena con lo que falta por pagar.
3. Elige la **forma de pago** (efectivo, transferencia, tarjeta, depósito o cheque) y, si quieres, una **referencia** (folio, SPEI o número de recibo).
4. Si el evento está en cotización, verás marcada la casilla **Es el anticipo: confirmar el evento y apartar su horario.** Déjala marcada para cobrar y confirmar en un solo paso.
5. Pulsa **Registrar abono** y revisa el monto en la ventana de confirmación.

Lo que debes saber:

- **No puedes cobrar más de lo que se debe.** Si el monto excede el saldo, el sistema lo rechaza y te dice cuál es el saldo.
- **Cuando el saldo llega a cero el evento queda _Finiquitado_ con la fecha del día.** Esa marca la pone el sistema; no hay botón para ponerla ni para quitarla.
- **Un abono registrado no se puede modificar ni borrar.** Por eso la ventana de confirmación te muestra el monto. Si te equivocas, avisa al administrador del sistema.
- Un evento cancelado o ya liquidado no admite abonos.

### 8. Reportes

En **Reportes** hay tres pestañas. Cada una tiene sus totales arriba, sus filtros y el botón **Descargar CSV**, que baja un archivo con las mismas columnas y los mismos filtros que ves en pantalla. El archivo abre en Excel.

| Reporte | Qué muestra | Para qué sirve |
|---|---|---|
| **Cartera** | Eventos confirmados o realizados con saldo, clasificados por semáforo | Cobrar antes de que el evento ocurra |
| **Activos** | Eventos en cotización o confirmados, por fecha, con cliente, salón, paquete, aforo, costo y saldo | Conocer la carga de trabajo comprometida |
| **Realizados** | Eventos que ya se llevaron a cabo, con costo, pagado y saldo restante | Revisar el histórico y lo que quedó sin liquidar |

El semáforo de cartera:

| Color | Categoría | Cuándo |
|---|---|---|
| Rojo | Vencida | La fecha del evento ya pasó y aún debe |
| Ámbar | Próxima a vencer | El evento es hoy o dentro de los próximos 21 días |
| Verde | Vigente | Faltan más de 21 días |

Al pulsar la clave de un renglón abres la ficha del evento para registrar el abono.

### 9. Mensajes frecuentes

| Mensaje | Qué hacer |
|---|---|
| «…admite N personas y el evento es para M» | Reduce los invitados o elige un salón más grande |
| «…ya está ocupado el … por el evento EVT-…» | Cambia el horario, la fecha o el salón |
| «No se puede confirmar…: ya está apartado… por el evento…, que ya dio anticipo» | Otra cotización se confirmó primero. Ofrece otro horario o cancela esta |
| «El abono de $… excede el saldo pendiente de $…» | Captura el saldo o menos |
| «Ese correo ya pertenece a otro usuario» | Busca al cliente en el directorio: ya está registrado |
| «La página expiró» | Vuelve a cargar la página e inténtalo de nuevo |

---

## Parte 2 · Cliente

### 1. Entrar

El salón te da una **clave inicial**. Entra con tu **correo o tu celular** (el que le diste al salón) y esa clave. Puedes escribirla en minúsculas y sin el guion. La primera vez el sistema te pide cambiarla por una tuya, de al menos 8 caracteres.

Si olvidas tu clave o tu cuenta se bloquea, pide una nueva al salón.

### 2. Mis eventos

Ves únicamente tus eventos, separados en **Próximos**, **Anteriores** y **Cancelados**, cada uno con su fecha, su estatus y tu saldo pendiente.

### 3. Detalle de tu evento

Al abrir un evento encuentras:

- **Tu evento:** clave, salón, fecha, horario, invitados y quién te atiende.
- **Estado de cuenta:** costo total, lo que has pagado y tu saldo pendiente.
- **Menú contratado** y su precio por persona.
- **Pagos:** cada abono con su fecha, forma de pago, referencia y monto.

Cuando terminas de pagar, tu evento aparece como **liquidado**. Desde el portal no se modifica nada: si algo no coincide con lo que acordaste, comunícate con el salón.

> Si tu evento dice **Cotización**, tu fecha todavía no está apartada. Se aparta cuando das tu anticipo y el salón lo confirma.
