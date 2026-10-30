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
  const dialogo = document.getElementById("confirmacion");
  document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
      evento.preventDefault();
      dialogo.querySelector("[data-mensaje]").textContent = formulario.dataset.confirmar;
      dialogo.returnValue = "";
      dialogo.addEventListener("close", () => {
        if (dialogo.returnValue === "si") formulario.submit();
      }, { once: true });
      dialogo.showModal();
    });
  });

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
        formClave.querySelector(`[data-regla="${nombre}"]`)?.classList.toggle("cumple", cumple());
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
  }
});
