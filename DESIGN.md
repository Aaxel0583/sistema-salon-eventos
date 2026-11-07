---
name: Sistema de Reservaciones · Salón de Eventos
description: Agenda de salones, paquetes de banquete y control de anticipos en un mismo lugar.
colors:
  marino-de-gala: "#1f3864"
  azul-invitacion: "#2b70af"
  azul-invitacion-hondo: "#255f95"
  azul-borde: "#9eb6dd"
  azul-claro: "#d9e2f3"
  azul-seleccion: "#edf3fb"
  panel: "#f2f5fa"
  panel-suave: "#f7fafd"
  fondo: "#ffffff"
  tinta: "#1d2533"
  tinta-suave: "#555e6e"
  tinta-etiqueta: "#444c5a"
  control-borde: "#8090aa"
  control-borde-hover: "#5f6f8a"
  verde: "#3d7a28"
  verde-fondo: "#e5efdf"
  verde-hondo: "#2f6320"
  ambar: "#b8860b"
  ambar-fondo: "#fdf2dc"
  ambar-borde: "#d4a017"
  ambar-texto: "#8a6400"
  ambar-hondo: "#6e5200"
  rojo: "#c00000"
  rojo-fondo: "#fbeaea"
  rojo-borde: "#d06060"
  rojo-hondo: "#990000"
  gris: "#6b7280"
  gris-fondo: "#eceff3"
  gris-borde: "#d1d5db"
  foco: "#7fa7d6"
  lema-suave: "#cfdaee"
  linea-datos: "#cfd9e8"
  velo-modal: "rgba(16, 28, 52, .45)"
typography:
  display:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "clamp(1.7rem, 4vw, 2.4rem)"
    fontWeight: 700
    lineHeight: 1.2
  headline:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.6rem"
    fontWeight: 700
    lineHeight: 1.25
  title:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 700
    lineHeight: 1.25
  body:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 600
    lineHeight: 1.5
  cifra:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.1rem"
    fontWeight: 700
    lineHeight: 1.25
    fontFeature: "tnum"
  precio:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.4rem"
    fontWeight: 700
    lineHeight: 1.25
    fontFeature: "tnum"
  clave:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "0.12em"
    fontFeature: "tnum"
  etiqueta:
    fontFamily: "Segoe UI, system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  control: "6px"
  panel: "10px"
  pill: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "1rem"
  lg: "1.25rem"
  xl: "1.5rem"
components:
  button-primary:
    backgroundColor: "{colors.azul-invitacion}"
    textColor: "{colors.fondo}"
    rounded: "{rounded.control}"
    padding: "0.5rem 1.1rem"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.azul-invitacion-hondo}"
  button-secondary:
    backgroundColor: "{colors.fondo}"
    textColor: "{colors.azul-invitacion}"
    rounded: "{rounded.control}"
    padding: "0.5rem 1.1rem"
    height: "44px"
  button-secondary-hover:
    backgroundColor: "{colors.azul-seleccion}"
  button-danger:
    backgroundColor: "{colors.fondo}"
    textColor: "{colors.rojo}"
    rounded: "{rounded.control}"
  button-danger-hover:
    backgroundColor: "{colors.rojo-fondo}"
  button-disabled:
    backgroundColor: "{colors.gris-fondo}"
    textColor: "{colors.gris}"
  input:
    backgroundColor: "{colors.fondo}"
    textColor: "{colors.tinta}"
    rounded: "{rounded.control}"
    padding: "0.55rem 0.75rem"
    height: "44px"
  panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.panel}"
    padding: "1.25rem"
  nav-bar:
    backgroundColor: "{colors.marino-de-gala}"
    textColor: "{colors.fondo}"
  table-header:
    backgroundColor: "{colors.azul-claro}"
    textColor: "{colors.marino-de-gala}"
  tag:
    rounded: "{rounded.pill}"
    padding: "0.1rem 0.55rem"
    typography: "{typography.etiqueta}"
  tag-marino:
    backgroundColor: "{colors.azul-claro}"
    textColor: "{colors.marino-de-gala}"
    rounded: "{rounded.pill}"
---

# Design System: Sistema de Reservaciones · Salón de Eventos

## Overview

**Creative North Star: "La Agenda del Salón"**

Ordenada y confiable como la libreta del gerente: todo tiene su lugar y nada se encima. La interfaz es una herramienta de trabajo para alguien que captura con calma en la PC y consulta de pie en el celular, y para clientes que quizá nunca han usado un sistema así. Por eso el sistema se apoya en patrones conocidos, en un solo azul de acción y en una tinta marino que da formalidad sin ceremonia.

La densidad es media: paneles con aire, tablas legibles y controles de 44 px que sirven igual con el dedo que con el mouse. La personalidad vive en los detalles precisos (cifras tabulares, bordes que se afinan al pasar el cursor, una sombra que apenas despega lo que se puede tocar), no en ornamentos. Los colores de estado (verde, ámbar, rojo) son convenciones del SDD, Anexo C: rojo con barra lateral para un rechazo, ámbar con borde para una advertencia, gris para lo no disponible.

**Key Characteristics:**
- Un solo azul de acción sobre fondos blancos y paneles azul hielo.
- Barra superior marino con el nombre del negocio en mayúsculas.
- Componentes sobrios y precisos: planos en reposo, respuesta leve al cursor.
- Pensada desde 360 px; nada provoca desplazamiento horizontal.
- Movimiento corto (150–220 ms); con "reducir movimiento" se quitan desplazamientos y escalas, pero se quedan los fundidos.

## Colors

Una paleta fría y contenida: marino para la estructura, un azul para actuar y tres colores de estado que solo aparecen cuando dicen algo.

### Primary
- **Azul Invitación** (#2b70af): botones principales, enlaces de acción (también los conteos del panel), la barra de la pestaña activa y el contorno de foco. Pasa 4.5:1 sobre los paneles azul hielo. Al pasar el cursor se oscurece a **Azul Invitación Hondo** (#255f95).

### Secondary
- **Marino de Gala** (#1f3864): barra superior, títulos (h1, h2), encabezados de tabla y precios. Da el tono formal del salón.

### Neutral
- **Blanco** (#ffffff): fondo de la página, campos y botones secundarios.
- **Panel Azul Hielo** (#f2f5fa) y **Panel Suave** (#f7fafd): fondo de paneles, tarjetas, filas de tabla y avisos informativos.
- **Azul Borde** (#9eb6dd): contorno de paneles, tarjetas, tablas y pestañas.
- **Azul Claro** (#d9e2f3): encabezado de tablas.
- **Azul Selección** (#edf3fb): hover de botones secundarios y pestañas; fondo del segmento elegido.
- **Tinta** (#1d2533), **Tinta Suave** (#555e6e) y **Tinta Etiqueta** (#444c5a): texto principal, texto secundario y etiquetas de formulario.
- **Borde de Control** (#8090aa, 3.2:1 sobre blanco), que pasa a #5f6f8a al pasar el cursor: contorno de campos y segmentos.
- **Foco**: contorno de 3px en Azul Invitación sobre fondos claros (4.8:1); dentro de la barra marino se usa #7fa7d6 (4.65:1).
- **Línea de Datos** (#cfd9e8) y **Borde Deshabilitado** (#d1d5db): separador punteado de las fichas de salón y borde de botones no disponibles.
- **Lema Suave** (#cfdaee): texto secundario sobre el marino de la pantalla de acceso.
- **Velo de Modal** (rgba(16, 28, 52, .45)): fondo detrás del diálogo de confirmación.

### Estados
- **Verde** (#3d7a28 sobre #e5efdf): éxito, cuenta activa, condición de clave cumplida, clave generada; el título de la clave generada usa **Verde Hondo** (#2f6320, 6.1:1).
- **Ámbar** (#b8860b sobre #fdf2dc, borde #d4a017): advertencias. Como texto se usa **Ámbar Texto** (#8a6400, 5.4:1 sobre blanco) o **Ámbar Hondo** (#6e5200) sobre fondos verdes; el ámbar base nunca va como texto.
- **Rojo** (#c00000 sobre #fbeaea): rechazo de una regla, cuenta bloqueada, acción de eliminar. Borde de los botones de peligro en **Rojo Borde** (#d06060); hover del botón lleno en **Rojo Hondo** (#990000).
- **Gris** (#6b7280 sobre #eceff3): acción no disponible, salón no disponible.

### Named Rules
**The Un Solo Azul Rule.** Azul Invitación es el único color que invita a actuar. Si algo es azul, se puede tocar; si no se puede tocar, no es azul.

**The El Color Dice Algo Rule.** Verde, ámbar y rojo solo aparecen para comunicar un estado o un resultado, nunca como decoración.

## Typography

**Body Font:** Segoe UI (con system-ui, -apple-system, Roboto, Helvetica Neue, Arial, sans-serif)

**Character:** Una sola familia del sistema operativo, en dos pesos (400 y 600/700). Se siente nativa en Windows y en el celular, carga al instante y no compite con el contenido.

### Hierarchy
- **Display** (700, clamp(1.7rem, 4vw, 2.4rem), 1.2): solo el lema de la pantalla de acceso.
- **Headline** (700, 1.6rem, 1.25): título de cada pantalla, en Marino de Gala.
- **Title** (700, 1.1rem, 1.25): títulos de panel y de tarjeta.
- **Body** (400, 1rem, 1.5): texto general, campos y celdas.
- **Label** (600, 0.9rem): etiquetas de formulario, encabezados de tabla, notas y texto auxiliar.
- **Etiqueta** (600, 0.8rem): píldoras de estado.
- **Cifra** (700, 1.1rem, números tabulares): conteos del panel.
- **Precio** (700, 1.4rem, números tabulares): precio por persona en las tarjetas de paquete.
- **Clave** (700, 1.35rem, espaciado 0.12em, números tabulares): la clave generada, agrupada para dictarse.

### Named Rules
**The Cifras Alineadas Rule.** Todo número que se compara (conteos, precios, teléfonos, claves generadas) usa números tabulares para que las columnas no bailen.

## Layout

Contenido centrado con un ancho máximo de 1120px y márgenes laterales de 1rem. La página se arma con paneles apilados y rejillas que se acomodan solas: salones en `repeat(auto-fit, minmax(280px, 1fr))`, y dos columnas a partir de 860px. La pantalla de acceso se parte en 44% marca y 56% formulario desde 820px.

El ritmo usa pasos de 0.25, 0.5, 0.75, 1, 1.25 y 1.5rem; entre paneles va 1rem y dentro de un panel 1.25rem. En cada pantalla de catálogo las pestañas van arriba y el título de la pantalla debajo. Por debajo de 640px las pestañas se reparten el ancho y la tabla de clientes se vuelve una tarjeta por fila (nombre y estado arriba, la acción siempre visible). Ninguna página se desplaza a los lados (RNF-13, 360px).

## Elevation & Depth

Híbrido sobrio: la profundidad la dan sobre todo los fondos azul hielo y los bordes; las sombras son leves y sirven para ordenar, no para decorar. Lo que se puede tocar se despega un poco al pasar el cursor; lo que flota (menú del usuario, modal) lleva la sombra más marcada.

### Shadow Vocabulary
- **Reposo** (`box-shadow: 0 1px 2px rgba(31,56,100,.06), 0 1px 3px rgba(31,56,100,.05)`): paneles, tablas y botón principal.
- **Elevado** (`box-shadow: 0 4px 12px rgba(31,56,100,.12), 0 1px 3px rgba(31,56,100,.08)`): hover del botón principal; menú del usuario.
- **Modal** (`box-shadow: 0 12px 32px rgba(31,56,100,.25)`): solo el diálogo de confirmación, sobre un fondo marino al 45%.

### Named Rules
**The Sombra Que Responde Rule.** Las superficies descansan con la sombra de reposo; solo suben a la sombra elevada como respuesta al cursor o porque flotan sobre la página.

## Shapes

Esquinas suavemente redondeadas en dos tamaños: 6px para controles (botones, campos, segmentos, pestañas, avisos) y 10px para contenedores (paneles, tarjetas, tablas, menú, modal). Las etiquetas de estado son píldoras (999px). Los bordes son de 1px; el énfasis se hace con color o con un anillo interior, nunca engrosando el borde, para que nada se mueva al seleccionar. Los avisos llevan una barra lateral de 6px del color de su estado.

## Components

### Buttons
Sobrios y precisos: planos, con una respuesta corta y clara.
- **Shape:** esquinas suaves (6px), alto mínimo de 44px (36px en la variante pequeña con mouse; 44px en pantallas táctiles).
- **Primary:** fondo Azul Invitación, texto blanco, peso 600, sombra de reposo.
- **Hover / Focus:** el principal se oscurece a Azul Invitación Hondo y sube a la sombra elevada; el secundario toma fondo Azul Selección. Al presionar, todos se encogen a 97%. El foco es un contorno de 3px separado 2px, en Azul Invitación (en la barra, #7fa7d6).
- **Secondary:** fondo blanco, texto y borde Azul Invitación.
- **Danger:** texto rojo con borde #d06060 (3.8:1); hover con fondo rojo claro. Se usa también para «Clave nueva», porque corta el acceso de un cliente.
- **Danger lleno:** fondo rojo con texto blanco (6.5:1); solo para el botón que confirma una acción irreversible en el modal.
- **Disabled:** fondo y texto grises, sin sombra, cursor de no permitido.
- **Link action:** acción con forma de enlace, 44px de alto, cuyo subrayado aparece al pasar el cursor.

### Chips
- **Style:** píldora de 0.8rem en peso 600 con fondo claro y texto del mismo estado (verde, ámbar, rojo o gris).
- **State:** solo informan; no son botones. «Estándar» y «No disponible» en gris, «Personalizado» en marino sobre azul claro (no en ámbar: el ámbar es advertencia).

### Cards / Containers
- **Corner Style:** 10px.
- **Background:** Panel Azul Hielo, o Panel Suave en formularios largos.
- **Shadow Strategy:** sombra de reposo; las tarjetas no suben al pasar el cursor porque no son tocables por sí mismas.
- **Border:** 1px Azul Borde.
- **Internal Padding:** 1.25rem.

### Inputs / Fields
- **Style:** fondo blanco, borde 1px Borde de Control, 6px, 44px de alto.
- **Focus:** el borde cambia a Azul Invitación y aparece el contorno de foco.
- **Hover:** el borde se oscurece a #5f6f8a.
- **Segmentos:** selector de dos opciones con forma de botón; el elegido toma fondo Azul Selección, texto azul y un anillo interior de 1px.

### Navigation
- **Barra:** fondo Marino de Gala; el nombre del negocio va a la izquierda, en mayúsculas y peso 700.
- **Enlaces:** texto #d6e0f0, 44px de alto; hover con velo blanco al 8%; la página actual con velo al 15% y texto blanco.
- **Menú del usuario:** nombre con una flecha dibujada que gira al abrir; lista flotante blanca de 10px con sombra elevada y opciones de 44px.
- **Pestañas de catálogo:** botones de 44px con borde Azul Borde; la activa queda en blanco con texto marino y una barra azul de 3px abajo, para no competir con el botón principal de la pantalla.

### Hoja de agenda
El motivo visual de "La Agenda del Salón": una hoja de calendario junto al título del panel, con el mes en una franja marino, el día en grande y el día de la semana. La fecha sale de la base, en la zona horaria del salón. Se reserva para fechas reales; no se decora con ella.

### Panel
Empieza por **Pendientes** (clientes bloqueados, salones no disponibles), cada uno con su acción. Los conteos van en una sola línea bajo el título, como enlaces discretos. La actividad no muestra inicios de sesión.

### Armador de paquetes
Resumen vivo arriba de los platillos («2 platillos · $280.00 por persona»), fijo al desplazarse en escritorio. Con más de 8 clientes aparece un buscador que filtra la lista.

### Tablas
Encabezado Azul Claro con texto Marino de Gala; filas Panel Suave separadas por líneas #e3e9f2 que se aclaran a blanco al pasar el cursor.

### Avisos
Banda de 6px a la izquierda del color de su estado sobre su fondo claro. Entran con un desplazamiento de 6px en 220ms.

### Clave generada
Va primero en la pantalla, en un bloque verde con borde de 2px. Muestra la clave en el estilo Clave, con qué dato entra el cliente y el aviso en Ámbar Hondo de que no volverá a mostrarse. Tiene «Copiar mensaje para el cliente» y «Ya la entregué»; mientras no se confirme, el navegador advierte antes de salir.

### Modal de confirmación
Diálogo nativo de hasta 420px, con 10px de esquinas y sombra de modal. Entra y sale con opacidad y un desplazamiento de 8px en 180ms. El foco empieza en "Cancelar". Cada acción trae su propio título («¿Eliminar «Paquete Clásico»?»), su consecuencia en una frase y su verbo en el botón Danger lleno («Eliminar paquete», «Generar clave nueva»); nunca un «Continuar» genérico.

## Do's and Don'ts

### Do:
- **Do** mantener todo lo que se toca en 44px de alto o más.
- **Do** usar Azul Invitación solo para lo que se puede tocar y Marino de Gala para la estructura y los títulos.
- **Do** marcar la selección con color o un anillo interior (`inset 0 0 0 1px`), sin cambiar el grosor del borde.
- **Do** usar números tabulares en cifras, precios y claves.
- **Do** mantener las transiciones entre 150 y 220ms con `cubic-bezier(.2, 0, 0, 1)` y, con `prefers-reduced-motion`, quitar solo el movimiento (desplazar, escalar, girar) y conservar fundidos y cambios de color.
- **Do** probar cada pantalla a 360px sin desplazamiento horizontal.
- **Do** dar contexto oculto a las acciones repetidas («Editar<span class="solo-lector"> Crema de elote</span>») y poner los estados en texto, no solo en un símbolo o un color.

### Don't:
- **Don't** agregar un segundo color de acción ni usar verde, ámbar o rojo como decoración.
- **Don't** cargar fuentes, estilos o scripts externos ni en línea: la CSP solo permite recursos propios.
- **Don't** usar `window.confirm` ni `alert`; las confirmaciones van en el modal de la página, con título y verbo propios.
- **Don't** marcar un estado bajando la opacidad del texto; se usa una etiqueta («No disponible»).
- **Don't** subir la sombra de una superficie que no se puede tocar ni flota.
- **Don't** inventar logotipos, fotos del salón ni testimonios.
- **Don't** usar caracteres (○, ✓, +, ▾) como íconos; los marcadores se dibujan con CSS.
