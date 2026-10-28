"""
Sistema de Reservaciones y Gestión para Salón de Eventos.

Fábrica de la aplicación Flask (patrón Application Factory).
Ensambla las capas del SDD §3: presentación (PKG-01), rutas (PKG-02),
servicios (PKG-03), seguridad (PKG-04) y acceso a datos (PKG-05).
"""
import logging

from flask import Flask, g, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from app.config import Configuracion
from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorDominio
from app.datos.repositorio_usuarios import RepositorioUsuarios
from app.seguridad.sesion import cerrar_sesion, id_en_sesion

csrf = CSRFProtect()

# Endpoints que un usuario con clave inicial sí puede visitar (RF-04).
_PERMITIDOS_CON_CLAVE_INICIAL = {"acceso.cambiar_clave", "acceso.logout", "static"}


def create_app(config: Configuracion | None = None) -> Flask:
    config = config or Configuracion.desde_entorno()

    app = Flask(
        __name__,
        template_folder="presentacion/templates",
        static_folder="presentacion/static",
    )
    app.config.update(
        SECRET_KEY=config.secret_key,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=config.cookie_segura,
        PERMANENT_SESSION_LIFETIME=config.DURACION_SESION,
        WTF_CSRF_TIME_LIMIT=None,          # el token vive lo que viva la sesión
        CONFIGURACION=config,
    )
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    csrf.init_app(app)
    BaseDatos.iniciar(config.database_url, config.pool_min, config.pool_max)

    _registrar_blueprints(app)
    _registrar_ganchos(app, config)
    _registrar_errores(app)
    return app


def _registrar_blueprints(app: Flask) -> None:
    from app.rutas.acceso import bp as acceso
    from app.rutas.catalogos import bp as catalogos
    from app.rutas.clientes import bp as clientes
    from app.rutas.panel import bp as panel
    from app.rutas.portal import bp as portal

    for blueprint in (acceso, panel, clientes, catalogos, portal):
        app.register_blueprint(blueprint)


def _registrar_ganchos(app: Flask, config: Configuracion) -> None:

    @app.before_request
    def cargar_usuario():
        """Relee al usuario en cada petición (RF-05, RF-06, RNF-06)."""
        g.usuario = None
        if request.endpoint == "static":
            return None
        id_usuario = id_en_sesion()
        if id_usuario is None:
            return None

        with BaseDatos.transaccion() as cur:
            usuario = RepositorioUsuarios(cur).por_id(id_usuario)
        if usuario is None or usuario.esta_bloqueado:
            cerrar_sesion()
            return redirect(url_for("acceso.login"))
        g.usuario = usuario

        # RF-04: con la clave inicial no se puede hacer nada más.
        if usuario.debe_cambiar_clave and request.endpoint not in _PERMITIDOS_CON_CLAVE_INICIAL:
            return redirect(url_for("acceso.cambiar_clave"))
        return None

    @app.context_processor
    def datos_globales():
        return {"nombre_negocio": config.nombre_negocio, "usuario": g.get("usuario")}

    @app.after_request
    def cabeceras_seguridad(respuesta):
        respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
        respuesta.headers.setdefault("X-Frame-Options", "DENY")
        respuesta.headers.setdefault("Referrer-Policy", "same-origin")
        respuesta.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "form-action 'self'; frame-ancestors 'none'",
        )
        # Las páginas con datos personales no se guardan en caché del navegador.
        if g.get("usuario") is not None:
            respuesta.headers["Cache-Control"] = "no-store"
        return respuesta

    @app.teardown_appcontext
    def _limpiar(_excepcion=None):
        g.pop("usuario", None)


def _registrar_errores(app: Flask) -> None:

    @app.errorhandler(ErrorDominio)
    def error_dominio(error: ErrorDominio):
        # Último recurso: las rutas deberían atrapar y mostrar el error en su pantalla.
        return render_template("errores/error.html", titulo="No se pudo completar la operación",
                               mensaje=error.mensaje), 400

    @app.errorhandler(CSRFError)
    def error_csrf(_error):
        return render_template("errores/error.html", titulo="La página expiró",
                               mensaje="Vuelve a cargar la página e inténtalo de nuevo."), 400

    @app.errorhandler(404)
    def no_encontrado(_error):
        return render_template("errores/error.html", titulo="Página no encontrada",
                               mensaje="La dirección no existe o ya no está disponible."), 404

    @app.errorhandler(500)
    def error_interno(_error):
        return render_template("errores/error.html", titulo="Algo salió mal",
                               mensaje="Ocurrió un error inesperado. Intenta de nuevo."), 500
