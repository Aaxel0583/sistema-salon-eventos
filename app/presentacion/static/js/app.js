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
});
