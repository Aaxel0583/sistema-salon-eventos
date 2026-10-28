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
  document.querySelectorAll("form[data-confirmar]").forEach((formulario) => {
    formulario.addEventListener("submit", (evento) => {
      if (!window.confirm(formulario.dataset.confirmar)) evento.preventDefault();
    });
  });

  // IU-02: las tres condiciones de la clave nueva se marcan al escribir.
  const formClave = document.querySelector("[data-validar-clave]");
  if (formClave) {
    const nueva = formClave.querySelector("#new-password");
    const reglas = {
      largo: (v) => v.length >= 8,
      letra: (v) => /\p{L}/u.test(v),
      numero: (v) => /\d/.test(v),
    };
    const revisar = () => {
      for (const [nombre, cumple] of Object.entries(reglas)) {
        formClave.querySelector(`[data-regla="${nombre}"]`)
          ?.classList.toggle("cumple", cumple(nueva.value));
      }
    };
    nueva.addEventListener("input", revisar);
    revisar();
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
