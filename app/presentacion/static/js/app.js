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

  // Confirmación antes de acciones irreversibles (regenerar clave, eliminar).
  // Escape o "Cancelar" cierran sin enviar; el foco inicia en "Cancelar".
  // Cada formulario trae su título (data-titulo), su consecuencia (data-confirmar) y su verbo (data-verbo).
  const dialogo = document.getElementById("dialogo-confirmar");
  document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
      evento.preventDefault();
      dialogo.querySelector("[data-titulo]").textContent = formulario.dataset.titulo || "¿Confirmas la acción?";
      dialogo.querySelector("[data-mensaje]").textContent = formulario.dataset.confirmar;
      dialogo.querySelector("[data-verbo]").textContent = formulario.dataset.verbo || "Continuar";
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

  // IU-06 (Figura 32) · Cotización en vivo, lugares disponibles y alta rápida del cliente.
  // Solo orienta la captura: el costo oficial lo calcula la base al guardar (RN-09)
  // y el aforo lo hace cumplir el trigger de HU-007 (BF001).
  const formReserva = document.querySelector("[data-reservacion]");
  if (formReserva) {
    const $ = (selector) => formReserva.querySelector(selector);
    const salon = $("#id_salon"), paquete = $("#id_paquete"), invitados = $("#num_asistentes");
    const inicio = $("#hora_inicio"), termino = $("#hora_fin");
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

      guardar.disabled = Boolean(problema);
      motivo.hidden = !problema;
      motivo.textContent = problema === "aforo" ? "Deshabilitado mientras el aforo no se cumpla."
                         : problema === "horario" ? "Deshabilitado hasta corregir el horario." : "";
    };

    esNuevo.addEventListener("change", () => { alternarCliente(); recalcular(); });
    cliente.addEventListener("change", () => { filtrarPaquetes(); recalcular(); });
    [salon, paquete].forEach((campo) => campo.addEventListener("change", recalcular));
    [invitados, inicio, termino].forEach((campo) => campo.addEventListener("input", recalcular));

    // Evita registrar dos veces el mismo evento por un doble clic.
    formReserva.addEventListener("submit", (evento) => {
      if (guardar.disabled) { evento.preventDefault(); return; }
      guardar.disabled = true;
      guardar.textContent = "Guardando…";
    });
    // Al volver con el botón «atrás» el navegador puede restaurar el botón deshabilitado.
    window.addEventListener("pageshow", () => { guardar.textContent = "Guardar reservación"; recalcular(); });

    alternarCliente();
    recalcular();
  }
});
