"""
Directorio de clientes · C-02 · IU-04 · HU-002
/clientes · /clientes/nuevo · /clientes/<id>/clave  (SDD Anexo A)

La clave generada se presenta en la respuesta del POST y no se guarda en
la sesión: la cookie de Flask es legible por el cliente, así que guardar
ahí la clave en claro la expondría. Por eso no se usa redirect tras el alta.
"""
from flask import Blueprint, flash, render_template, request

from app.datos.errores import ErrorDominio
from app.datos.repositorio_usuarios import LIMITE_BUSQUEDA
from app.seguridad.decoradores import solo_gerente
from app.seguridad.sesion import usuario_actual
from app.servicios.servicio_clientes import ServicioClientes

bp = Blueprint("clientes", __name__, url_prefix="/clientes")
_servicio = ServicioClientes()


def _directorio(clave_mostrada=None, formulario=None, estado=200, mostrar_formulario=False):
    texto = request.args.get("q", "")
    return render_template(
        "clientes/directorio.html",
        clientes=_servicio.buscar(texto),
        limite=LIMITE_BUSQUEDA,
        q=texto,
        clave_mostrada=clave_mostrada,
        formulario=formulario or {},
        mostrar_formulario=mostrar_formulario,
    ), estado


@bp.get("")
@solo_gerente
def directorio():
    return _directorio()


@bp.get("/nuevo")
@solo_gerente
def formulario_nuevo():
    return _directorio(mostrar_formulario=True)


@bp.post("/nuevo")
@solo_gerente
def nuevo():
    formulario = {k: request.form.get(k, "") for k in ("nombre", "correo", "telefono")}
    try:
        registrado = _servicio.registrar(usuario_actual().id_usuario, **formulario)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        return _directorio(formulario=formulario, estado=422, mostrar_formulario=True)
    return _directorio(clave_mostrada=registrado)


@bp.post("/<int:id_cliente>/clave")
@solo_gerente
def regenerar_clave(id_cliente: int):
    try:
        registrado = _servicio.regenerar_clave(usuario_actual().id_usuario, id_cliente)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        return _directorio(estado=422)
    return _directorio(clave_mostrada=registrado)
