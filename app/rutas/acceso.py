"""
Rutas de acceso · C-01 · IU-01, IU-02 · HU-001
/login · /logout · /clave  (SDD Anexo A)
"""
import re

from flask import (Blueprint, current_app, flash, redirect, render_template,
                   request, url_for)

from app.datos.errores import ErrorDominio
from app.seguridad.decoradores import login_requerido
from app.seguridad.sesion import (cerrar_sesion, iniciar_sesion, panel_de,
                                  usuario_actual)
from app.servicios.servicio_acceso import ServicioAcceso

bp = Blueprint("acceso", __name__)


def _servicio() -> ServicioAcceso:
    return ServicioAcceso(current_app.config["CONFIGURACION"].MAX_INTENTOS_FALLIDOS)


def _destino_seguro(siguiente: str | None) -> str | None:
    """Evita redirecciones abiertas: solo rutas internas."""
    # El navegador lee "\" como "/" e ignora tabuladores: "/\evil.com" sería otro sitio.
    if siguiente and re.fullmatch(r"/(?![/\\])[^\s\\]*", siguiente):
        return siguiente
    return None


@bp.get("/")
def raiz():
    usuario = usuario_actual()
    if usuario is None:
        return redirect(url_for("acceso.login"))
    return redirect(url_for(panel_de(usuario)))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if usuario_actual() is not None:
        return redirect(url_for(panel_de(usuario_actual())))

    identificador = ""
    if request.method == "POST":
        identificador = request.form.get("identificador", "")
        try:
            resultado = _servicio().autenticar(identificador, request.form.get("clave", ""))
        except ErrorDominio as error:
            flash(error.mensaje, "error")
        else:
            if resultado.exito:
                iniciar_sesion(resultado.usuario)
                if resultado.usuario.debe_cambiar_clave:
                    return redirect(url_for("acceso.cambiar_clave"))
                destino = _destino_seguro(request.args.get("siguiente"))
                return redirect(destino or url_for(panel_de(resultado.usuario)))
            flash(resultado.mensaje, "error")

    return render_template("acceso/login.html", identificador=identificador)


@bp.post("/logout")
def logout():
    cerrar_sesion()
    flash("Cerraste tu sesión.", "exito")
    return redirect(url_for("acceso.login"))


@bp.route("/clave", methods=["GET", "POST"])
@login_requerido
def cambiar_clave():
    usuario = usuario_actual()
    if request.method == "POST":
        try:
            actualizado = _servicio().cambiar_clave(
                usuario,
                request.form.get("clave_actual", ""),
                request.form.get("clave_nueva", ""),
                request.form.get("confirmacion", ""),
            )
        except ErrorDominio as error:
            flash(error.mensaje, "error")
        else:
            iniciar_sesion(actualizado)     # esta sesión sigue; las demás quedan cerradas
            flash("Tu clave se actualizó.", "exito")
            return redirect(url_for(panel_de(usuario)))

    return render_template("acceso/clave.html", obligatorio=usuario.debe_cambiar_clave)
