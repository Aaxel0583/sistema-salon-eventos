# Desviaciones del Sprint 1 respecto a la línea base

Durante la construcción se detectaron diferencias entre el código y los documentos aprobados (SDD v2.0, Plan de Proyecto v2.0). Conforme al Plan §11 (control de cambios) e ISO/IEC 29110 (PM: *Change Request* y *Correction Register*), cada una debe registrarse antes del cierre del sprint y reflejarse en la siguiente versión del SDD (v2.1).

| # | Documento y apartado | Lo que dice la línea base | Lo que hace el código | Justificación | Acción sugerida |
|---|---|---|---|---|---|
| D-01 | SDD §4.2, tabla PAQUETE | Sin campo de nombre | `nombre VARCHAR(80) NOT NULL` | Sin nombre el gerente no distingue un paquete de otro en IU-05 ni al cotizar en IU-06 | CRQ · agregar el campo al modelo de datos y al diagrama de clases |
| D-02 | SDD §4.2, tabla SALON | Sin descripción | `descripcion VARCHAR(255)` | RF-14 exige editar la descripción del salón | Correction Register · el SRS ya lo pedía; el SDD lo omitió |
| D-03 | SDD §4.2, tabla EVENTO | Sin nombre del evento | `nombre_evento VARCHAR(120)` | RF-28 pide buscar por "nombre del evento" | Correction Register · mismo caso que D-02 |
| D-04 | Plan §9.1, Sprint 2 | "Crear las tablas de eventos y de pagos" en el Sprint 2 | Se crean en el Sprint 1 (`01_esquema.sql`) | El trigger BF004 (HU-003, Sprint 1) consulta EVENTO; sin la tabla no puede existir | CRQ · mover la tarea al Sprint 1; los triggers de EVENTO siguen en el Sprint 2 |
| D-05 | SDD §3.1, vista de paquetes | Siete paquetes, sin uno de dominio | Paquete `app/dominio` con las clases de la Figura 3 | Las clases del dominio no son de presentación, rutas ni datos; las comparten servicios y repositorios | CRQ · agregar el paquete a la Figura 1 o declararlo parte de PKG-03 |
| D-06 | SDD Anexo A, /logout | Métodos GET, POST | Solo POST con token CSRF | Un cierre de sesión por GET puede dispararlo otra página sin que el usuario lo pida | Correction Register |
| D-07 | SDD §4.2, BITACORA (RNF-18) | "Sin operación de borrado en la interfaz" | Además, trigger que rechaza UPDATE y DELETE en la base | Refuerza la regla con el mismo criterio de DA-01 | Registrar como mejora; sin cambio de alcance |
| D-08 | SRS RN-04 | "Mayor número de asistentes de los eventos ya agendados" | Cuenta solo eventos en COTIZACION o CONFIRMADO con fecha de hoy en adelante | Un evento cancelado no ocupa el salón (RN-02) y uno pasado ya no depende de la capacidad actual | Validar con el cliente y precisar la redacción de RN-04 |
| D-09 | Cronograma / Plan Anexo A | Sprint 1 del 9 al 22 de octubre | Construcción iniciada después de esa ventana | — | Progress Status Record · registrar la variación y el plan de recuperación |
