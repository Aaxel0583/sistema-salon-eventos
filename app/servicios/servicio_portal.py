"""
Portal del cliente.

C-07 Portal del cliente · HU-008 · CU-10 · RF-39, RF-40 · RNF-06
Escenario 7 (Figura 10) · IU-09 e IU-10

El identificador del titular llega SIEMPRE desde la sesión (C-01), nunca
desde la petición: es lo que impide que un cliente consulte el evento de
otro escribiendo su clave en la dirección. El filtro por titular se
aplica en la consulta, de modo que un evento ajeno y uno inexistente
producen exactamente la misma respuesta.

El portal es de solo lectura: no ofrece ninguna operación de cambio.
"""
import re
from dataclasses import dataclass
from datetime import date

from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorNoEncontrado
from app.datos.repositorio_catalogos import RepositorioPaquetes
from app.datos.repositorio_eventos import RepositorioEventos
from app.dominio.modelos import Evento, Pago, Paquete

_PATRON_CLAVE = re.compile(r"EVT-\d{4}-\d{4}")       # RN-08
_NO_ES_TUYO = "No encontramos ese evento entre los tuyos."


@dataclass
class EventosDelCliente:
    """Contenido de IU-09."""
    eventos: list[Evento]
    hoy: date

    @property
    def proximos(self) -> list[Evento]:
        return [e for e in self.eventos if e.fecha_evento >= self.hoy]

    @property
    def anteriores(self) -> list[Evento]:
        return [e for e in self.eventos if e.fecha_evento < self.hoy]


@dataclass
class DetalleDelCliente:
    """Contenido de IU-10: resumen del evento, menú, pagos y saldo (RF-40)."""
    evento: Evento
    paquete: Paquete | None
    pagos: list[Pago]
    hoy: date


class ServicioPortal:

    def mis_eventos(self, id_titular: int) -> EventosDelCliente:
        """RF-39 · Solo los eventos de los que el cliente autenticado es titular."""
        with BaseDatos.transaccion() as cur:
            eventos = RepositorioEventos(cur)
            return EventosDelCliente(eventos.de_cliente(id_titular), eventos.hoy())

    def detalle(self, id_titular: int, clave_proyecto: str) -> DetalleDelCliente:
        """
        RF-40 · Detalle de un evento propio. Si la clave no existe o es de
        otro cliente se responde lo mismo, sin revelar cuál de las dos cosas
        ocurrió (RNF-06).
        """
        clave = (clave_proyecto or "").strip().upper()
        if not _PATRON_CLAVE.fullmatch(clave):
            raise ErrorNoEncontrado(_NO_ES_TUYO)
        with BaseDatos.transaccion() as cur:
            eventos = RepositorioEventos(cur)
            evento = eventos.por_clave_de_cliente(clave, id_titular)
            if evento is None:
                raise ErrorNoEncontrado(_NO_ES_TUYO)
            paquete = RepositorioPaquetes(cur).por_id(evento.id_paquete) if evento.id_paquete else None
            return DetalleDelCliente(evento, paquete, eventos.pagos(evento.id_evento), eventos.hoy())
