"""
Manejo de la sesión del usuario autenticado.

C-01 · RF-05 · RF-06 · RNF-06
La cookie de sesión solo guarda el id del usuario. En cada petición se
vuelve a leer el usuario de la base (g.usuario): si fue bloqueado o
eliminado, la sesión deja de valer de inmediato. El rol y el titular
siempre se toman de aquí, nunca de un parámetro de la petición.
"""
import hashlib

from flask import g, session

from app.dominio.modelos import Usuario

_CLAVE_SESION = "id_usuario"
_CLAVE_HUELLA = "huella"


def huella_clave(usuario: Usuario) -> str:
    """Cambia con cada clave nueva: una sesión abierta con la clave anterior deja de valer."""
    return hashlib.sha256(usuario.clave_hash.encode()).hexdigest()[:16]


def iniciar_sesion(usuario: Usuario) -> None:
    session.clear()                 # evita fijación de sesión
    session.permanent = True
    session[_CLAVE_SESION] = usuario.id_usuario
    session[_CLAVE_HUELLA] = huella_clave(usuario)


def huella_vigente(usuario: Usuario) -> bool:
    return session.get(_CLAVE_HUELLA) == huella_clave(usuario)


def cerrar_sesion() -> None:
    session.clear()
    g.usuario = None


def id_en_sesion() -> int | None:
    return session.get(_CLAVE_SESION)


def usuario_actual() -> Usuario | None:
    return getattr(g, "usuario", None)


def panel_de(usuario: Usuario) -> str:
    """Endpoint de inicio según el rol (mapa de navegación, Figura 26)."""
    return "panel.inicio" if usuario.es_gerente else "portal.mis_eventos"
