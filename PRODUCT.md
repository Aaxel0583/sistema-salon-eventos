# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Gerente del salón** (usuario principal). Trabaja mitad en PC y mitad en celular: captura con calma en el escritorio (registra clientes, edita salones, arma paquetes y, desde el Sprint 2, cotiza y reserva) y consulta rápido desde el celular cuando está en el salón, entre clientes y proveedores.
- **Cliente del salón**. Perfil mixto: desde familias que organizan una boda o unos XV años hasta empresas con eventos corporativos. Entra con correo o celular y una clave que el gerente le entrega (a veces dictada). Consulta su evento, el menú contratado, sus pagos y su saldo.

## Product Purpose

Sistema de reservaciones y gestión para un salón de eventos con tres espacios: cotizar, reservar y cobrar eventos, y administrar clientes, salones, platillos y paquetes de banquete. Tiene éxito cuando el gerente nunca agenda dos eventos encimados ni sobrevende un salón, y cuando el cliente sabe en todo momento qué contrató y cuánto debe.

Es a la vez un proyecto escolar (entregado y evaluado con SRS/SDD bajo ISO/IEC 29110, por sprints) y un sistema que un salón real va a usar. Las decisiones deben servir a los dos: trazables a los documentos y útiles en la operación diaria.

## Positioning

"Cada fecha, un solo evento." Las reglas críticas (tres salones como máximo, capacidad que no baja del mayor aforo agendado, sin traslapes, bitácora que no se altera) viven en la base de datos, no solo en la pantalla: se cumplen aunque el dato llegue por otra vía. Agenda, paquetes y control de anticipos están en un mismo lugar.

## Operating Context

- Un solo negocio por instalación; su nombre viene del `.env` (`NOMBRE_NEGOCIO`).
- Roles: gerente y cliente. El acceso se controla por rol en el servidor.
- El gerente crea las cuentas de cliente y entrega una clave inicial legible (sin caracteres que se confundan al dictarla); el cliente debe cambiarla en su primer ingreso.
- Los gerentes se dan de alta y se recuperan solo desde la consola (`administracion/admin.py`).
- Toda acción relevante queda en una bitácora inalterable.
- Documentos de referencia del curso: SRS v2.0, SDD v2.0 (wireframes IU-01 a IU-10 como contrato de construcción, Figuras 27 a 36), Plan de Proyecto, Correction Register y Traceability Record.

## Capabilities and Constraints

- **Sprint 1 (hecho):** acceso con bloqueo al quinto intento, cambio obligatorio de clave inicial, directorio y alta de clientes, edición de los tres salones, catálogo de platillos por categoría, paquetes estándar y personalizados (un personalizado pertenece a un cliente).
- **Sprint 2 (pendiente):** eventos, cotización, reservación, pagos, tablero con indicadores (HU-006) y portal real del cliente (HU-008).
- **Sprint 3 (pendiente):** reportes.
- Stack fijo: Python 3.11, Flask, HTML/CSS sin framework, JavaScript sin dependencias, PostgreSQL en Neon (nivel gratuito, conexiones limitadas). Despliegue de demostración en Render.
- CSP estricta: solo recursos propios, sin estilos ni scripts en línea.
- Idioma: español de México (`es-MX`), moneda MXN.
- Terminología del dominio: salón, platillo, paquete (estándar o personalizado), evento, cotización, anticipo, finiquito, aforo, clave inicial.

## Evidence on Hand

- Datos de semilla en `basedatos/03_semilla.sql`: tres salones, trece platillos y tres paquetes estándar.
- Trazabilidad requisito → código → prueba en `docs/trazabilidad_sprint1.md`; desviaciones respecto a los documentos en `docs/desviaciones_sprint1.md`.
- No hay testimonios, clientes reales con nombre, fotos del salón ni logotipo en el repositorio. No inventarlos.

## Product Principles

1. **La regla manda.** Si una regla de negocio puede romperse, se impide en la base y la pantalla explica el rechazo con los valores involucrados.
2. **Claro para quien no es técnico.** Mensajes en lenguaje cotidiano, sin códigos; un cliente que nunca usó el sistema debe entender qué pasó y qué hacer.
3. **Rápido en el celular, cómodo en la PC.** Cada pantalla del gerente sirve para consultar de pie y para capturar con calma.
4. **Trazable al documento.** Lo que se construye corresponde a un requisito y a un wireframe del SDD; si se desvía, se registra.
5. **Nada se pierde a la mitad.** Cada operación se guarda completa o no se guarda.

## Accessibility & Inclusion

- Utilizable desde 360 px sin desplazamiento horizontal (RNF-13).
- Áreas de toque de al menos 44 px, foco visible y respeto a la preferencia de movimiento reducido.
- Clientes con poca experiencia técnica: la clave inicial se puede dictar y se acepta escrita en minúsculas, con espacios o sin guion.
