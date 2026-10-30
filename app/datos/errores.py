"""
Excepciones del dominio y traducción de errores de la base.

C-10 · Decisión DA-01 · RNF-12
Las reglas viven en PostgreSQL; aquí se convierte cada rechazo
(código BFnnn o restricción con nombre) en un mensaje comprensible para
un usuario no técnico. Las rutas solo conocen estas excepciones, nunca
las de psycopg.
"""
import logging

import psycopg
from psycopg import errors as pg

log = logging.getLogger(__name__)


class ErrorDominio(Exception):
    """Base de todos los errores que la interfaz puede mostrar."""

    def __init__(self, mensaje: str, codigo: str | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class ErrorNegocio(ErrorDominio):
    """La operación viola una regla de negocio (RN-xx)."""


class ErrorValidacion(ErrorDominio):
    """Los datos capturados están incompletos o mal formados."""


class ErrorNoEncontrado(ErrorDominio):
    """El registro solicitado no existe."""


class ErrorConexion(ErrorDominio):
    """No fue posible comunicarse con la base de datos."""


# Restricciones con nombre -> (código de regla, mensaje para el usuario)
_RESTRICCIONES = {
    "uq_usuario_correo":   ("BF007", "Ese correo ya pertenece a otro usuario."),
    "uq_usuario_telefono": ("BF007", "Ese número de celular ya pertenece a otro usuario."),
    "ck_usuario_contacto": ("BF006", "Captura al menos un dato de contacto: correo o celular."),
    "ck_paquete_dueno":    ("BF0012", "Un paquete personalizado necesita un cliente; uno estándar no puede tenerlo."),
    "uq_salon_nombre":     (None, "Ya existe un salón con ese nombre."),
    "uq_platillo_nombre":  (None, "Ya existe un platillo con ese nombre."),
    "ck_salon_capacidad":  (None, "La capacidad del salón debe ser mayor a cero."),
    "ck_salon_costo":      (None, "El costo de renta no puede ser negativo."),
    "ck_paquete_precio":   (None, "El precio por persona no puede ser negativo."),
    "fk_pp_platillo":      (None, "El platillo forma parte de uno o más paquetes. Quítalo de esos paquetes antes de eliminarlo."),
    "fk_paquete_cliente":  (None, "El cliente tiene paquetes personalizados asociados."),
    "fk_evento_paquete":   (None, "El paquete ya está contratado en uno o más eventos y no se puede eliminar."),
}


def traducir_error(error: psycopg.Error) -> ErrorDominio:
    """Convierte un error de psycopg en una excepción del dominio."""
    codigo = getattr(error, "sqlstate", None) or ""

    # 1) Reglas impuestas por triggers y procedimientos: RAISE ... ERRCODE 'BFnnn'.
    #    El mensaje ya viene redactado para el usuario y con los valores.
    if codigo.startswith("BF"):
        return ErrorNegocio(error.diag.message_primary, codigo)

    # 2) Restricciones declarativas con nombre (UNIQUE, CHECK, FK).
    restriccion = getattr(error.diag, "constraint_name", None)
    if restriccion in _RESTRICCIONES:
        codigo_regla, mensaje = _RESTRICCIONES[restriccion]
        return ErrorNegocio(mensaje, codigo_regla)

    # 3) Problemas de comunicación (instancia suspendida, red, credenciales).
    if isinstance(error, psycopg.OperationalError):
        log.warning("Falla de conexión con la base: %s", error)
        return ErrorConexion(
            "No fue posible comunicarse con la base de datos. "
            "Intenta de nuevo en unos segundos."
        )

    if isinstance(error, (pg.IntegrityError,)):
        log.error("Restricción sin traducción: %s (%s)", restriccion, error)
        return ErrorNegocio("La operación viola una regla de integridad de los datos.")

    log.exception("Error de base de datos no previsto")
    return ErrorDominio("Ocurrió un error al guardar la información. Intenta de nuevo.")
