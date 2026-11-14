"""
Pagos · C-05 · IU-07 (panel de pagos) · HU-009
/eventos/<id>/pagos  (SDD Anexo A: «Registro de abono con control de saldo»)

Un abono aceptado responde con POST/redirect/GET hacia la ficha: al
recargar la página no se repite. Uno rechazado devuelve la ficha con lo
capturado y el motivo del rechazo.
"""
from flask import Blueprint, flash, redirect, request, url_for

from app.datos.errores import ErrorDominio
from app.rutas.eventos import presentar_ficha
from app.seguridad.decoradores import solo_gerente
from app.seguridad.sesion import usuario_actual
from app.servicios.servicio_pagos import ServicioPagos

bp = Blueprint("pagos", __name__, url_prefix="/eventos")
_pagos = ServicioPagos()


@bp.post("/<int:id_evento>/pagos")
@solo_gerente
def registrar(id_evento: int):
    """RF-31 a RF-34 · Abono con monto, forma de pago y referencia."""
    try:
        resultado = _pagos.registrar(usuario_actual().id_usuario, id_evento, request.form)
    except ErrorDominio as error:
        # Se devuelve la ficha con lo capturado para corregir sin volver a escribir (RNF-12).
        flash(error.mensaje, "error")
        return presentar_ficha(id_evento, abono=request.form, estado=422)

    evento = resultado.evento
    partes = [f"Abono de ${resultado.monto:,.2f} registrado en {evento.clave_proyecto}."]
    if resultado.confirmado:
        partes.append("El evento quedó confirmado y aparta su horario.")
    if resultado.finiquito:
        partes.append("El saldo llegó a cero: el evento quedó finiquitado.")
    else:
        partes.append(f"Saldo pendiente: ${evento.saldo:,.2f}.")
    flash(" ".join(partes), "exito")
    return redirect(url_for("eventos.ficha", id_evento=id_evento) + "#pagos")
