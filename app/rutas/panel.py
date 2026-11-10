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
from app.dominio.modelos import ACCIONES_BITACORA, ROL_CLIENTE
from app.seguridad.decoradores import solo_gerente

bp = Blueprint("panel", __name__)

_MESES = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")
_DIAS = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")


@bp.get("/panel")
@solo_gerente
def inicio():
    with BaseDatos.transaccion() as cur:
        usuarios = RepositorioUsuarios(cur)
        # La fecha sale de la base: su zona horaria es la del salón (conexion.py).
        cur.execute("SELECT CURRENT_DATE AS hoy")
        hoy = cur.fetchone()["hoy"]
        resumen = {
            "salones": RepositorioSalones(cur).listar(),
            "clientes": usuarios.contar_por_rol(ROL_CLIENTE),
            "bloqueados": usuarios.clientes_bloqueados(),
            "paquetes": RepositorioPaquetes(cur).contar(),
            # Los inicios de sesión son ruido para el gerente; siguen en la bitácora.
            "actividad": RepositorioBitacora(cur).recientes(10, excluir=("INICIO_SESION",)),
        }
    return render_template("panel.html", acciones=ACCIONES_BITACORA, hoy=hoy,
                           MESES=_MESES, DIAS=_DIAS, **resumen)
