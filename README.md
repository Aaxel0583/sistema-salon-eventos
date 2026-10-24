# Sistema de Reservaciones y Gestión para Salón de Eventos

Aplicación web para cotizar, reservar y cobrar eventos en un salón con tres espacios. Python 3.11 + Flask, HTML5/CSS3 sin framework y PostgreSQL con las reglas críticas en PL/pgSQL (SRS v2.0 §4.5, SDD v2.0).

**Estado: Sprint 1 (Release 1 · Núcleo y Catálogos)** — HU-001 Autenticación, HU-002 Alta de clientes, HU-003 Salones, HU-004 Platillos y paquetes.

---

## 1. Requisitos previos

| Herramienta | Versión | Para qué |
|---|---|---|
| Python | 3.11 (RD-01) | Ejecutar la aplicación |
| Git | cualquiera reciente | Control de versiones (Plan §11) |
| Cuenta en Neon | nivel gratuito (RD-05) | PostgreSQL administrado con respaldo |
| VS Code | — | Editor acordado en el Plan §17 |
| psql | opcional | Ejecutar scripts SQL a mano |

## 2. Repositorio y modelo de ramas (Plan de Proyecto §11)

```bash
git init
git add .
git commit -m "chore: estructura base del Sprint 1"
git branch -M main
git checkout -b develop
git remote add origin https://github.com/<organizacion>/sistema-salon-eventos.git
git push -u origin main develop
```

Una rama por Historia de Usuario, que se fusiona a `develop` por *pull request* revisado por el otro desarrollador (quien escribe no revisa):

```bash
git checkout develop
git checkout -b feature/HU-001
# ... trabajo ...
git commit -m "feat(HU-001): bloqueo al quinto intento fallido (RF-03)"
git push -u origin feature/HU-001
```

Protege `main` y `develop` en GitHub (Settings → Branches → Require a pull request).
Al cerrar el sprint: `develop` → `main` y etiqueta `git tag -a v1.0-sprint1 -m "Release 1"`.

## 3. Base de datos en Neon

1. Entra a <https://console.neon.tech> y crea un proyecto (región más cercana, PostgreSQL 16 o superior).
2. Crea la base `salon` (o usa `neondb`).
3. En **Connection string** copia la cadena **directa** (el host *sin* `-pooler`). La aplicación ya trae su propio pool de conexiones; usar además el pooler de Neon no aporta y puede chocar con sentencias preparadas.
4. La cadena debe terminar en `?sslmode=require` (IE-01: conexión cifrada).
5. Crea una segunda rama de Neon llamada `pruebas` (Branches → New branch). Ahí corren las pruebas automáticas sin tocar los datos reales.

## 4. Entorno virtual y dependencias

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## 5. Archivo de configuración (DA-06, RNF-07)

```bash
cp .env.example .env          # en Windows: copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # pega el resultado en SECRET_KEY
```

Llena `DATABASE_URL` con la cadena de Neon y `NOMBRE_NEGOCIO` con el nombre del salón. **`.env` nunca se sube al repositorio** (ya está en `.gitignore`).

## 6. Instalar el esquema

Opción A, con Python (funciona igual en Windows):

```bash
python -m basedatos.instalar
```

Opción B, con psql o pegando cada archivo en el *SQL Editor* de Neon, **en este orden**:

```
basedatos/01_esquema.sql         tablas, llaves y restricciones (RN-06, RN-07, RN-11, RN-12)
basedatos/02_reglas_sprint1.sql  triggers BF003, BF004 y bitácora inalterable
basedatos/03_semilla.sql         3 salones, 13 platillos y 3 paquetes estándar
```

`00_limpiar.sql` borra todo; úsalo solo en desarrollo (`python -m basedatos.instalar --reiniciar`).

## 7. Crear el primer gerente (C-09)

Los gerentes no se crean desde la web ni con SQL, para que la clave se derive con sal (RNF-04):

```bash
python -m administracion.admin crear-gerente --nombre "Nombre del gerente" --correo gerente@salon.mx
```

Imprime una clave inicial; en el primer ingreso el sistema obliga a cambiarla (RF-04). La misma utilidad recupera el acceso si un gerente queda bloqueado:

```bash
python -m administracion.admin desbloquear --usuario gerente@salon.mx
```

## 8. Ejecutar

```bash
flask --app wsgi run --debug
```

Abre <http://127.0.0.1:5000>.

## 9. Pruebas

En `.env` agrega `TEST_DATABASE_URL` con la cadena de la rama `pruebas` de Neon (o un PostgreSQL local). **Las pruebas borran y reinstalan esa base.**

```bash
pytest -v
```

Sin `TEST_DATABASE_URL` solo corren las unitarias; las de integración se marcan como omitidas.

| Archivo | Qué verifica |
|---|---|
| `tests/test_unitarias.py` | Generador de clave dictable (RNF-14), cifrado con sal (RNF-04), normalización de correo y celular (RF-01, RN-07) |
| `tests/test_reglas_bd.py` | Reglas por SQL directo, sin la aplicación: CP-04, CP-05, CP-06, RN-06, RN-07, RNF-18 |
| `tests/test_flujos.py` | Flujos web completos: CP-01, CP-02, CP-03, CP-21, CP-22, CP-25 y RF-05 |

## 10. Estructura y correspondencia con el SDD

```
app/
├── presentacion/          PKG-01  plantillas, CSS y JS (IU-01 a IU-05)
├── rutas/                 PKG-02  controladores por área (Anexo A del SDD)
├── servicios/             PKG-03  reglas de aplicación (C-01, C-02, C-03)
├── seguridad/             PKG-04  cifrado, sesión, decoradores por rol
├── datos/                 PKG-05  C-10: pool, transacciones, repositorios, traducción de errores
├── dominio/               Figura 3: clases Usuario, Salon, Platillo, Paquete
└── config.py              DA-06: lectura del .env
basedatos/                 PKG-06  C-11: esquema, triggers y semilla
administracion/            PKG-07  C-09: utilidad de consola
tests/                     Casos de prueba del SRS, Anexo C
docs/                      Desviaciones y trazabilidad del sprint
wsgi.py                    Punto de entrada (Flask / Gunicorn)
```

## 11. Despliegue de demostración en Render (opcional)

| Campo | Valor |
|---|---|
| Build command | `pip install -r requirements.txt` |
| Start command | `gunicorn wsgi:app` |
| Variables | `DATABASE_URL`, `SECRET_KEY`, `NOMBRE_NEGOCIO`, `COOKIE_SEGURA=1`, `PYTHON_VERSION=3.11.9` |
