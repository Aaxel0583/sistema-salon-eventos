"""
Decoradores de control de acceso por rol.

C-01 · RF-05 · RNF-06 · SDD §9: "ocultar un enlace en la plantilla no se
considera un control". Toda ruta protegida lleva uno de estos decoradores
y la verificación ocurre en el servidor.
"""
from functools import wraps

from flask import flash, redirect, request, url_for

from app.seguridad.sesion import panel_de, usuario_actual


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if usuario_actual() is None:
            return redirect(url_for("acceso.login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura


def rol_requerido(*roles: str):
    """Permite la vista solo a los roles indicados; a los demás los regresa a su panel."""
    def decorador(vista):
        @wraps(vista)
        @login_requerido
        def envoltura(*args, **kwargs):
            usuario = usuario_actual()
            if usuario.rol not in roles:
                flash("No tienes acceso a esa sección.", "aviso")
                return redirect(url_for(panel_de(usuario)))
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def solo_gerente(vista):
    return rol_requerido("GERENTE")(vista)


def solo_cliente(vista):
    return rol_requerido("CLIENTE")(vista)
