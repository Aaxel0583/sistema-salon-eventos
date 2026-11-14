"""
Disponibilidad · C-04 · HU-007 · RF-24 · /api/agenda  (SDD Anexo A)

Única ruta del sistema que devuelve datos y no una página: alimenta la
consulta de agenda de IU-06. Solo informa. Que la agenda diga «libre» no
autoriza nada: la reserva la acepta o la rechaza el trigger IB-03 al
guardar (DA-01), porque entre la consulta y el guardado otro gerente pudo
ocupar el horario.

  GET /api/agenda?salon=3&fecha=2027-02-14&inicio=20:00&fin=23:00
"""
from flask import Blueprint, jsonify, request

from app.datos.errores import ErrorDominio, ErrorNoEncontrado
from app.seguridad.decoradores import solo_gerente
from app.servicios.servicio_eventos import ServicioReservaciones

bp = Blueprint("agenda", __name__, url_prefix="/api")
_reservaciones = ServicioReservaciones()


@bp.get("/agenda")
@solo_gerente
def consultar():
    try:
        agenda = _reservaciones.agenda(request.args.get("salon"), request.args.get("fecha"),
                                       request.args.get("inicio"), request.args.get("fin"))
    except ErrorNoEncontrado as error:
        return jsonify(error=error.mensaje), 404
    except ErrorDominio as error:
        return jsonify(error=error.mensaje), 400
    return jsonify(agenda.como_dict())
