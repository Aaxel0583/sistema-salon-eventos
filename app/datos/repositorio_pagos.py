"""
Repositorio de PAGO · C-10 · HU-009 · IB-06

El abono se registra con la función fn_registrar_pago de la base, que
valida el saldo (RN-05, BF005) y levanta el finiquito cuando el saldo
llega a cero (RN-10) en la misma invocación. Este repositorio no calcula
el saldo ni decide el finiquito (DA-01). La consulta de los abonos de un
evento está en RepositorioEventos.pagos, que comparten la ficha (IU-07) y
el portal del cliente (IU-10).
"""
from decimal import Decimal

from psycopg import Cursor


class RepositorioPagos:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    def registrar(self, id_evento: int, monto: Decimal, tipo: str, referencia: str | None) -> int:
        """RF-31, RF-32 · Devuelve el identificador del abono."""
        self._cur.execute(
            "SELECT fn_registrar_pago(%s, %s, %s, %s) AS id_pago",
            (id_evento, monto, tipo, referencia),
        )
        return self._cur.fetchone()["id_pago"]
