"""
Pruebas unitarias del Sprint 2 · Parte 2 (sin base de datos).
Traslape de horarios para pintar la agenda (RF-24, RF-27), respuesta de
/api/agenda y lectura de pagos para el portal (RF-40).
La regla que autoriza o rechaza está en la base (IB-02, IB-03) y se
prueba en test_disponibilidad.py.
"""
from datetime import date, datetime, time
from decimal import Decimal

import pytest

from app.dominio.modelos import Evento, Pago, Salon
from app.servicios.servicio_eventos import Agenda
from app.servicios.servicio_portal import EventosDelCliente

DIA = date(2027, 2, 14)


def _evento(inicio, fin, estado="CONFIRMADO", id_evento=1, dia=DIA):
    return Evento(id_evento=id_evento, clave_proyecto=f"EVT-2026-{id_evento:04d}", fecha_evento=dia,
                  hora_inicio=inicio, hora_fin=fin, num_asistentes=80, costo_total=Decimal("30000"),
                  estado=estado, id_cliente=7, nombre_cliente="Ana", id_salon=3,
                  nombre_salon="Salón Terraza", capacidad_maxima=90)


TERRAZA = Salon(id_salon=3, nombre="Salón Terraza", capacidad_maxima=90, costo_renta=Decimal("8000"))


class TestTraslape:
    @pytest.mark.parametrize("inicio, fin, esperado", [
        (time(20), time(23), True),          # CP-11: dentro de 19:00–23:59
        (time(18), time(19, 30), True),      # se encima por el inicio
        (time(17), time(23, 59), True),      # lo envuelve
        (time(8), time(13), False),          # CP-12: antes
        (time(17), time(19), False),         # contiguo: termina cuando el otro empieza (RF-27)
    ])
    def test_horarios(self, inicio, fin, esperado):
        assert _evento(time(19), time(23, 59)).se_traslapa(inicio, fin) is esperado

    def test_contiguo_por_el_final(self):
        assert not _evento(time(14), time(19)).se_traslapa(time(19), time(22))

    def test_un_cancelado_no_ocupa_el_salon(self):                         # RN-02
        cancelado = _evento(time(19), time(23), estado="CANCELADO")
        assert not cancelado.ocupa_salon and not cancelado.se_traslapa(time(20), time(22))

    def test_solo_el_anticipo_aparta_el_salon(self):                     # RN-02 · D-20
        for estado in ("CONFIRMADO", "REALIZADO"):
            assert _evento(time(19), time(23), estado=estado).se_traslapa(time(20), time(22))
        cotizacion = _evento(time(19), time(23), estado="COTIZACION")
        assert not cotizacion.ocupa_salon and not cotizacion.se_traslapa(time(20), time(22))
        assert cotizacion.coincide_con(time(20), time(22))


class TestAgenda:
    def test_sin_horario_no_hay_veredicto(self):
        agenda = Agenda(TERRAZA, DIA, [_evento(time(19), time(23, 59))])
        assert agenda.libre is None and agenda.traslapes == []
        assert agenda.como_dict()["libre"] is None

    def test_horario_invertido_tampoco_se_compara(self):
        agenda = Agenda(TERRAZA, DIA, [_evento(time(19), time(23))], time(22), time(20))
        assert agenda.libre is None

    def test_respuesta_de_la_ruta(self):
        ocupante, otro = _evento(time(19), time(23, 59)), _evento(time(8), time(12), id_evento=2)
        datos = Agenda(TERRAZA, DIA, [otro, ocupante], time(20), time(23)).como_dict()
        assert datos["libre"] is False
        assert datos["salon"] == {"id": 3, "nombre": "Salón Terraza", "capacidad": 90}
        assert datos["fecha"] == "2027-02-14" and datos["fecha_legible"] == "14/02/2027"
        assert [(e["clave"], e["inicio"], e["fin"], e["traslapa"]) for e in datos["eventos"]] == [
            ("EVT-2026-0002", "08:00", "12:00", False), ("EVT-2026-0001", "19:00", "23:59", True)]
        assert datos["eventos"][0]["titulo"] == "Evento de Ana" and datos["eventos"][0]["estado"] == "Confirmado"

    def test_dia_ocupado_con_horario_libre(self):
        assert Agenda(TERRAZA, DIA, [_evento(time(14), time(19))], time(8), time(13)).libre is True

    def test_cotizaciones_compiten_pero_no_ocupan(self):                 # D-20
        compite = _evento(time(19), time(23), estado="COTIZACION", id_evento=2)
        temprano = _evento(time(8), time(12), estado="COTIZACION", id_evento=3)
        agenda = Agenda(TERRAZA, DIA, [temprano, compite], time(20), time(22))
        assert agenda.libre is True and agenda.traslapes == [] and agenda.cotizaciones_encimadas == [compite]
        assert [(e["clave"], e["aparta"], e["traslapa"], e["compite"]) for e in agenda.como_dict()["eventos"]] == [
            ("EVT-2026-0003", False, False, False), ("EVT-2026-0002", False, False, True)]

    def test_dia_sin_eventos(self):
        assert Agenda(TERRAZA, DIA, [], time(8), time(13)).libre is True


class TestPortal:
    def test_tipo_de_pago_legible(self):
        pago = Pago(1, 1, Decimal("500"), "pago_inicial", datetime(2026, 11, 10, 12, 0))
        assert pago.tipo_legible == "Pago inicial"
        assert Pago(2, 1, Decimal("1"), "TRANSFERENCIA", datetime(2026, 11, 10)).tipo_legible == "Transferencia"

    def test_proximos_y_anteriores(self):
        hoy = date(2026, 11, 10)
        pasado = _evento(time(10), time(12), id_evento=1, dia=date(2026, 11, 9))
        de_hoy = _evento(time(10), time(12), id_evento=2, dia=hoy)
        lista = EventosDelCliente([de_hoy, pasado], hoy)
        assert lista.proximos == [de_hoy] and lista.anteriores == [pasado]      # el de hoy aún es próximo
