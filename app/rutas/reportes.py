"""
Reportes operativos · C-06 · IU-08 · HU-010, HU-011, HU-012
/reportes/cartera · /reportes/activos · /reportes/realizados  (SDD Anexo A)

La descarga se pide con el parámetro ?formato=csv sobre la misma ruta y
con los mismos filtros (IE-02): el archivo trae las columnas y las filas
que el gerente está viendo (RF-38).
"""
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from app.datos.errores import ErrorDominio
from app.seguridad.decoradores import solo_gerente
from app.seguridad.sesion import usuario_actual
from app.servicios.servicio_reportes import Reporte, ServicioReportes

bp = Blueprint("reportes", __name__, url_prefix="/reportes")
_reportes = ServicioReportes()

# Marca de orden de bytes: sigue siendo UTF-8 (IE-02) y hace que Excel en
# Windows muestre bien los acentos al abrir el archivo con doble clic.
_BOM = "\ufeff"


def _responder(reporte: Reporte):
    """Pantalla o archivo, según se pida. Los dos salen del mismo objeto Reporte."""
    if request.args.get("formato", "").lower() == "csv":
        _reportes.registrar_descarga(usuario_actual().id_usuario, reporte)
        return Response(
            (_BOM + reporte.a_csv()).encode("utf-8"),
            content_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{reporte.nombre_archivo}"'},
        )
    # Enlace de descarga: la misma dirección con sus filtros, más formato=csv.
    filtros = {k: v for k, v in request.args.items() if k != "formato" and v}
    return render_template(
        "reportes/reporte.html", reporte=reporte, servicio=_reportes,
        url_csv=url_for(request.endpoint, formato="csv", **filtros),
    )


@bp.get("")
@solo_gerente
def inicio():
    return redirect(url_for("reportes.cartera"))


@bp.get("/cartera")
@solo_gerente
def cartera():
    """HU-010 · Cobranza preventiva a 21 días."""
    return _responder(_reportes.cartera(request.args.get("semaforo", "")))


@bp.get("/activos")
@solo_gerente
def activos():
    """HU-011 · Carga de trabajo comprometida."""
    return _responder(_reportes.activos(request.args.get("estado", ""), request.args.get("salon", "")))


@bp.get("/realizados")
@solo_gerente
def realizados():
    """HU-012 · Histórico de eventos y su liquidación."""
    try:
        reporte = _reportes.realizados(request.args.get("desde", ""), request.args.get("hasta", ""),
                                       request.args.get("liquidacion", ""))
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        reporte = _reportes.realizados()
    return _responder(reporte)
