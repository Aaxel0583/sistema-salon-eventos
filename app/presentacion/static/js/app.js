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
      salida.total.textContent = s && p && n ? pesos.format(renta + precio * n) : "—";

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
          avisoAforo.textContent = `El ${s.dataset.nombre} admite ${enteros.format(capacidad)} personas y capturaste ` +
            `${enteros.format(n)}. Reduce los invitados o elige otro salón.`;
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

      guardar.disabled = Boolean(problema);
      motivo.hidden = !problema;
      motivo.textContent = problema === "aforo" ? "Deshabilitado mientras el aforo no se cumpla."
                         : problema === "horario" ? "Deshabilitado hasta corregir el horario."
                         : problema === "traslape" ? "Deshabilitado mientras el horario se encime con otro evento." : "";
    };

    // RF-24 (HU-007) · Agenda del salón en la fecha capturada.
    // El servidor decide qué eventos se enciman; aquí solo se pinta la respuesta.
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
      agenda.classList.toggle("agenda-dia--ocupada", datos.eventos.some((e) => e.aparta));
      const encimados = datos.eventos.filter((e) => e.traslapa);
      const compiten = datos.eventos.filter((e) => e.compite);
      if (!datos.eventos.length) {
        estado.textContent = "Sin eventos ese día: el salón está libre.";
      } else if (datos.libre === null) {
        estado.textContent = "Ese día ya hay eventos. Captura el horario para saber si está libre.";
      } else if (datos.libre && compiten.length) {
        estado.textContent = `El horario de ${inicio.value} a ${termino.value} está libre, pero ` +
          (compiten.length === 1 ? "hay otra cotización" : `hay ${compiten.length} cotizaciones`) +
          " para ese horario: el salón lo aparta el primer evento que se confirme con anticipo.";
      } else if (datos.libre) {
        estado.textContent = `Ese día ya hay eventos, pero el horario de ${inicio.value} a ${termino.value} está libre.`;
      } else {
        estado.textContent = "El horario que capturaste no está libre.";
      }
      traslape = encimados.length
        ? `"${datos.salon.nombre}" ya está ocupado el ${datos.fecha_legible} de ${encimados[0].inicio} a ` +
          `${encimados[0].fin} por el evento ${encimados[0].clave}. Elige otro horario, otra fecha u otro salón.`
        : "";
      agenda.hidden = false;
    };

    const consultarAgenda = () => {
      clearTimeout(esperaAgenda);
      consultaAgenda?.abort();
      if (!salon.value || !fecha.value) {
        agenda.hidden = true; traslape = ""; recalcular();
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
          agenda.hidden = true; traslape = "";
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
      guardar.textContent = "Guardar reservación"; recalcular(); consultarAgenda();
    });

    alternarCliente();
    recalcular();
  }
});
