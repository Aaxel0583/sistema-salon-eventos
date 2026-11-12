# Manual técnico

Sistema de Reservaciones y Gestión para Salón de Eventos · versión 1.0 (Release 3)

Para quien instala, opera y mantiene el sistema. La instalación paso a paso está en el `README.md` de la raíz; aquí se explica cómo está hecho y cómo se cuida.

## 1. Arquitectura

Aplicación web renderizada en el servidor, en capas (SDD §3). Cada capa solo conoce a la de abajo.

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Presentación (PKG-01) | `app/presentacion/` | Plantillas Jinja, una hoja de estilos y un archivo JavaScript sin dependencias |
| Rutas (PKG-02) | `app/rutas/` | Un *blueprint* por área. Reciben la petición, llaman a un servicio y eligen la respuesta |
| Servicios (PKG-03) | `app/servicios/` | Validan la captura, abren la transacción, registran la bitácora |
| Seguridad (PKG-04) | `app/seguridad/` | Cifrado de claves, sesión y decoradores por rol |
| Datos (PKG-05) | `app/datos/` | Pool de conexiones, repositorios y traducción de errores de la base |
| Dominio | `app/dominio/modelos.py` | Clases Usuario, Salon, Platillo, Paquete, Evento, Pago y las filas de los reportes |
| Base de datos (PKG-06) | `basedatos/` | Esquema, triggers, funciones, vistas y semilla |
| Consola (PKG-07) | `administracion/admin.py` | Alta y recuperación de gerentes |

**Decisión central (DA-01):** las reglas críticas viven en PostgreSQL, no en Python. La aplicación envía la operación y traduce el rechazo. Así la regla se cumple aunque el dato llegue por SQL directo.

Tecnología: Python 3.11, Flask 3.1, psycopg 3 con pool, PostgreSQL 16 (Neon), HTML5 y CSS3 sin framework. Versiones exactas en `requirements.txt`.

> El Plan de Proyecto compromete Oracle Database con PL/SQL. El desarrollo y las pruebas se hicieron sobre PostgreSQL (Neon) con PL/pgSQL. Antes de la entrega hay que formalizar el cambio con una *Change Request* o migrar los scripts 01 a 06.

## 2. Componentes y rutas

| Componente | Servicio | Rutas | Pantallas |
|---|---|---|---|
| C-01 Acceso | `servicio_acceso.py` | `/login` · `/logout` · `/clave` | IU-01, IU-02 |
| C-02 Clientes | `servicio_clientes.py` | `/clientes` · `/clientes/nuevo` · `/clientes/<id>/clave` | IU-04 |
| C-03 Catálogos | `servicio_catalogos.py` | `/salones` · `/platillos` · `/paquetes` | IU-05 |
| C-04 Reservación | `servicio_eventos.py::ServicioReservaciones` | `/eventos/nuevo` · `/api/agenda` | IU-06 |
| C-05 Control financiero | `servicio_pagos.py` | `/eventos/<id>/pagos` | IU-07 (panel de pagos) |
| C-06 Reportes | `servicio_reportes.py` | `/reportes/cartera` · `/reportes/activos` · `/reportes/realizados` (`?formato=csv`) | IU-08 |
| C-07 Portal del cliente | `servicio_portal.py` | `/mis-eventos` · `/mis-eventos/<clave>` | IU-09, IU-10 |
| C-08 Tablero | `servicio_eventos.py::ServicioEventos` | `/panel` · `/eventos` · `/eventos/<id>` · `/eventos/<id>/estado` | IU-03, IU-07 |
| C-09 Consola | `administracion/admin.py` | — | — |
| C-10 Acceso a datos | `app/datos/` | — | — |
| C-11 Reglas en la base | `basedatos/*.sql` | — | — |

Todas las rutas del gerente llevan `@solo_gerente` y las del cliente `@solo_cliente`: el rol se verifica en el servidor en cada petición.

## 3. Modelo de datos

Ocho tablas en tercera forma normal (script 01):

| Tabla | Contenido | Notas |
|---|---|---|
| `usuario` | Gerentes y clientes | Correo y celular únicos; al menos uno obligatorio; clave cifrada con sal |
| `salon` | Los tres espacios | Capacidad, renta y disponibilidad |
| `platillo` | Menú por categoría | |
| `paquete` · `paquete_platillo` | Banquete con precio por persona | Estándar o personalizado (con dueño) |
| `evento` | Cotización, reservación y su estado de cuenta | Clave `EVT-AAAA-NNNN`, costo, estatus, finiquito |
| `pago` | Abonos de un evento | Inalterables |
| `bitacora` | Operaciones sensibles | Inalterable |

El **saldo no se almacena**: se calcula en la vista `vw_evento_detalle` como costo menos pagos.

### Objetos de la base

| Id | Objeto | Script | Qué hace |
|---|---|---|---|
| IB-01 | `vw_evento_detalle` | 04 | Evento con cliente, salón, paquete, pagado y saldo. Base de las demás vistas |
| IB-02 | `trg_evento_aforo` | 05 | Rechaza con **BF001** el evento con más invitados que la capacidad |
| IB-03 | `trg_evento_disponibilidad` | 05 | Rechaza con **BF002** el traslape contra eventos confirmados o realizados |
| IB-04 | `trg_salon_limite` | 02 | Rechaza con **BF003** un cuarto salón |
| IB-05 | `trg_salon_capacidad` | 02 | Rechaza con **BF004** bajar la capacidad por debajo del mayor evento agendado |
| IB-06 | `fn_registrar_pago`, `trg_pago_saldo`, `trg_pago_finiquito` | 06 | Rechaza con **BF005** el abono mayor al saldo y marca el finiquito al llegar a cero |
| — | `trg_pago_inalterable`, `trg_evento_finiquito`, `trg_evento_costo_pagado` | 06 | Un abono no se edita ni se borra; el finiquito no se pone ni se quita a mano (**BF010**); el costo no baja de lo pagado |
| IB-07 | `trg_evento_clave`, `trg_evento_clave_inmutable` | 04 | Asigna la clave del evento (**BF008**) |
| — | `fn_cotizar`, `trg_evento_costo` | 04 | Costo = renta + precio por persona × invitados |
| IB-08 | `vw_cartera` | 06 | Cuentas con saldo y su semáforo a 21 días |
| IB-09 | `vw_proyectos_activos`, `vw_proyectos_realizados` | 06 | Reportes operativos |
| IB-10 | `vw_ocupacion_salon` | 04 | Medidor del tablero |
| IB-11 | `vw_pendientes_cierre` | 04 | Eventos vencidos sin cerrar |

Todos los scripts son re-ejecutables.

### Códigos de regla

| Código | Regla | Dónde se impone |
|---|---|---|
| BF001 | RN-01 aforo | Trigger |
| BF002 | RN-02 traslape | Trigger |
| BF003 | RN-03 tres salones | Trigger |
| BF004 | RN-04 reducción de capacidad | Trigger |
| BF005 | RN-05 pago mayor al saldo | Trigger |
| BF006, BF007 | RN-06 contacto obligatorio · RN-07 contacto único | Restricciones |
| BF008, BF009 | RN-08 clave del evento · RN-09 cotización | Trigger y función |
| BF0010 | RN-10 finiquito automático | Trigger (la base emite `BF010`: un SQLSTATE tiene cinco caracteres) |
| BF0011, BF0012 | RN-11 estatus válidos · RN-12 paquete personalizado | Restricciones |

`app/datos/errores.py` convierte cada código o restricción en el mensaje que ve el usuario.

## 4. Seguridad y privacidad

- **Claves:** derivadas con sal (`app/seguridad/claves.py`); nunca se guardan ni se registran en claro. La clave inicial se muestra una sola vez.
- **Sesión:** cookie firmada, `HttpOnly`, `SameSite=Lax` y `Secure` con `COOKIE_SEGURA=1`. Dura 8 horas. Si la clave cambia, las sesiones abiertas dejan de valer.
- **Bloqueo:** al quinto intento fallido.
- **CSRF:** todos los formularios llevan *token* (Flask-WTF).
- **Inyección SQL:** todas las consultas usan parámetros enlazados.
- **Cabeceras:** política de contenido que solo permite recursos propios, sin scripts ni estilos en línea; `X-Frame-Options: DENY`; páginas con sesión sin caché.
- **Aislamiento:** el portal del cliente filtra por el titular guardado en la sesión, nunca por un dato de la petición.
- **Archivo CSV:** un texto que empieza con `=`, `+`, `-` o `@` se entrega con apóstrofo para que la hoja de cálculo no lo ejecute como fórmula. Cada descarga queda en bitácora.
- **Datos personales (LFPDPPP):** el sistema guarda nombre, correo y celular de los clientes. El salón debe poner a su disposición un **aviso de privacidad**; el sistema no lo incluye. Los datos residen en el proveedor de la base (Neon): hay que mencionarlo en el aviso.

## 5. Configuración

Todo lo que cambia entre instalaciones está en `.env` (nunca se sube al repositorio):

| Variable | Uso |
|---|---|
| `NOMBRE_NEGOCIO` | Nombre que aparece en la barra y en los títulos |
| `DATABASE_URL` | Cadena de conexión, con `?sslmode=require` |
| `SECRET_KEY` | Llave de firma de la sesión (64 caracteres hexadecimales) |
| `COOKIE_SEGURA` | `1` en producción con HTTPS |
| `POOL_MIN`, `POOL_MAX` | Tamaño del pool; en el nivel gratuito de Neon, 1 y 5 |
| `TEST_DATABASE_URL` | Solo para pruebas; esa base se borra en cada corrida |

La aplicación trabaja en la zona horaria `America/Mexico_City`: «hoy», el semáforo y las fechas de finiquito se calculan con esa hora.

## 6. Operación

**Gerentes** (no se crean desde la web):

```bash
python -m administracion.admin crear-gerente --nombre "Nombre" --correo gerente@salon.mx
python -m administracion.admin regenerar-clave --usuario gerente@salon.mx
python -m administracion.admin desbloquear --usuario 4921234567
```

**Actualizar una instalación** que ya tiene datos: ejecutar solo los scripts nuevos, nunca `--reiniciar`.

```bash
git pull
pip install -r requirements.txt
python -m basedatos.instalar --solo 06_finanzas_sprint3.sql
```

**Despliegue en Render:** *build* `pip install -r requirements.txt`, *start* `gunicorn wsgi:app`, variables del apartado 5 más `PYTHON_VERSION=3.11.9`.

## 7. Respaldo y restauración (RNF-16)

Neon conserva el historial de la base y permite restaurarla a un punto anterior desde su consola (*Branches → Restore*). El periodo que conserva depende del plan contratado: **verifícalo en la consola y haz una prueba de restauración antes de la entrega.**

Respaldo manual, recomendado antes de cada actualización (Plan §19):

```bash
pg_dump "$DATABASE_URL" --no-owner --format=custom --file=respaldo_$(date +%F).dump
# Restaurar en una base vacía:
pg_restore --no-owner --dbname="$URL_DESTINO" respaldo_2026-11-20.dump
```

## 8. Pruebas

```bash
pytest -v                      # 223 pruebas; las de integración necesitan TEST_DATABASE_URL
pytest tests/test_pagos.py -v  # un módulo
```

Resultado de la regresión y matriz de casos: `docs/registro_pruebas.md`.

## 9. Solución de problemas

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| «Falta la variable … en el archivo .env» | `.env` no existe o está incompleto | Copiar `.env.example` y llenarlo |
| «No fue posible comunicarse con la base de datos» al primer clic del día | Neon suspendió la instancia por inactividad | Reintentar: la conexión se restablece sola en unos segundos |
| `getaddrinfo failed` al correr pruebas | Host mal escrito en `TEST_DATABASE_URL` | Revisar la cadena |
| «La página expiró» | El formulario estuvo abierto más que la sesión | Recargar la página |
| El gerente no puede entrar | Cuenta bloqueada | `administracion.admin desbloquear` |
| Un abono se capturó mal | Los abonos son inalterables | Ver el procedimiento siguiente |

**Corregir un abono mal capturado.** No hay pantalla para hacerlo (límite conocido, `desviaciones_sprint3.md`). Solo el administrador de la base, con respaldo previo y dejando constancia:

```sql
BEGIN;
ALTER TABLE pago   DISABLE TRIGGER trg_pago_inalterable;
ALTER TABLE evento DISABLE TRIGGER trg_evento_finiquito;
DELETE FROM pago WHERE id_pago = <id>;
UPDATE evento SET finiquitado = 'N', fecha_finiquito = NULL WHERE id_evento = <id_evento>;
INSERT INTO bitacora (accion, entidad) VALUES ('CORRECCION_PAGO', 'evento:<id_evento>:pago:<id>');
ALTER TABLE evento ENABLE TRIGGER trg_evento_finiquito;
ALTER TABLE pago   ENABLE TRIGGER trg_pago_inalterable;
COMMIT;
```

Después se vuelve a registrar el abono correcto desde la ficha del evento.

## 10. Mantenimiento y soporte

El Plan §19 no establece un acuerdo formal de mantenimiento: el equipo acompaña la presentación final y resuelve dudas del cierre. Para evolucionar el sistema, cada cambio entra por *Change Request* (Plan §11), en una rama `feature/HU-xxx` que se fusiona a `develop` con revisión de otro desarrollador.
