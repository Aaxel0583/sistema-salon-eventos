"""
Sprint 3 · Pruebas unitarias (sin base de datos) de pagos y reportes:
presentación del saldo, del semáforo y del archivo CSV (RF-38, IE-02).
"""
import csv
import io
from datetime import date, datetime, time
from decimal import Decimal

from app.dominio.modelos import CuentaCartera, Evento, Pago, ProyectoActivo
from app.servicios.servicio_reportes import (FECHA, MONEDA, Columna, Reporte, _COLUMNAS_ACTIVOS,
                                             _COLUMNAS_CARTERA, _COLUMNAS_REALIZADOS, _texto_seguro)

HOY = date(2026, 11, 11)


def _evento(clase=Evento, **cambios):
    datos = dict(id_evento=1, clave_proyecto="EVT-2026-0001", fecha_evento=date(2026, 12, 5),
                 hora_inicio=time(14), hora_fin=time(19), num_asistentes=60, costo_total=Decimal("20000"),
                 estado="CONFIRMADO", id_cliente=2, nombre_cliente="Ana Ruiz", id_salon=3,
                 nombre_salon="Salón Terraza", capacidad_maxima=90, total_pagado=Decimal("5000"),
                 saldo=Decimal("15000"), correo_cliente="ana@correo.mx")
    datos.update(cambios)
    return clase(**datos)


class TestCobro:
    def test_admite_pagos_mientras_haya_saldo_y_no_este_cancelado(self):
        assert _evento().admite_pagos
        assert _evento(estado="COTIZACION").admite_pagos and _evento(estado="REALIZADO").admite_pagos
        assert not _evento(estado="CANCELADO").admite_pagos
        assert not _evento(saldo=Decimal("0"), finiquitado="S").admite_pagos

    def test_solo_una_cotizacion_vigente_se_confirma_al_abonar(self):
        assert _evento(estado="COTIZACION").puede_confirmarse_al_abonar(HOY)
        assert not _evento(estado="CONFIRMADO").puede_confirmarse_al_abonar(HOY)
        assert not _evento(estado="COTIZACION", fecha_evento=date(2026, 11, 1)).puede_confirmarse_al_abonar(HOY)

    def test_anticipo_sin_confirmar(self):
        assert _evento(estado="COTIZACION").tiene_anticipo_sin_confirmar
        assert not _evento(estado="COTIZACION", total_pagado=Decimal("0")).tiene_anticipo_sin_confirmar
        assert not _evento().tiene_anticipo_sin_confirmar

    def test_forma_de_pago_legible(self):
        assert Pago(1, 1, Decimal("1"), "DEPOSITO", datetime(2026, 11, 11)).tipo_legible == "Depósito"
        assert Pago(1, 1, Decimal("1"), "pago_inicial", datetime(2026, 11, 11)).tipo_legible == "Pago inicial"


class TestCartera:
    def test_plazo_en_palabras(self):
        casos = {-3: "Hace 3 días", -1: "Hace 1 día", 0: "Hoy", 1: "En 1 día", 21: "En 21 días"}
        for dias, texto in casos.items():
            assert _evento(CuentaCartera, dias_para_evento=dias).plazo == texto

    def test_semaforo_legible(self):
        assert _evento(CuentaCartera, semaforo="PROXIMA").semaforo_legible == "Próxima a vencer"

    def test_aforo_de_proyecto_activo(self):
        assert _evento(ProyectoActivo, porcentaje_aforo=67).aforo == "60 de 90"


class TestCsv:
    def _reporte(self, columnas, filas):
        return Reporte("cartera", "Cartera", "", columnas, filas, [], HOY)

    def test_columnas_y_formatos(self):
        fila = _evento(CuentaCartera, dias_para_evento=24, semaforo="VIGENTE")
        lineas = list(csv.reader(io.StringIO(self._reporte(_COLUMNAS_CARTERA, [fila]).a_csv())))
        assert lineas[0] == ["Clave", "Cliente", "Contacto", "Salón", "Fecha del evento", "Plazo",
                             "Pagado", "Saldo", "Semáforo"]
        assert lineas[1] == ["EVT-2026-0001", "Ana Ruiz", "ana@correo.mx", "Salón Terraza", "05/12/2026",
                             "En 24 días", "5000.00", "15000.00", "Vigente"]

    def test_importes_sin_simbolo_ni_miles_para_poder_sumarlos(self):
        columna = Columna("Costo", lambda e: e.costo_total, MONEDA)
        reporte = self._reporte([columna], [])
        assert reporte.celda_csv(columna, _evento(costo_total=Decimal("1234567.5"))) == "1234567.50"

    def test_fecha_y_valor_vacio(self):
        reporte = self._reporte([], [])
        assert reporte.celda_csv(Columna("F", lambda e: e.fecha_evento, FECHA), _evento()) == "05/12/2026"
        assert reporte.celda_csv(Columna("X", lambda e: None), _evento()) == ""

    def test_comas_comillas_y_saltos_quedan_en_su_celda(self):
        fila = _evento(CuentaCartera, nombre_cliente='Ruiz, "La Güera"\nS.A.')
        lineas = list(csv.reader(io.StringIO(self._reporte(_COLUMNAS_CARTERA, [fila]).a_csv())))
        assert len(lineas) == 2 and lineas[1][1] == 'Ruiz, "La Güera"\nS.A.'

    def test_texto_que_parece_formula_se_neutraliza(self):
        for peligroso in ("=1+1", "+52 492", "-10", "@SUM(A1)"):
            assert _texto_seguro(peligroso) == "'" + peligroso
        assert _texto_seguro("Ana") == "Ana" and _texto_seguro("") == ""

    def test_nombre_del_archivo(self):
        assert self._reporte([], []).nombre_archivo == "cartera_2026-11-11.csv"

    def test_cada_reporte_abre_con_la_clave_y_cierra_con_su_etiqueta(self):
        for columnas in (_COLUMNAS_CARTERA, _COLUMNAS_ACTIVOS, _COLUMNAS_REALIZADOS):
            assert columnas[0].papel == "titulo" and columnas[-1].papel == "estado"
            assert len({c.titulo for c in columnas}) == len(columnas)
