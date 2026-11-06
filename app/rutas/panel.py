"""
Tablero del gerente · C-08 · IU-03 · /panel · HU-006

Sigue DESIGN.md («Panel»): hoja de agenda con la fecha de hoy, conteos en
una línea bajo el título y, primero, los Pendientes con su acción.
Sprint 1: clientes bloqueados y salones no disponibles.
Sprint 2: indicadores de eventos (IB-01), ocupación por salón (IB-10) y
eventos cuya fecha pasó sin cerrarse (IB-11, RN-14).
"""
from flask import Blueprint, render_template

from app.dominio.modelos import ACCIONES_BITACORA
from app.seguridad.decoradores import solo_gerente
from app.servicios.servicio_eventos import ServicioEventos

bp = Blueprint("panel", __name__)

_MESES = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")
_DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


@bp.get("/panel")
@solo_gerente
def inicio():
    return render_template("panel.html", tablero=ServicioEventos().tablero(),
                           acciones=ACCIONES_BITACORA, MESES=_MESES, DIAS=_DIAS)
