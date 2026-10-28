"""
Catálogos operativos · C-03 · IU-05 · HU-003, HU-004
/salones · /platillos · /paquetes  (SDD Anexo A)
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.datos.errores import ErrorDominio
from app.dominio.modelos import CATEGORIAS_PLATILLO, TIPOS_PAQUETE, agrupar_por_categoria
from app.seguridad.decoradores import solo_gerente
from app.seguridad.sesion import usuario_actual
from app.servicios.servicio_catalogos import (ServicioPaquetes,
                                              ServicioPlatillos,
                                              ServicioSalones)
from app.servicios.servicio_clientes import ServicioClientes

bp = Blueprint("catalogos", __name__)
_salones = ServicioSalones()
_platillos = ServicioPlatillos()
_paquetes = ServicioPaquetes()


# ------------------------------- Salones -------------------------------
@bp.get("/salones")
@solo_gerente
def salones():
    return render_template("catalogos/salones.html", salones=_salones.listar(),
                           editando=request.args.get("editar", type=int))


@bp.post("/salones/<int:id_salon>")
@solo_gerente
def editar_salon(id_salon: int):
    try:
        _salones.actualizar(usuario_actual().id_usuario, id_salon, request.form)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        return redirect(url_for("catalogos.salones", editar=id_salon))
    flash("Salón actualizado.", "exito")
    return redirect(url_for("catalogos.salones"))


# ------------------------------- Platillos -----------------------------
@bp.get("/platillos")
@solo_gerente
def platillos():
    return render_template(
        "catalogos/platillos.html",
        grupos=agrupar_por_categoria(_platillos.listar()),
        categorias=CATEGORIAS_PLATILLO,
        editando=request.args.get("editar", type=int),
    )


@bp.post("/platillos")
@solo_gerente
def crear_platillo():
    try:
        _platillos.crear(request.form)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
    else:
        flash("Platillo agregado.", "exito")
    return redirect(url_for("catalogos.platillos"))


@bp.post("/platillos/<int:id_platillo>")
@solo_gerente
def editar_platillo(id_platillo: int):
    try:
        _platillos.actualizar(id_platillo, request.form)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        return redirect(url_for("catalogos.platillos", editar=id_platillo))
    flash("Platillo actualizado.", "exito")
    return redirect(url_for("catalogos.platillos"))


@bp.post("/platillos/<int:id_platillo>/eliminar")
@solo_gerente
def eliminar_platillo(id_platillo: int):
    try:
        _platillos.eliminar(id_platillo)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
    else:
        flash("Platillo eliminado.", "exito")
    return redirect(url_for("catalogos.platillos"))


# ------------------------------- Paquetes ------------------------------
@bp.get("/paquetes")
@solo_gerente
def paquetes():
    return render_template("catalogos/paquetes.html", paquetes=_paquetes.listar())


def _formulario_paquete(paquete=None, datos=None, seleccion=None, estado=200):
    return render_template(
        "catalogos/paquete_form.html",
        paquete=paquete,
        datos=datos or {},
        seleccion=set(seleccion or []),
        grupos=agrupar_por_categoria(_platillos.listar()),
        clientes=ServicioClientes().buscar(""),
        tipos=TIPOS_PAQUETE,
    ), estado


@bp.route("/paquetes/nuevo", methods=["GET", "POST"])
@solo_gerente
def nuevo_paquete():
    if request.method == "POST":
        seleccion = request.form.getlist("platillos")
        try:
            _paquetes.guardar(usuario_actual().id_usuario, request.form, seleccion)
        except ErrorDominio as error:
            flash(error.mensaje, "error")
            return _formulario_paquete(datos=request.form,
                                       seleccion=[int(i) for i in seleccion if i.isdigit()],
                                       estado=422)
        flash("Paquete creado.", "exito")
        return redirect(url_for("catalogos.paquetes"))
    return _formulario_paquete()


@bp.route("/paquetes/<int:id_paquete>", methods=["GET", "POST"])
@solo_gerente
def editar_paquete(id_paquete: int):
    try:
        paquete = _paquetes.obtener(id_paquete)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
        return redirect(url_for("catalogos.paquetes"))

    if request.method == "POST":
        seleccion = request.form.getlist("platillos")
        try:
            _paquetes.guardar(usuario_actual().id_usuario, request.form, seleccion, id_paquete)
        except ErrorDominio as error:
            flash(error.mensaje, "error")
            return _formulario_paquete(paquete, request.form,
                                       [int(i) for i in seleccion if i.isdigit()], 422)
        flash("Paquete actualizado.", "exito")
        return redirect(url_for("catalogos.paquetes"))

    datos = {"nombre": paquete.nombre, "precio_persona": paquete.precio_persona,
             "tipo": paquete.tipo, "id_cliente": paquete.id_cliente or ""}
    return _formulario_paquete(paquete, datos, [p.id_platillo for p in paquete.platillos])


@bp.post("/paquetes/<int:id_paquete>/eliminar")
@solo_gerente
def eliminar_paquete(id_paquete: int):
    try:
        _paquetes.eliminar(usuario_actual().id_usuario, id_paquete)
    except ErrorDominio as error:
        flash(error.mensaje, "error")
    else:
        flash("Paquete eliminado.", "exito")
    return redirect(url_for("catalogos.paquetes"))
