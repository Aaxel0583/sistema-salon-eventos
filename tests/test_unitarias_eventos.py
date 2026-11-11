"""
Pruebas unitarias del Sprint 2 · Parte 1 (sin base de datos).
Ciclo de vida del evento (SDD §5.3, RN-11, RN-14), ocupación (IB-10) y
validación de la captura de IU-06.
"""
from datetime import date, time, timedelta
from decimal import Decimal

import pytest

from app.datos.errores import ErrorValidacion
from app.dominio.modelos import Evento, OcupacionSalon
from app.servicios.servicio_eventos import ServicioReservaciones
from app.servicios.validaciones import fecha, hora, id_seleccionado

HOY = date(2026, 11, 6)


def _evento(estado="COTIZACION", dias=10, **extra):
    datos = dict(id_evento=1, clave_proyecto="EVT-2026-0001", fecha_evento=HOY + timedelta(days=dias),
                 hora_inicio=time(19), hora_fin=time(23, 30), num_asistentes=100,
                 costo_total=Decimal("46000"), estado=estado, id_cliente=7, nombre_cliente="Ana",
                 id_salon=1, nombre_salon="Salón Principal", capacidad_maxima=250)
    datos.update(extra)
    return Evento(**datos)


class TestCicloDeVida:
    def test_cotizacion_futura_puede_confirmarse_o_cancelarse(self):
        assert _evento("COTIZACION", 10).estados_siguientes(HOY) == ["CONFIRMADO", "CANCELADO"]

    def test_no_se_marca_realizado_antes_de_la_fecha(self):
        evento = _evento("CONFIRMADO", 10)
        assert "REALIZADO" not in evento.estados_siguientes(HOY)
        assert "antes de su fecha" in evento.motivo_rechazo_estado("REALIZADO", HOY)

    def test_el_mismo_dia_ya_puede_marcarse_realizado(self):
        assert "REALIZADO" in _evento("CONFIRMADO", 0).estados_siguientes(HOY)

    def test_pendiente_de_cierre_ofrece_realizado_o_cancelado(self):     # IB-11 · RN-14
        for estado in ("COTIZACION", "CONFIRMADO"):
            evento = _evento(estado, -3)
            assert evento.pendiente_de_cierre(HOY)
            assert evento.estados_siguientes(HOY) == ["REALIZADO", "CANCELADO"]

    def test_cotizacion_vencida_no_se_confirma(self):
        assert "ya pasó" in _evento("COTIZACION", -1).motivo_rechazo_estado("CONFIRMADO", HOY)

    @pytest.mark.parametrize("estado", ["REALIZADO", "CANCELADO"])
    def test_estados_finales_no_tienen_salida(self, estado):
        evento = _evento(estado, -3)
        assert evento.estados_siguientes(HOY) == []
        assert not evento.pendiente_de_cierre(HOY)
        assert "cerró su ciclo" in evento.motivo_rechazo_estado("COTIZACION", HOY)

    def test_mismo_estatus_se_explica(self):
        assert "ya está en estatus Cotización" in _evento().motivo_rechazo_estado("COTIZACION", HOY)

    def test_titulo_sin_nombre_de_evento(self):
        assert _evento().titulo == "Evento de Ana"
        assert _evento(nombre_evento="Boda Robles").titulo == "Boda Robles"
        assert _evento().horario == "19:00 a 23:30"


class TestOcupacion:
    def test_porcentaje_acotado_y_umbral(self):
        alta = OcupacionSalon(1, "Terraza", 90, 2, 88, 95)
        assert alta.es_alta and alta.porcentaje == 95
        assert OcupacionSalon(1, "X", 90, 1, 200, 130).porcentaje == 100
        assert not OcupacionSalon(1, "X", 90, 1, 72, 80).es_alta


class TestCapturaReservacion:
    BASE = {"id_salon": "1", "id_paquete": "2", "fecha_evento": "2027-01-20",
            "hora_inicio": "19:00", "hora_fin": "23:30", "num_asistentes": "120"}

    def test_captura_valida(self):
        captura = ServicioReservaciones._validar_captura(self.BASE)
        assert captura.fecha_evento == date(2027, 1, 20)
        assert captura.hora_inicio == time(19) and captura.num_asistentes == 120
        assert captura.nombre_evento is None

    @pytest.mark.parametrize("campo, valor, mensaje", [
        ("id_salon", "", "Elige un valor en «Salón»"),
        ("id_paquete", "", "Elige un valor en «Paquete»"),
        ("fecha_evento", "31/02/2027", "fecha válida"),
        ("hora_inicio", "7 pm", "formato de 24 horas"),
        ("num_asistentes", "0", "mayor a cero"),
        ("num_asistentes", "cien", "número entero"),
    ])
    def test_campos_invalidos(self, campo, valor, mensaje):
        with pytest.raises(ErrorValidacion, match=mensaje):
            ServicioReservaciones._validar_captura({**self.BASE, campo: valor})

    @pytest.mark.parametrize("inicio, fin", [("23:00", "19:00"), ("19:00", "19:00")])
    def test_termino_posterior_al_inicio(self, inicio, fin):
        with pytest.raises(ErrorValidacion, match="debe ser posterior"):
            ServicioReservaciones._validar_captura({**self.BASE, "hora_inicio": inicio, "hora_fin": fin})


class TestValidadores:
    def test_fecha_en_dos_formatos(self):
        assert fecha("2026-12-24", "Fecha") == fecha("24/12/2026", "Fecha") == date(2026, 12, 24)

    def test_hora_descarta_segundos(self):
        assert hora("19:30:45", "Inicio") == time(19, 30)

    def test_seleccion_vacia(self):
        with pytest.raises(ErrorValidacion, match="Elige un valor en «Cliente»"):
            id_seleccionado("", "Cliente")
