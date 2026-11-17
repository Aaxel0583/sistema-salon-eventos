/* =====================================================================
   PKG-01 Presentación · JavaScript de apoyo (sin dependencias)
   Ninguna regla de negocio vive aquí: todo se valida otra vez en el
   servidor y en la base. Este archivo solo mejora la captura.
   ===================================================================== */
"use strict";

document.addEventListener("DOMContentLoaded", () => {
  // Mostrar u ocultar la clave mientras se escribe.
  document.querySelectorAll("[data-mostrar-clave]").forEach((boton) => {
    const campo = document.getElementById(boton.dataset.mostrarClave);
    if (!campo) return;
    boton.addEventListener("click", () => {
      const visible = campo.type === "text";
      campo.type = visible ? "password" : "text";
      boton.textContent = visible ? "Mostrar" : "Ocultar";
      boton.setAttribute("aria-pressed", String(!visible));
    });
  });

  // Confirmación antes de acciones irreversibles (regenerar clave, eliminar, cerrar un evento).
  // Escape o "Cancelar" cierran sin enviar; el foco inicia en "Cancelar".
  // Cada formulario trae su título (data-titulo), su consecuencia (data-confirmar) y su verbo (data-verbo).
  // Si la acción depende de una lista (p. ej. el estatus del evento), la lista lleva
  // data-confirmar-segun y cada <option> trae sus propios textos.
  // data-tono="primario" pinta el verbo en azul; sin él es rojo, porque DESIGN.md reserva
  // el rojo lleno para lo destructivo (eliminar, cortar un acceso, cancelar).
  // data-volver cambia el texto de "Cancelar" cuando chocaría con el verbo («Cancelar evento»).
  const dialogo = document.getElementById("dialogo-confirmar");
  const verbo = dialogo.querySelector("[data-verbo]");
  const volver = dialogo.querySelector('button[value="no"]');
  document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
      evento.preventDefault();
      const lista = formulario.querySelector("select[data-confirmar-segun]");
      const fuente = lista?.selectedOptions[0]?.dataset.verbo ? lista.selectedOptions[0] : formulario;
      dialogo.querySelector("[data-titulo]").textContent = fuente.dataset.titulo || "¿Confirmas la acción?";
      dialogo.querySelector("[data-mensaje]").textContent = fuente.dataset.confirmar || formulario.dataset.confirmar;
      verbo.textContent = fuente.dataset.verbo || "Continuar";
      volver.textContent = fuente.dataset.volver || "Cancelar";
      const azul = fuente.dataset.tono === "primario";
      verbo.classList.toggle("boton--primario", azul);
      verbo.classList.toggle("boton--peligro-lleno", !azul);
      dialogo.returnValue = "";
      dialogo.addEventListener("close", () => {
        if (dialogo.returnValue === "si") formulario.submit();
      }, { once: true });
      dialogo.showModal();
    });
  });

  // RF-08: la clave generada se muestra una sola vez. Copiar el mensaje listo para
  // enviar y avisar antes de salir mientras no se confirme la entrega.
  const bloqueClave = document.querySelector("[data-clave-generada]");
  if (bloqueClave) {
    const copiar = bloqueClave.querySelector("[data-copiar-clave]");
    const entregada = bloqueClave.querySelector("[data-clave-entregada]");
    const avisarAlSalir = (evento) => evento.preventDefault();
    window.addEventListener("beforeunload", avisarAlSalir);
    if (navigator.clipboard) {
      copiar.hidden = false;
      copiar.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(bloqueClave.dataset.mensaje);
          copiar.textContent = "Mensaje copiado";
        } catch {
          copiar.textContent = "No se pudo copiar; díctala";
        }
      });
    }
    entregada.hidden = false;
    entregada.addEventListener("click", () => {
      window.removeEventListener("beforeunload", avisarAlSalir);
      bloqueClave.remove();
      document.getElementById("q")?.focus();
    });
  }

  // IU-02 (Figura 28): las tres condiciones de la clave nueva se marcan al escribir.
  const formClave = document.querySelector("[data-validar-clave]");
  if (formClave) {
    const actual = formClave.querySelector("#current-password");
    const nueva = formClave.querySelector("#new-password");
    const confirmacion = formClave.querySelector("#confirmacion");
    const reglas = {
      largo: () => nueva.value.length >= 8,
      distinta: () => nueva.value !== "" && nueva.value !== actual.value,
      coincide: () => nueva.value !== "" && nueva.value === confirmacion.value,
    };
    const revisar = () => {
      for (const [nombre, cumple] of Object.entries(reglas)) {
        const regla = formClave.querySelector(`[data-regla="${nombre}"]`);
        if (!regla) continue;
        const ok = cumple();
        regla.classList.toggle("cumple", ok);
        const estado = regla.querySelector("[data-estado]");
        const texto = ok ? "Cumple: " : "Pendiente: ";
        if (estado && estado.textContent !== texto) estado.textContent = texto;   // solo anuncia cambios
      }
    };
    [actual, nueva, confirmacion].forEach((campo) => campo.addEventListener("input", revisar));
    revisar();
  }

  // Menú del usuario: se cierra al hacer clic fuera o con Escape.
  const menu = document.querySelector(".menu-usuario");
  if (menu) {
    document.addEventListener("click", (evento) => {
      if (menu.open && !menu.contains(evento.target)) menu.open = false;
    });
    document.addEventListener("keydown", (evento) => {
      if (evento.key === "Escape" && menu.open) { menu.open = false; menu.querySelector("summary").focus(); }
    });
  }

  // IU-05: el campo de cliente solo aparece en paquetes personalizados (RN-12).
  const formPaquete = document.querySelector("[data-paquete]");
  if (formPaquete) {
    const campoCliente = formPaquete.querySelector("[data-campo-cliente]");
    const select = campoCliente.querySelector("select");
    const actualizar = () => {
      const tipo = formPaquete.querySelector("[data-tipo-paquete]:checked")?.value;
      const personalizado = tipo === "PERSONALIZADO";
      campoCliente.hidden = !personalizado;
      select.required = personalizado;
      if (!personalizado) select.value = "";
    };
    formPaquete.querySelectorAll("[data-tipo-paquete]").forEach((r) =>
      r.addEventListener("change", actualizar));
    actualizar();

    // Resumen vivo: "5 platillos · $280.00 por persona", como en la tarjeta del catálogo.
    const resumen = formPaquete.querySelector("[data-resumen-paquete]");
    const precio = formPaquete.querySelector("#precio_persona");
    const moneda = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
    const resumir = () => {
      const n = formPaquete.querySelectorAll('input[name="platillos"]:checked').length;
      const p = parseFloat(precio.value);
      const partes = [n ? `${n} ${n === 1 ? "platillo" : "platillos"}` : "Elige al menos un platillo"];
      if (p >= 0) partes.push(`${moneda.format(p)} por persona`);
      resumen.textContent = partes.join(" · ");
    };
    // Solo en "change": el anuncio no se repite con cada tecla del precio.
    formPaquete.addEventListener("change", resumir);
    resumir();

    // Con muchos clientes, filtrar la lista mientras se escribe el nombre.
    const filtro = formPaquete.querySelector("[data-filtro-cliente]");
    filtro?.addEventListener("input", () => {
      const texto = filtro.value.trim().toLowerCase();
      for (const opcion of select.options) {
        opcion.hidden = Boolean(opcion.value) && !opcion.text.toLowerCase().includes(texto);
      }
    });
  }

  // IU-06 (Figura 32) · Cotización en vivo, lugares disponibles, agenda del salón
  // y alta rápida del cliente. Solo orienta la captura: el costo oficial lo calcula
  // la base al guardar (RN-09) y el aforo y el traslape los hacen cumplir los
  // triggers de HU-007 (BF001 y BF002).
  const formReserva = document.querySelector("[data-reservacion]");
  if (formReserva) {
    const $ = (selector) => formReserva.querySelector(selector);
    const salon = $("#id_salon"), paquete = $("#id_paquete"), invitados = $("#num_asistentes");
    const inicio = $("#hora_inicio"), termino = $("#hora_fin"), fecha = $("#fecha_evento");
    const agenda = $("[data-agenda]"), avisoTraslape = $("[data-aviso-traslape]");
    let traslape = "";            // mensaje del traslape vigente; "" si el horario está libre
    let consultaAgenda = null;    // AbortController de la consulta en curso
    let esperaAgenda = 0;
    const cliente = $("#id_cliente"), esNuevo = $("#cliente_nuevo");
    const bloqueNuevo = $("[data-cliente-nuevo]"), bloqueExistente = $("[data-cliente-existente]");
    const avisoAforo = $("[data-aviso-aforo]"), avisoHorario = $("[data-aviso-horario]");
    const guardar = $("[data-guardar]"), motivo = $("[data-motivo]");
    const salida = {
      renta: $("[data-cot-renta]"), etiquetaPaquete: $("[data-cot-paquete-etiqueta]"),
      paquete: $("[data-cot-paquete]"), total: $("[data-cot-total]"), lugares: $("[data-cot-lugares]"),
    };
    const pesos = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
    const enteros = new Intl.NumberFormat("es-MX");
    const elegida = (select) => (select.value ? select.selectedOptions[0] : null);
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)");

    // El total cuenta hacia su nuevo valor (≈300 ms). aria-busy evita que el lector
    // de pantalla anuncie cada paso: solo se lee la cifra final.
    const contar = (elemento, valor) => {
      const desde = Number(elemento.dataset.valor) || 0;
      elemento.dataset.valor = valor;
      cancelAnimationFrame(elemento._cuadro);
      if (quieto.matches || !desde || desde === valor) { elemento.textContent = pesos.format(valor); return; }
      const caja = elemento.closest("[aria-live]");
      caja?.setAttribute("aria-busy", "true");
      const inicioAnim = performance.now();
      const paso = (ahora) => {
        const avance = Math.min(1, (ahora - inicioAnim) / 300);
        const suave = 1 - Math.pow(1 - avance, 3);
        elemento.textContent = pesos.format(Math.round(desde + (valor - desde) * suave));
        if (avance < 1) { elemento._cuadro = requestAnimationFrame(paso); return; }
        elemento.textContent = pesos.format(valor);
        caja?.setAttribute("aria-busy", "false");
      };
      elemento._cuadro = requestAnimationFrame(paso);
    };

    // Overdrive · línea del día: los eventos de la agenda como bloques sobre las horas
    // y el horario capturado como bloque fantasma (rojo si se encima con uno que aparta).
    const linea = $("[data-linea-dia]"), pista = $("[data-linea-pista]"), regla = $("[data-linea-horas]");
    let eventosDelDia = [];
    const minutos = (hhmm) => { const [h, m] = hhmm.split(":").map(Number); return h * 60 + m; };
    const pintarLinea = () => {
      const fantasma = inicio.value && termino.value && termino.value > inicio.value
        ? { inicio: inicio.value, fin: termino.value } : null;
      const horarios = [...eventosDelDia, ...(fantasma ? [fantasma] : [])];
      if (!horarios.length) { linea.hidden = true; return; }
      linea.hidden = false;
      const desde = Math.min(8, ...horarios.map((e) => Math.floor(minutos(e.inicio) / 60)));
      const hasta = 24, horas = hasta - desde;
      const posicion = (e) => {
        const a = Math.max(0, minutos(e.inicio) - desde * 60), b = minutos(e.fin) - desde * 60;
        return { left: `${(a / (horas * 60)) * 100}%`, width: `${((b - a) / (horas * 60)) * 100}%` };
      };
      pista.style.setProperty("--horas", horas);
      // Las cotizaciones van primero y en un carril delgado abajo: lo que aparta se dibuja encima.
      const bloques = [...eventosDelDia].sort((a, b) => Number(a.aparta) - Number(b.aparta)).map((e) => {
        const bloque = document.createElement("span");
        bloque.className = `linea-dia__bloque${e.aparta ? "" : " linea-dia__bloque--cotiza"}`;
        Object.assign(bloque.style, posicion(e));
        return bloque;
      });
      let previo = pista.querySelector(".linea-dia__bloque--fantasma");
      pista.replaceChildren(...bloques);
      if (fantasma) {
        const choca = eventosDelDia.some((e) => e.aparta && e.inicio < fantasma.fin && fantasma.inicio < e.fin);
        const bloque = previo || document.createElement("span");
        const estabaChocando = bloque.classList.contains("linea-dia__bloque--choca");
        bloque.className = "linea-dia__bloque linea-dia__bloque--fantasma";
        if (choca) {
          if (!estabaChocando) void bloque.offsetWidth;   // reinicia el temblor solo al entrar en choque
          bloque.classList.add("linea-dia__bloque--choca");
        }
        Object.assign(bloque.style, posicion(fantasma));
        pista.append(bloque);
      }
      const salto = horas > 12 ? (pista.clientWidth < 320 ? 4 : 3) : 2, marcas = [];   // menos marcas en el celular
      for (let h = desde; h <= hasta; h += salto) marcas.push(h);
      // La última marca es siempre el fin del día; si queda pegada a la anterior, la reemplaza.
      if (marcas[marcas.length - 1] !== hasta) {
        if (hasta - marcas[marcas.length - 1] < salto) marcas.pop();
        marcas.push(hasta);
      }
      regla.replaceChildren(...marcas.map((h) => {
        const marca = document.createElement("span");
        marca.textContent = `${String(h).padStart(2, "0")}:00`;
        marca.style.left = `${((h - desde) / horas) * 100}%`;
        return marca;
      }));
    };

    // Un paquete personalizado solo se ofrece a su dueño (RN-12).
    const filtrarPaquetes = () => {
      const dueno = esNuevo.checked ? "" : cliente.value;
      for (const opcion of paquete.options) {
        if (!opcion.value) continue;
        const propio = opcion.dataset.cliente === "" || opcion.dataset.cliente === dueno;
        opcion.disabled = !propio;
        opcion.hidden = !propio;
      }
      if (paquete.selectedOptions[0]?.disabled) paquete.value = "";
    };

    const alternarCliente = () => {
      bloqueNuevo.hidden = !esNuevo.checked;
      bloqueExistente.hidden = esNuevo.checked;
      cliente.required = !esNuevo.checked;
      formReserva.querySelector("#nombre").required = esNuevo.checked;
      filtrarPaquetes();
    };

    const recalcular = () => {
      const s = elegida(salon), p = elegida(paquete);
      const n = Math.max(0, parseInt(invitados.value, 10) || 0);
      const renta = s ? Number(s.dataset.renta) : 0;
      const precio = p ? Number(p.dataset.precio) : 0;

      salida.renta.textContent = s ? pesos.format(renta) : "—";
      salida.etiquetaPaquete.textContent = `Paquete × ${enteros.format(n)} pers.`;
      salida.paquete.textContent = p ? pesos.format(precio * n) : "—";
      if (s && p && n) contar(salida.total, renta + precio * n);
      else { salida.total.textContent = "—"; salida.total.dataset.valor = ""; }

      // RF-23 · lugares disponibles y aviso de aforo excedido
      let problema = "";
      salida.lugares.classList.remove("excedido", "justo");
      if (s && n) {
        const capacidad = Number(s.dataset.capacidad);
        const libres = capacidad - n;
        salida.lugares.textContent = libres < 0 ? `−${enteros.format(-libres)}` : enteros.format(libres);
        if (libres < 0) {
          salida.lugares.classList.add("excedido");
          problema = "aforo";
          // Solo se reescribe si cambió: un role="alert" se anuncia cada vez que cambia su texto.
          const mensaje = `El ${s.dataset.nombre} admite ${enteros.format(capacidad)} personas y capturaste ` +
            `${enteros.format(n)}. Reduce los invitados o elige otro salón.`;
          if (avisoAforo.textContent !== mensaje) avisoAforo.textContent = mensaje;
        } else if (libres <= capacidad * 0.1) {
          salida.lugares.classList.add("justo");
        }
      } else {
        salida.lugares.textContent = s ? enteros.format(Number(s.dataset.capacidad)) : "—";
      }
      avisoAforo.hidden = problema !== "aforo";

      // La hora de término debe ser posterior a la de inicio (ck_evento_horario)
      const horarioMal = inicio.value && termino.value && termino.value <= inicio.value;
      avisoHorario.hidden = !horarioMal;
      if (horarioMal) {
        avisoHorario.textContent = `La hora de término (${termino.value}) debe ser posterior a la de inicio (${inicio.value}).`;
        problema = problema || "horario";
      }

      // RF-24 · el horario se encima con un evento ya programado (lo informó /api/agenda)
      avisoTraslape.hidden = !traslape || Boolean(horarioMal);
      if (traslape && !horarioMal) {
        avisoTraslape.textContent = traslape;
        problema = problema || "traslape";
      }

      pintarLinea();
      // Todas las reglas que fallan, no solo la primera: corregir una no debe revelar otra por sorpresa.
      const fallas = [
        !avisoAforo.hidden && "el aforo excedido",
        !avisoHorario.hidden && "la hora de término",
        !avisoTraslape.hidden && "el horario encimado con otro evento",
      ].filter(Boolean);
      guardar.disabled = Boolean(problema);
      motivo.hidden = !fallas.length;
      motivo.textContent = fallas.length
        ? `Deshabilitado hasta resolver ${fallas.length > 1 ? fallas.slice(0, -1).join(", ") + " y " + fallas.at(-1) : fallas[0]}.`
        : "";
    };

    // RF-24 (HU-007) · Agenda del salón en la fecha capturada.
    // El servidor decide qué eventos se enciman; aquí solo se pinta la respuesta.
    // Huecos del día (08:00–24:00) que no aparta ningún evento: «08:00–14:00 y 19:00–24:00».
    const horasLibres = (eventos) => {
      const ocupados = eventos.filter((e) => e.aparta).sort((a, b) => (a.inicio < b.inicio ? -1 : 1));
      const huecos = [];
      let desde = "08:00";
      for (const e of ocupados) {
        if (e.inicio > desde) huecos.push(`${desde}–${e.inicio}`);
        if (e.fin > desde) desde = e.fin;
      }
      if (desde < "24:00") huecos.push(`${desde}–24:00`);
      return huecos.length > 1 ? `${huecos.slice(0, -1).join(", ")} y ${huecos.at(-1)}` : (huecos[0] || "");
    };

    const pintarAgenda = (datos) => {
      const lista = agenda.querySelector("[data-agenda-lista]");
      const estado = agenda.querySelector("[data-agenda-estado]");
      agenda.querySelector("[data-agenda-titulo]").textContent =
        `Agenda de ${datos.salon.nombre} · ${datos.fecha_legible}`;
      lista.replaceChildren(...datos.eventos.map((e) => {
        const fila = document.createElement("li");
        const horas = document.createElement("span");
        horas.className = "agenda-dia__horas";
        horas.textContent = `${e.inicio} a ${e.fin}`;
        const detalle = document.createElement("span");
        detalle.textContent = `${e.clave} · ${e.titulo} (${e.estado})`;
        fila.append(horas, detalle);
        if (e.traslapa) {
          fila.className = "agenda-dia__encimado";
          const marca = document.createElement("strong");
          marca.textContent = "Se encima";
          fila.append(marca);
        } else if (e.compite) {
          // D-20: una cotización no aparta el horario; solo se avisa que hay otra en la fila
          const marca = document.createElement("strong");
          marca.textContent = "También cotizado";
          fila.append(marca);
        }
        return fila;
      }));
      // Ámbar solo como advertencia previa: el día tiene eventos y aún no hay horario que comparar.
      // Libre queda neutro y un choque lo dice el aviso rojo, una sola vez.
      agenda.classList.toggle("agenda-dia--ocupada", datos.libre === null && datos.eventos.some((e) => e.aparta));
      eventosDelDia = datos.eventos;
      const encimados = datos.eventos.filter((e) => e.traslapa);
      const libres = horasLibres(datos.eventos);
      const compiten = datos.eventos.filter((e) => e.compite);
      if (!datos.eventos.length) {
        estado.textContent = "Sin eventos ese día: el salón está libre.";
      } else if (datos.libre === null) {
        estado.textContent = "Ese día ya hay eventos. Captura el horario para saber si está libre." +
          (libres ? ` Libre: ${libres}.` : "");
      } else if (datos.libre && compiten.length) {
        estado.textContent = `El horario de ${inicio.value} a ${termino.value} está libre, pero ` +
          (compiten.length === 1 ? "hay otra cotización" : `hay ${compiten.length} cotizaciones`) +
          " para ese horario: el salón lo aparta el primer evento que se confirme con anticipo.";
      } else if (datos.libre) {
        estado.textContent = `Ese día ya hay eventos, pero el horario de ${inicio.value} a ${termino.value} está libre.`;
      } else {
        estado.textContent = "";      // el aviso rojo de arriba ya lo dice, con la sugerencia
      }
      traslape = encimados.length
        ? `«${datos.salon.nombre}» ya está ocupado el ${datos.fecha_legible} de ${encimados[0].inicio} a ` +
          `${encimados[0].fin} por el evento ${encimados[0].clave}. ` +
          (libres ? `Libre ese día: ${libres}.` : "Elige otra fecha u otro salón.")
        : "";
      agenda.hidden = false;
    };

    const consultarAgenda = () => {
      clearTimeout(esperaAgenda);
      consultaAgenda?.abort();
      if (!salon.value || !fecha.value) {
        agenda.hidden = true; traslape = ""; eventosDelDia = []; recalcular();
        return;
      }
      esperaAgenda = setTimeout(async () => {
        consultaAgenda = new AbortController();
        const parametros = new URLSearchParams({ salon: salon.value, fecha: fecha.value });
        if (inicio.value && termino.value && termino.value > inicio.value) {
          parametros.set("inicio", inicio.value);
          parametros.set("fin", termino.value);
        }
        try {
          const respuesta = await fetch(`${agenda.dataset.url}?${parametros}`, {
            headers: { Accept: "application/json" }, signal: consultaAgenda.signal,
          });
          const esJson = (respuesta.headers.get("content-type") || "").includes("application/json");
          if (!respuesta.ok || !esJson) throw new Error("agenda no disponible");
          pintarAgenda(await respuesta.json());
        } catch (error) {
          if (error.name === "AbortError") return;
          // Sin agenda la captura sigue: la base valida el horario al guardar (BF002).
          agenda.hidden = true; traslape = ""; eventosDelDia = [];
        }
        recalcular();
      }, 250);
    };

    esNuevo.addEventListener("change", () => { alternarCliente(); recalcular(); });
    cliente.addEventListener("change", () => { filtrarPaquetes(); recalcular(); });
    [salon, paquete].forEach((campo) => campo.addEventListener("change", recalcular));
    [invitados, inicio, termino].forEach((campo) => campo.addEventListener("input", recalcular));
    salon.addEventListener("change", consultarAgenda);
    [fecha, inicio, termino].forEach((campo) => campo.addEventListener("input", consultarAgenda));

    // Evita registrar dos veces el mismo evento por un doble clic.
    formReserva.addEventListener("submit", (evento) => {
      if (guardar.disabled) { evento.preventDefault(); return; }
      guardar.disabled = true;
      guardar.textContent = "Guardando…";
    });
    // Al volver con el botón «atrás» el navegador puede restaurar el botón deshabilitado.
    window.addEventListener("pageshow", () => {
      guardar.textContent = "Guardar cotización"; recalcular(); consultarAgenda();
    });

    alternarCliente();
    recalcular();
  }

  document.querySelectorAll("[data-filtros] select").forEach((lista) =>
    lista.addEventListener("change", () => lista.form.requestSubmit()));
  const pliegue = document.querySelector("[data-pliegue-filtros]");
  if (pliegue && !pliegue.hasAttribute("data-activos") && window.matchMedia("(max-width: 640px)").matches) {
    pliegue.open = false;
  }
});

/* ---------------------------------------------------------------------
   IU-07 · Captura de abono (HU-009)
   Solo ayuda a capturar: el diálogo de confirmación muestra el monto
   escrito y avisa si con él se liquida el evento. El saldo y el finiquito
   los decide la base (IB-06); un abono mayor al saldo lo rechaza ella.
   --------------------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
  const abono = document.querySelector("form[data-abono]");
  if (!abono) return;
  const monto = abono.querySelector("#monto");
  // La rueda del ratón no cambia el monto: se desplaza la página, como en cualquier campo de texto.
  monto.addEventListener("wheel", () => { if (document.activeElement === monto) monto.blur(); }, { passive: true });
  const liquidar = abono.querySelector("[data-liquidar]");
  const saldo = parseFloat(abono.dataset.saldo);
  const consecuencia = abono.dataset.confirmar;
  const moneda = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });

  const tipo = abono.querySelector("#tipo"), referencia = abono.querySelector("#referencia");
  const anticipo = abono.querySelector('input[name="confirmar"]');
  const error = abono.querySelector("#monto-error");

  // El diálogo repite lo que se va a guardar (monto · forma · referencia) y los efectos:
  // un abono no se corrige después. Si el monto excede el saldo, se dice en línea y no se envía.
  const actualizar = () => {
    const valor = parseFloat(monto.value);
    const excede = valor > saldo + 0.005;
    error.hidden = !excede;
    error.textContent = excede ? `Excede el saldo por ${moneda.format(valor - saldo)}. El abono máximo es ${moneda.format(saldo)}.` : "";
    if (excede) monto.setAttribute("aria-invalid", "true"); else monto.removeAttribute("aria-invalid");
    if (!(valor > 0)) return;
    abono.dataset.titulo = `¿Registrar abono de ${moneda.format(valor)} a ${abono.dataset.clave}?`;
    const detalle = [moneda.format(valor), tipo.value ? tipo.selectedOptions[0].text : "",
                     referencia.value.trim() ? `Ref. ${referencia.value.trim()}` : ""].filter(Boolean).join(" · ");
    const liquida = Math.abs(valor - saldo) < 0.005;
    abono.dataset.confirmar = `${detalle}. ` +
      (anticipo?.checked ? "El evento pasará a Confirmado y apartará su horario. " : "") +
      (liquida ? "Con este abono el saldo llega a cero y el evento queda finiquitado. " : "") + consecuencia;
  };
  abono.addEventListener("input", actualizar);
  abono.addEventListener("change", actualizar);
  // Antes que el diálogo: con el monto de más, el foco vuelve al campo con su explicación.
  abono.addEventListener("submit", (evento) => {
    actualizar();
    if (!error.hidden) { evento.preventDefault(); evento.stopImmediatePropagation(); monto.focus(); }
  }, true);

  if (saldo > 0) {
    liquidar.hidden = false;
    liquidar.addEventListener("click", () => {
      monto.value = saldo.toFixed(2);
      actualizar();
      monto.focus();
    });
  }
  actualizar();
});

/* =====================================================================
   transitions-dev · movimiento visible (todo decorativo: sin JS la página
   se ve igual). Pestañas deslizantes, medidores que se llenan y cifras que
   cuentan. Con «reducir movimiento» nada de esto corre.
   Los tiempos se leen de los tokens de :root para no desincronizarse del CSS.
   ===================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const raiz = getComputedStyle(document.documentElement);
  const ms = (token, porDefecto) => parseFloat(raiz.getPropertyValue(token)) || porDefecto;
  const suave = (t) => 1 - Math.pow(1 - t, 5);   // misma forma que --ease-smooth-out
  const animar = (duracion, espera, alAvanzar) => {
    setTimeout(() => {
      const inicio = performance.now();
      const paso = (ahora) => {
        const avance = Math.min(1, (ahora - inicio) / duracion);
        alAvanzar(suave(avance), avance === 1);
        if (avance < 1) requestAnimationFrame(paso);
      };
      requestAnimationFrame(paso);
    }, espera);
  };
  const guardado = {
    leer: (k) => { try { const v = sessionStorage.getItem(k); sessionStorage.removeItem(k); return v; } catch { return null; } },
    poner: (k, v) => { try { sessionStorage.setItem(k, v); } catch { /* sin almacenamiento: sin deslizamiento */ } },
  };

  // Tabs sliding: la barra azul viaja desde la pestaña de la que vienes hasta la activa.
  // Las pestañas son enlaces, así que la posición anterior se recuerda al hacer clic.
  document.querySelectorAll(".pestanas").forEach((barra) => {
    const tabs = [...barra.querySelectorAll("a")];
    const activa = tabs.find((t) => t.getAttribute("aria-current") === "page");
    if (!activa) return;
    const pill = document.createElement("span");
    pill.className = "t-tabs-pill";
    pill.setAttribute("aria-hidden", "true");
    barra.prepend(pill);
    barra.classList.add("t-tabs");
    const clave = "pestana:" + (barra.getAttribute("aria-label") || "");

    const moveTo = (tab, animate) => {
      const x = tab.offsetLeft + 1;
      const y = tab.offsetTop + tab.offsetHeight - pill.offsetHeight - 1;
      if (!animate) {
        const prev = pill.style.transition;
        pill.style.transition = "none";
        pill.style.transform = `translate(${x}px, ${y}px)`;
        pill.style.width = `${tab.offsetWidth - 2}px`;
        void pill.offsetWidth;
        pill.style.transition = prev;
      } else {
        pill.style.transform = `translate(${x}px, ${y}px)`;
        pill.style.width = `${tab.offsetWidth - 2}px`;
      }
    };

    tabs.forEach((tab) => tab.addEventListener("click", () => guardado.poner(clave, String(tabs.indexOf(activa)))));
    const anterior = tabs[Number(guardado.leer(clave))];
    if (!quieto && anterior && anterior !== activa) {
      moveTo(anterior, false);
      requestAnimationFrame(() => requestAnimationFrame(() => moveTo(activa, true)));
    } else {
      requestAnimationFrame(() => moveTo(activa, false));
    }
    window.addEventListener("resize", () => moveTo(activa, false));
  });

  if (quieto) return;

  // Medidores de ocupación: se llenan desde cero, uno tras otro.
  document.querySelectorAll("meter.medidor").forEach((medidor, i) => {
    const meta = Number(medidor.value);
    if (!meta) return;
    medidor.value = 0;
    const espera = ms("--duration-micro", 80) * (3 + i);
    animar(ms("--duration-very-slow", 500) * 1.6, espera, (t) => { medidor.value = meta * t; });
  });

  // Cifras de totales y del resumen del panel: cuentan desde cero hasta su valor.
  // El ancho final se reserva para que lo de al lado no brinque mientras cuenta.
  const pesos = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
  const enteros = new Intl.NumberFormat("es-MX");
  document.querySelectorAll(".total__cifra, .resumen-panel strong").forEach((cifra, i) => {
    const texto = cifra.textContent.trim();
    if (!/^\$?[\d,]+(\.\d+)?$/.test(texto)) return;
    const esMoneda = texto.startsWith("$");
    const meta = Number(texto.replace(/[$,]/g, ""));
    if (!meta) return;
    const escribir = (n) => { cifra.textContent = esMoneda ? pesos.format(n) : enteros.format(Math.round(n)); };
    cifra.style.display = "inline-block";
    cifra.style.minWidth = `${cifra.getBoundingClientRect().width}px`;
    escribir(0);
    const espera = ms("--duration-micro", 80) * 2 + ms("--duration-stagger", 40) * i;
    animar(ms("--duration-very-slow", 500) * 1.6, espera, (t, fin) => {
      if (fin) { cifra.textContent = texto; return; }
      escribir(esMoneda ? Math.round(meta * t * 100) / 100 : meta * t);
    });
  });
});
