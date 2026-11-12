"""
Sprint 3 · Control financiero (HU-009, CU-08).
Casos del SRS Anexo C:
  CP-14 · registro de pago y finiquito automático (RF-31, RF-33, RF-34, RN-10)
  CP-15 · rechazo de pago excedido con BF005 (RF-32, RN-05)
  CP-23 · bitácora del pago y del cambio de estatus (RF-41, RNF-18)
Además: las reglas se cumplen por SQL directo (DA-01, RNF-09), dos abonos
simultáneos no rebasan el saldo y el anticipo confirma la cotización (D-20).
"""
import threading
from decimal import Decimal

import psycopg
import pytest

from app.datos.conexion import BaseDatos
from app.datos.repositorio_eventos import RepositorioEventos
from tests.conftest import fecha_libre

pytestmark = pytest.mark.integracion


# ------------------------------- apoyo -------------------------------
def _entrar(http, identificador, clave):
    return http.post("/login", data={"identificador": identificador, "clave": clave})


@pytest.fixture
def gerente(cliente_http, crear_usuario):
    id_gerente, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    return id_gerente


def _evento(id_evento):
    with BaseDatos.transaccion() as cur:
        return RepositorioEventos(cur).por_id(id_evento)


def _nuevo_evento(id_cliente, estado="CONFIRMADO", dia=None, asistentes=50, id_salon=3):
    """Un evento confirmado en la Terraza con el paquete 1 y 50 invitados, salvo que se indique otro."""
    with BaseDatos.transaccion() as cur:
        repo = RepositorioEventos(cur)
        id_evento = repo.insertar(id_cliente, None, id_salon, 1, "Evento de prueba", dia or fecha_libre(),
                                  "14:00", "19:00", asistentes)
        if estado != "COTIZACION":
            repo.actualizar_estado(id_evento, estado)
        return repo.por_id(id_evento)


def _abonar(http, evento, monto, tipo="TRANSFERENCIA", referencia="", **extra):
    return http.post(f"/eventos/{evento.id_evento}/pagos",
                     data={"monto": str(monto), "tipo": tipo, "referencia": referencia, **extra})


def _bitacora(patron):
    with BaseDatos.transaccion() as cur:
        cur.execute("""SELECT b.accion, b.entidad, b.id_usuario, b.fecha FROM bitacora b
                        WHERE b.entidad LIKE %s ORDER BY b.id_bitacora""", (patron,))
        return cur.fetchall()


@pytest.fixture
def evento(crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    return _nuevo_evento(id_cliente)


# ------------------------------ CP-14 ------------------------------
def test_cp14_abono_parcial_recalcula_el_saldo(cliente_http, gerente, evento):
    """RF-31, RF-33: el abono queda con monto, tipo y referencia, y el saldo es costo − pagos."""
    respuesta = _abonar(cliente_http, evento, "5000.50", "TRANSFERENCIA", "SPEI 4471")
    assert respuesta.status_code == 302 and respuesta.location.endswith(f"/eventos/{evento.id_evento}#pagos")

    actual = _evento(evento.id_evento)
    assert actual.total_pagado == Decimal("5000.50")
    assert actual.saldo == evento.costo_total - Decimal("5000.50")
    assert actual.finiquitado == "N" and actual.fecha_finiquito is None

    ficha = cliente_http.get(f"/eventos/{evento.id_evento}").get_data(as_text=True)
    assert "Abono de $5,000.50 registrado" in ficha and f"Saldo pendiente: ${actual.saldo:,.2f}." in ficha
    assert "Transferencia" in ficha and "SPEI 4471" in ficha and "$5,000.50" in ficha
    assert "1 abono" in ficha


def test_cp14_pago_exacto_finiquita_con_fecha(cliente_http, gerente, evento):
    """RF-34, RN-10: al cubrir exactamente el saldo, el sistema marca el finiquito con su fecha."""
    _abonar(cliente_http, evento, "8000", "EFECTIVO")
    _abonar(cliente_http, evento, evento.costo_total - 8000, "TARJETA", "Terminal 0091")

    actual = _evento(evento.id_evento)
    with BaseDatos.transaccion() as cur:
        hoy = RepositorioEventos(cur).hoy()
    assert actual.saldo == 0 and actual.finiquitado == "S" and actual.fecha_finiquito == hoy
    assert actual.estado == "CONFIRMADO"                       # RN-11: el finiquito no mueve el estatus

    ficha = cliente_http.get(f"/eventos/{evento.id_evento}").get_data(as_text=True)
    assert "el evento quedó finiquitado" in ficha and f"Finiquitado el {hoy:%d/%m/%Y}" in ficha
    assert 'name="monto"' not in ficha                         # ya no hay captura de abono
    assert 'name="finiquitado"' not in ficha                   # IU-07: el finiquito no es editable


def test_ficha_ofrece_abono_y_no_permite_editar_el_finiquito(cliente_http, gerente, evento):
    ficha = cliente_http.get(f"/eventos/{evento.id_evento}").get_data(as_text=True)
    assert f'action="/eventos/{evento.id_evento}/pagos"' in ficha
    assert f'data-saldo="{evento.saldo:.2f}"' in ficha and "Aún no hay pagos registrados." in ficha
    for forma in ("Efectivo", "Transferencia", "Tarjeta", "Depósito", "Cheque"):
        assert f">{forma}</option>" in ficha
    assert "finiquitado" not in ficha.split('id="pagos"')[1].split("<form")[1].split("</form>")[0].lower()


# ------------------------------ CP-15 ------------------------------
def test_cp15_pago_excedido_se_rechaza_con_bf005(cliente_http, gerente, evento):
    """RF-32, RN-05: un abono mayor al saldo no se guarda y el mensaje trae los valores (RNF-12)."""
    excedido = evento.saldo + Decimal("0.01")
    respuesta = _abonar(cliente_http, evento, excedido, "CHEQUE", "Cheque 118")
    texto = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 422
    assert f"El abono de ${excedido:,.2f} excede el saldo pendiente de ${evento.saldo:,.2f}" in texto
    assert evento.clave_proyecto in texto and "BF005" not in texto          # sin códigos para el usuario
    assert f'value="{excedido}"' in texto and 'value="Cheque 118"' in texto  # no se pierde lo capturado
    assert '<option value="CHEQUE" selected>' in texto
    assert _evento(evento.id_evento).total_pagado == 0                       # sin rastro


def test_cp15_la_base_responde_bf005(conexion, evento):
    with pytest.raises(psycopg.Error) as error:
        conexion.execute("SELECT fn_registrar_pago(%s, %s, 'EFECTIVO', NULL)",
                         (evento.id_evento, evento.costo_total + 1))
    assert error.value.sqlstate == "BF005"


@pytest.mark.parametrize("datos, mensaje", [
    ({"monto": "", "tipo": "EFECTIVO"}, "debe ser un importe válido"),
    ({"monto": "0", "tipo": "EFECTIVO"}, "debe ser mayor a cero"),
    ({"monto": "-50", "tipo": "EFECTIVO"}, "no puede ser negativo"),
    ({"monto": "abc", "tipo": "EFECTIVO"}, "debe ser un importe válido"),
    ({"monto": "100", "tipo": ""}, "Elige la forma de pago"),
    ({"monto": "100", "tipo": "BITCOIN"}, "Elige la forma de pago"),
    ({"monto": "100", "tipo": "EFECTIVO", "referencia": "x" * 61}, "admite hasta 60 caracteres"),
])
def test_abono_mal_capturado_no_se_guarda(cliente_http, gerente, evento, datos, mensaje):
    respuesta = cliente_http.post(f"/eventos/{evento.id_evento}/pagos", data=datos)
    assert respuesta.status_code == 422 and mensaje in respuesta.get_data(as_text=True)
    assert _evento(evento.id_evento).total_pagado == 0


def test_importe_con_formato_de_miles(cliente_http, gerente, evento):
    _abonar(cliente_http, evento, "$1,500.00", "EFECTIVO")
    assert _evento(evento.id_evento).total_pagado == Decimal("1500.00")


def test_evento_cancelado_no_admite_abonos(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    cancelado = _nuevo_evento(id_cliente, estado="CANCELADO")
    respuesta = _abonar(cliente_http, cancelado, "100", "EFECTIVO")
    assert respuesta.status_code == 422
    assert f"El evento {cancelado.clave_proyecto} está cancelado y no admite abonos." in respuesta.get_data(as_text=True)
    ficha = cliente_http.get(f"/eventos/{cancelado.id_evento}").get_data(as_text=True)
    assert 'name="monto"' not in ficha and "no admite abonos" in ficha


def test_evento_liquidado_no_admite_mas_abonos(cliente_http, gerente, evento):
    _abonar(cliente_http, evento, evento.costo_total, "EFECTIVO")
    respuesta = _abonar(cliente_http, evento, "1", "EFECTIVO")
    assert respuesta.status_code == 422 and "ya está liquidado" in respuesta.get_data(as_text=True)
    assert _evento(evento.id_evento).total_pagado == evento.costo_total


def test_abono_a_evento_inexistente(cliente_http, gerente):
    respuesta = cliente_http.post("/eventos/99999999/pagos", data={"monto": "10", "tipo": "EFECTIVO"})
    assert respuesta.status_code == 302 and respuesta.location.endswith("/eventos")


def test_rf05_cliente_no_registra_pagos(cliente_http, crear_usuario, evento):
    _, correo, clave = crear_usuario("CLIENTE")
    _entrar(cliente_http, correo, clave)
    respuesta = _abonar(cliente_http, evento, "100", "EFECTIVO")
    assert respuesta.status_code == 302 and respuesta.location.endswith("/mis-eventos")
    assert _evento(evento.id_evento).total_pagado == 0


def test_sin_sesion_no_se_registran_pagos(cliente_http, evento):
    respuesta = _abonar(cliente_http, evento, "100", "EFECTIVO")
    assert respuesta.status_code == 302 and "/login" in respuesta.location
    assert _evento(evento.id_evento).total_pagado == 0


# ------------------------------ CP-23 ------------------------------
def test_cp23_bitacora_de_pago_y_de_estatus(cliente_http, gerente, crear_usuario):
    """RF-41, RNF-18: usuario, acción, entidad y fecha del pago y del cambio de estatus."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    evento = _nuevo_evento(id_cliente, estado="COTIZACION")
    cliente_http.post(f"/eventos/{evento.id_evento}/estado", data={"estado": "CONFIRMADO"})
    _abonar(cliente_http, evento, "2500", "EFECTIVO")

    filas = _bitacora(f"evento:{evento.id_evento}%")
    acciones = [f["accion"] for f in filas]
    assert acciones == ["CAMBIO_ESTATUS", "REGISTRO_PAGO"]
    assert all(f["id_usuario"] == gerente and f["fecha"] is not None for f in filas)
    assert filas[0]["entidad"] == f"evento:{evento.id_evento}:CONFIRMADO"
    assert filas[1]["entidad"].startswith(f"evento:{evento.id_evento}:pago:")

    # La interfaz no ofrece forma de borrar ni de editar la bitácora ni los abonos.
    panel = cliente_http.get("/panel").get_data(as_text=True)
    assert "Registro de pago" in panel and "Cambio de estatus de evento" in panel
    actividad = panel.split('id="t-actividad"')[1].split("</section>")[0]
    assert "<form" not in actividad and "<button" not in actividad            # solo lectura
    for ruta in ("/bitacora", f"/eventos/{evento.id_evento}/pagos/1/eliminar"):
        assert cliente_http.post(ruta).status_code in (404, 405)
    from app.datos.errores import ErrorDominio
    with pytest.raises(ErrorDominio), BaseDatos.transaccion() as cur:
        cur.execute("DELETE FROM bitacora WHERE entidad LIKE %s", (f"evento:{evento.id_evento}%",))


def test_cp23_el_finiquito_queda_en_bitacora_a_nombre_del_sistema(cliente_http, gerente, evento):
    _abonar(cliente_http, evento, evento.costo_total, "TRANSFERENCIA")
    filas = _bitacora(f"evento:{evento.id_evento}%")
    assert [f["accion"] for f in filas] == ["REGISTRO_PAGO", "FINIQUITO"]
    assert filas[0]["id_usuario"] == gerente and filas[1]["id_usuario"] is None


def test_abono_rechazado_no_deja_bitacora(cliente_http, gerente, evento):
    """RNF-08: si la base rechaza el abono, tampoco queda su registro en bitácora."""
    _abonar(cliente_http, evento, evento.costo_total + 5, "EFECTIVO")
    assert _bitacora(f"evento:{evento.id_evento}%") == []


# ----------------------- D-20 · el anticipo confirma -----------------------
def test_anticipo_confirma_la_cotizacion_en_el_mismo_paso(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    cotizacion = _nuevo_evento(id_cliente, estado="COTIZACION")
    ficha = cliente_http.get(f"/eventos/{cotizacion.id_evento}").get_data(as_text=True)
    assert 'name="confirmar" value="S" checked' in ficha

    _abonar(cliente_http, cotizacion, "3000", "EFECTIVO", confirmar="S")
    actual = _evento(cotizacion.id_evento)
    assert actual.estado == "CONFIRMADO" and actual.total_pagado == 3000
    assert [f["accion"] for f in _bitacora(f"evento:{cotizacion.id_evento}%")] == ["CAMBIO_ESTATUS", "REGISTRO_PAGO"]
    ficha = cliente_http.get(f"/eventos/{cotizacion.id_evento}").get_data(as_text=True)
    assert "El evento quedó confirmado y aparta su horario." in ficha
    assert 'name="confirmar"' not in ficha                     # ya confirmado: la casilla desaparece


def test_abono_sin_confirmar_deja_la_cotizacion_y_lo_advierte(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    cotizacion = _nuevo_evento(id_cliente, estado="COTIZACION")
    _abonar(cliente_http, cotizacion, "3000", "EFECTIVO")          # casilla sin marcar
    assert _evento(cotizacion.id_evento).estado == "COTIZACION"
    ficha = cliente_http.get(f"/eventos/{cotizacion.id_evento}").get_data(as_text=True)
    assert "ya tiene abonos y sigue en cotización" in ficha


def test_anticipo_a_horario_ya_apartado_no_guarda_nada(cliente_http, gerente, crear_usuario):
    """RNF-08 · BF002: si el horario ya lo apartó otro evento, ni se confirma ni se cobra."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    dia = fecha_libre()
    tardia = _nuevo_evento(id_cliente, estado="COTIZACION", dia=dia)
    ganadora = _nuevo_evento(id_cliente, estado="COTIZACION", dia=dia)
    cliente_http.post(f"/eventos/{ganadora.id_evento}/estado", data={"estado": "CONFIRMADO"})

    respuesta = _abonar(cliente_http, tardia, "3000", "EFECTIVO", confirmar="S")
    assert respuesta.status_code == 422
    assert f"por el evento {ganadora.clave_proyecto}, que ya dio anticipo" in respuesta.get_data(as_text=True)
    actual = _evento(tardia.id_evento)
    assert actual.estado == "COTIZACION" and actual.total_pagado == 0
    assert _bitacora(f"evento:{tardia.id_evento}%") == []


# ------------------- DA-01 · las reglas viven en la base -------------------
def test_pago_excedido_por_sql_directo(conexion, evento):
    """RNF-09: el INSERT directo, sin pasar por la aplicación ni por fn_registrar_pago, también se rechaza."""
    with pytest.raises(psycopg.Error) as error:
        conexion.execute("INSERT INTO pago (id_evento, monto, tipo) VALUES (%s, %s, 'EFECTIVO')",
                         (evento.id_evento, evento.costo_total + 1))
    assert error.value.sqlstate == "BF005"
    assert "excede el saldo pendiente" in error.value.diag.message_primary


def test_finiquito_automatico_por_sql_directo(conexion, evento):
    conexion.execute("INSERT INTO pago (id_evento, monto, tipo) VALUES (%s, %s, 'EFECTIVO')",
                     (evento.id_evento, evento.costo_total))
    fila = conexion.execute("SELECT finiquitado, fecha_finiquito, CURRENT_DATE AS hoy FROM evento WHERE id_evento = %s",
                            (evento.id_evento,)).fetchone()
    assert fila["finiquitado"] == "S" and fila["fecha_finiquito"] == fila["hoy"]


def test_rn10_el_finiquito_no_se_marca_a_mano(conexion, evento):
    with pytest.raises(psycopg.Error) as error:
        conexion.execute("UPDATE evento SET finiquitado = 'S' WHERE id_evento = %s", (evento.id_evento,))
    assert error.value.sqlstate == "BF010" and "lo asigna el sistema" in error.value.diag.message_primary


def test_rn10_el_finiquito_no_se_retira(conexion, evento):
    conexion.execute("SELECT fn_registrar_pago(%s, %s, 'EFECTIVO')", (evento.id_evento, evento.costo_total))
    for sentencia in ("UPDATE evento SET finiquitado = 'N' WHERE id_evento = %s",
                      "UPDATE evento SET fecha_finiquito = CURRENT_DATE - 5 WHERE id_evento = %s",
                      "UPDATE evento SET num_asistentes = num_asistentes - 1 WHERE id_evento = %s"):
        with pytest.raises(psycopg.Error) as error, conexion.transaction():
            conexion.execute(sentencia, (evento.id_evento,))
        assert error.value.sqlstate == "BF010", sentencia


def test_evento_nace_sin_finiquito_aunque_el_insert_lo_pida(conexion, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    fila = conexion.execute(
        """INSERT INTO evento (clave_proyecto, id_cliente, id_salon, id_paquete, fecha_evento, hora_inicio,
                               hora_fin, num_asistentes, costo_total, finiquitado, fecha_finiquito)
           VALUES ('X', %s, 3, 1, %s, '08:00', '09:00', 10, 0, 'S', CURRENT_DATE)
           RETURNING finiquitado, fecha_finiquito""", (id_cliente, fecha_libre())).fetchone()
    assert fila["finiquitado"] == "N" and fila["fecha_finiquito"] is None


def test_un_abono_no_se_modifica_ni_se_elimina(conexion, evento):
    conexion.execute("SELECT fn_registrar_pago(%s, 1000, 'EFECTIVO')", (evento.id_evento,))
    for sentencia in ("UPDATE pago SET monto = 999999 WHERE id_evento = %s",
                      "DELETE FROM pago WHERE id_evento = %s",
                      "DELETE FROM evento WHERE id_evento = %s"):          # borrado en cascada
        with pytest.raises(psycopg.Error) as error, conexion.transaction():
            conexion.execute(sentencia, (evento.id_evento,))
        assert error.value.sqlstate == "BF005", sentencia


def test_el_costo_no_baja_de_lo_pagado(conexion, evento):
    conexion.execute("SELECT fn_registrar_pago(%s, 17000, 'EFECTIVO')", (evento.id_evento,))
    with pytest.raises(psycopg.Error) as error, conexion.transaction():
        conexion.execute("UPDATE evento SET num_asistentes = 10 WHERE id_evento = %s", (evento.id_evento,))
    assert error.value.sqlstate == "BF005" and "ya tiene $17,000.00 pagados" in error.value.diag.message_primary
    conexion.execute("UPDATE evento SET num_asistentes = 49 WHERE id_evento = %s", (evento.id_evento,))   # 17,760: cabe


def test_bf010_se_presenta_con_el_codigo_del_srs(evento):
    from app.datos.errores import ErrorNegocio
    with pytest.raises(ErrorNegocio) as error, BaseDatos.transaccion() as cur:
        cur.execute("UPDATE evento SET finiquitado = 'S' WHERE id_evento = %s", (evento.id_evento,))
    assert error.value.codigo == "BF0010"


def test_dos_abonos_simultaneos_no_rebasan_el_saldo(base_pruebas, evento):
    """Dos cajas cobran el total al mismo tiempo: solo una lo logra (candado sobre el evento)."""
    barrera, resultados = threading.Barrier(2), []

    def cobrar():
        with psycopg.connect(base_pruebas) as con:
            barrera.wait()
            try:
                con.execute("SELECT fn_registrar_pago(%s, %s, 'EFECTIVO')", (evento.id_evento, evento.costo_total))
                con.commit()
                resultados.append("ok")
            except psycopg.Error as error:
                resultados.append(error.sqlstate)

    hilos = [threading.Thread(target=cobrar) for _ in range(2)]
    [h.start() for h in hilos]
    [h.join() for h in hilos]
    assert sorted(resultados) == ["BF005", "ok"]
    actual = _evento(evento.id_evento)
    assert actual.total_pagado == evento.costo_total and actual.finiquitado == "S"


# ------------------------ HU-008 · el cliente lo ve ------------------------
def test_el_cliente_ve_su_abono_y_su_finiquito(cliente_http, crear_usuario):
    id_gerente, correo_g, clave_g = crear_usuario("GERENTE")
    id_cliente, correo_c, clave_c = crear_usuario("CLIENTE")
    evento = _nuevo_evento(id_cliente)
    _entrar(cliente_http, correo_g, clave_g)
    _abonar(cliente_http, evento, evento.costo_total, "DEPOSITO", "Ficha 5521")
    cliente_http.post("/logout")

    _entrar(cliente_http, correo_c, clave_c)
    detalle = cliente_http.get(f"/mis-eventos/{evento.clave_proyecto}").get_data(as_text=True)
    assert "Depósito" in detalle and "Ficha 5521" in detalle and "Tu evento quedó liquidado" in detalle
