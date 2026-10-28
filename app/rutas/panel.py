"""
Tablero del gerente · C-08 · IU-03 · /panel

Sprint 1: resumen de catálogos y actividad reciente.
Sprint 2 (HU-006): indicadores, ocupación por salón y eventos por cerrar.
"""
from flask import Blueprint, render_template

from app.datos.conexion import BaseDatos
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_catalogos import RepositorioPaquetes, RepositorioSalones
from app.datos.repositorio_usuarios import RepositorioUsuarios
from app.dominio.modelos import ROL_CLIENTE
from app.seguridad.decoradores import solo_gerente

bp = Blueprint("panel", __name__)


@bp.get("/panel")
@solo_gerente
def inicio():
    with BaseDatos.transaccion() as cur:
        resumen = {
            "salones": RepositorioSalones(cur).listar(),
            "clientes": RepositorioUsuarios(cur).contar_por_rol(ROL_CLIENTE),
            "paquetes": RepositorioPaquetes(cur).contar(),
            "actividad": RepositorioBitacora(cur).recientes(10),
        }
    return render_template("panel.html", **resumen)
