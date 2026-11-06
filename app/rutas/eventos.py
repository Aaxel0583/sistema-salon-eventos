"""
Eventos · C-04 y C-08 · IU-06, IU-07 (parcial) · HU-005, HU-006
/eventos · /eventos/nuevo · /eventos/<id> · /eventos/<id>/estado  (SDD Anexo A)

Tras registrar un evento:
- con un cliente existente se redirige a la ficha (POST/redirect/GET);
- con un cliente dado de alta en la misma pantalla se presenta la
  respuesta directamente, porque incluye su clave inicial y esa clave no
  se guarda en la sesión (mismo criterio que rutas/clientes.py).
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.datos.errores import ErrorDominio
from app.dominio.modelos import ESTADOS_EVENTO
from app.seguridad.decoradores import solo_gerente
from app.seguridad.sesion import usuario_actual
from app.servicios.servicio_catalogos import ServicioSalones
from app.servicios.servicio_eventos import ServicioEventos, ServicioReservaciones

bp = Blueprint("eventos", __name__, url_prefix="/eventos")
_reservaciones = ServicioReservaciones()
_eventos = ServicioEventos()

# Campos de IU-06 que se devuelven al formulario si algo falla (RNF-12: no perder lo capturado).
_CAMPOS_RESERVACION = ("id_cliente", "cliente_nuevo", "nombre", "correo", "telefono", "nombre_evento",
                       "id_salon", "id_paquete", "fecha_evento", "hora_inicio", "hora_fin",
                       "num_asistentes")

# Pantallas a las que puede volver un cambio de estatus (lista cerrada: no hay redirección abierta).
_DESTINOS = {"panel": "panel.inicio", "listado": "eventos.listado"}


# ------------------------------ Listado ------------------------------
@bp.get("")
@solo_gerente
def listado():
    filtros = {
        "estado": request.args.get("estado", ""),
        "id_salon": request.args.get("salon", ""),
        "texto": request.args.get("q", ""),
    }
    eventos, hoy = _eventos.listar(**filtros)
    return render_template(
        "eventos/listado.html",
        eventos=eventos,
        hoy=hoy,
        salones=ServicioSalones().listar(),
        estados=ESTADOS_EVENTO,
        filtros=filtros,
        hay_filtros=any(v.strip() for v in filtros.values()),
        limite=_eventos.limite_listado,
    )


# --------------------------- IU-06 Reservación ---------------------------
def _formulario(datos: dict | None = None, estado: int = 200):
    contexto = _reservaciones.datos_formulario()
    datos = dict(datos or {})
    if not datos and request.args.get("cliente", "").isdigit():     # llegada desde el directorio
        datos["id_cliente"] = request.args["cliente"]
    return render_template("eventos/nuevo.html", datos=datos, **vars(contexto)), estado


@bp.get("/nuevo")
@solo_gerente
def nuevo():
    return _formulario()


@bp.post("/nuevo")
@solo_gerente
def registrar():
    datos = {k: request.form.get(k, "") for k in _CAMPOS_RESERVACION}
    try:
        resultado = _reservaciones.registrar(usuario_actual().id_usuario, request.form)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        return _formulario(datos, 422)

    evento = resultado.evento
    if resultado.cliente_nuevo:
        return render_template("eventos/registrado.html", evento=evento,
                               clave_mostrada=resultado.cliente_nuevo)
    flash(f"Evento {evento.clave_proyecto} registrado en cotización por "
          f"${evento.costo_total:,.2f}.", "exito")
    return redirect(url_for("eventos.ficha", id_evento=evento.id_evento))


# ------------------------------ Ficha ------------------------------
@bp.get("/<int:id_evento>")
@solo_gerente
def ficha(id_evento: int):
    try:
        evento, paquete, gerentes, hoy = _eventos.obtener(id_evento)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        return redirect(url_for("eventos.listado"))
    return render_template("eventos/ficha.html", evento=evento, paquete=paquete,
                           gerentes=gerentes, hoy=hoy, estados=ESTADOS_EVENTO,
                           siguientes=evento.estados_siguientes(hoy))


@bp.post("/<int:id_evento>")
@solo_gerente
def asignar_gerente(id_evento: int):
    """RF-29 · Gerente responsable."""
    try:
        evento = _eventos.asignar_gerente(usuario_actual().id_usuario, id_evento,
                                          request.form.get("id_gerente"))
    except ErrorDominio as error:
        flash(error.mensaje, "error")
    else:
        flash(f"{evento.nombre_gerente} quedó como responsable de {evento.clave_proyecto}.", "exito")
    return redirect(url_for("eventos.ficha", id_evento=id_evento))


@bp.post("/<int:id_evento>/estado")
@solo_gerente
def cambiar_estado(id_evento: int):
    """Cambio de estatus desde la ficha o desde el aviso de pendientes del tablero."""
    destino = _DESTINOS.get(request.form.get("volver", ""))
    try:
        evento = _eventos.cambiar_estado(usuario_actual().id_usuario, id_evento,
                                         request.form.get("estado", ""))
    except ErrorDominio as error:
        flash(error.mensaje, "error")
    else:
        flash(f"{evento.clave_proyecto} quedó en estatus {evento.estado_legible}.", "exito")
    if destino:
        return redirect(url_for(destino))
    return redirect(url_for("eventos.ficha", id_evento=id_evento))
