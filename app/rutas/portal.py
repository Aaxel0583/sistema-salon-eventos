"""
Portal del cliente · C-07 · IU-09, IU-10 · HU-008

Sprint 1: solo existe la pantalla de llegada del cliente para que el
acceso por rol (HU-001) tenga destino. El listado real de eventos,
filtrado por el titular de la sesión (RF-39, RNF-06), se construye en
el Sprint 2.
"""
from flask import Blueprint, render_template

from app.seguridad.decoradores import solo_cliente

bp = Blueprint("portal", __name__)


@bp.get("/mis-eventos")
@solo_cliente
def mis_eventos():
    return render_template("portal/mis_eventos.html")
