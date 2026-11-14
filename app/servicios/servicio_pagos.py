"""
Control financiero · C-05 · HU-009 · CU-08 · RF-31 a RF-34, RF-41
Escenario 6 (Figura 9) · Decisiones DA-01 y DA-05

Lo que este servicio NO hace (DA-01): calcular el saldo, decidir si el
abono cabe ni marcar el finiquito. La base valida el saldo (RN-05, BF005)
y levanta el finiquito (RN-10) en la misma invocación de IB-06. Aquí se
valida que el dato esté completo y bien formado, se registra la bitácora
y se informa el resultado.

D-20 · El anticipo es lo que aparta el salón. Al abonar a una cotización
el gerente puede confirmarla en el mismo paso; es una decisión suya,
marcada en el formulario, nunca un cambio automático (RN-14). El cambio
de estatus y el abono van en una sola transacción: si la base rechaza
cualquiera de los dos, no se guarda ninguno (RNF-08).
"""
from dataclasses import dataclass
from decimal import Decimal

from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorNegocio, ErrorNoEncontrado, ErrorValidacion
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_eventos import RepositorioEventos
from app.datos.repositorio_pagos import RepositorioPagos
from app.dominio.modelos import ESTADO_CONFIRMADO, FORMAS_PAGO, Evento
from app.servicios.validaciones import importe, texto_opcional

_MAX_REFERENCIA = 60        # columna pago.referencia


@dataclass
class PagoRegistrado:
    """Resultado de HU-009: el evento ya con su saldo nuevo y lo que provocó el abono."""
    evento: Evento
    monto: Decimal
    finiquito: bool = False         # el abono dejó el saldo en cero (RN-10)
    confirmado: bool = False        # el gerente confirmó la cotización en el mismo paso (D-20)


class ServicioPagos:

    formas_pago = FORMAS_PAGO

    def registrar(self, id_gerente: int, id_evento: int, formulario) -> PagoRegistrado:
        """RF-31 a RF-34 · Registra un abono indicando monto, tipo y referencia."""
        monto = importe(formulario.get("monto"), "Monto")
        if monto <= 0:
            raise ErrorValidacion("El monto del abono debe ser mayor a cero.")
        tipo = (formulario.get("tipo") or "").strip().upper()
        if tipo not in FORMAS_PAGO:
            raise ErrorValidacion("Elige la forma de pago del abono.")
        referencia = (formulario.get("referencia") or "").strip()
        if len(referencia) > _MAX_REFERENCIA:
            raise ErrorValidacion(f"El campo «Referencia» admite hasta {_MAX_REFERENCIA} caracteres.")
        referencia = texto_opcional(referencia, _MAX_REFERENCIA)
        confirmar = formulario.get("confirmar") == "S"

        with BaseDatos.transaccion() as cur:
            eventos, bitacora = RepositorioEventos(cur), RepositorioBitacora(cur)
            if not eventos.bloquear(id_evento):
                raise ErrorNoEncontrado("El evento no existe.")
            evento = eventos.por_id(id_evento)

            confirmado = False
            if confirmar and evento.puede_confirmarse_al_abonar(eventos.hoy()):
                motivo = evento.motivo_rechazo_estado(ESTADO_CONFIRMADO, eventos.hoy())
                if motivo:
                    raise ErrorNegocio(motivo)
                eventos.actualizar_estado(id_evento, ESTADO_CONFIRMADO)      # BF002 si el horario ya se apartó
                bitacora.registrar(id_gerente, "CAMBIO_ESTATUS", f"evento:{id_evento}:{ESTADO_CONFIRMADO}")
                confirmado = True

            id_pago = RepositorioPagos(cur).registrar(id_evento, monto, tipo, referencia)   # BF005
            bitacora.registrar(id_gerente, "REGISTRO_PAGO", f"evento:{id_evento}:pago:{id_pago}")

            actual = eventos.por_id(id_evento)
            finiquito = actual.esta_finiquitado and not evento.esta_finiquitado
            if finiquito:
                # Lo asignó la base, no el gerente: en la bitácora queda a nombre del sistema.
                bitacora.registrar(None, "FINIQUITO", f"evento:{id_evento}")
            return PagoRegistrado(actual, monto, finiquito, confirmado)
