"""
Portal del cliente · C-07 · IU-09, IU-10 · HU-008
/mis-eventos · /mis-eventos/<clave>  (SDD Anexo A)

Las dos rutas son de solo lectura (GET). El titular se toma de la sesión
con usuario_actual(); la clave de la dirección solo dice CUÁL de sus
eventos quiere ver. Pedir el evento de otro cliente devuelve al usuario
a su propio panel (CP-13, RNF-06).
"""
from flask import Blueprint, flash, redirect, render_template, url_for

from app.datos.errores import ErrorNoEncontrado
from app.seguridad.decoradores import solo_cliente
from app.seguridad.sesion import usuario_actual
from app.servicios.servicio_portal import ServicioPortal

bp = Blueprint("portal", __name__)
_portal = ServicioPortal()


@bp.get("/mis-eventos")
@solo_cliente
def mis_eventos():
    """IU-09 · RF-39."""
    return render_template("portal/mis_eventos.html",
                           lista=_portal.mis_eventos(usuario_actual().id_usuario))


@bp.get("/mis-eventos/<clave>")
@solo_cliente
def detalle(clave: str):
    """IU-10 · RF-40."""
    try:
        contenido = _portal.detalle(usuario_actual().id_usuario, clave)
    except ErrorNoEncontrado as error:
        flash(error.mensaje, "aviso")
        return redirect(url_for("portal.mis_eventos"))
    return render_template("portal/detalle.html", evento=contenido.evento, paquete=contenido.paquete,
                           pagos=contenido.pagos, hoy=contenido.hoy)
