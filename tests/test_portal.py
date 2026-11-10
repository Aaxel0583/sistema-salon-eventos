"""
Sprint 2 · Parte 2 · Portal del cliente (HU-008, CU-10).
Caso del SRS Anexo C: CP-13 · consulta del evento propio y aislamiento
entre clientes (RF-39, RF-40, RNF-06).
"""
import re

import pytest

from app.datos.conexion import BaseDatos
from app.datos.repositorio_eventos import RepositorioEventos
from tests.conftest import fecha_libre

pytestmark = pytest.mark.integracion


# ------------------------------- apoyo -------------------------------
def _entrar(http, identificador, clave):
    return http.post("/login", data={"identificador": identificador, "clave": clave})


def _evento_de(id_cliente, nombre, id_paquete=2, asistentes=60, estado="COTIZACION", dia=None, id_gerente=None):
    """Registra un evento como lo haría el gerente y devuelve su fila de IB-01."""
    with BaseDatos.transaccion() as cur:
        repo = RepositorioEventos(cur)
        id_evento = repo.insertar(id_cliente, id_gerente, 3, id_paquete, nombre, dia or fecha_libre(),
                                  "14:00", "19:00", asistentes)
        if estado != "COTIZACION":
            repo.actualizar_estado(id_evento, estado)
        return repo.por_id(id_evento)


def _abonar(id_evento, monto, tipo="TRANSFERENCIA", referencia=None):
    """El registro de pagos (IB-06) llega en el Sprint 3; aquí se inserta el abono directo."""
    with BaseDatos.transaccion() as cur:
        cur.execute("INSERT INTO pago (id_evento, monto, tipo, referencia) VALUES (%s, %s, %s, %s)",
                    (id_evento, monto, tipo, referencia))


@pytest.fixture
def dos_clientes(app, crear_usuario):
    """Ana y Beto, cada uno con su evento."""
    ana = crear_usuario("CLIENTE")
    beto = crear_usuario("CLIENTE")
    return {
        "ana": ana, "beto": beto,
        "evento_ana": _evento_de(ana[0], "Boda de Ana"),
        "evento_beto": _evento_de(beto[0], "Graduación de Beto"),
    }


# ------------------------------ CP-13 ------------------------------
def test_cp13_cliente_ve_solo_sus_eventos(cliente_http, dos_clientes):
    """RF-39 · IU-09: la lista trae únicamente los eventos del titular autenticado."""
    _, correo, clave = dos_clientes["ana"]
    _entrar(cliente_http, correo, clave)
    texto = cliente_http.get("/mis-eventos").get_data(as_text=True)

    propio, ajeno = dos_clientes["evento_ana"], dos_clientes["evento_beto"]
    assert "Boda de Ana" in texto and propio.clave_proyecto in texto
    assert f'href="/mis-eventos/{propio.clave_proyecto}"' in texto
    assert "Graduación de Beto" not in texto and ajeno.clave_proyecto not in texto
    assert "Cotización" in texto and "Saldo pendiente" in texto              # estatus y saldo (IU-09)
    assert "<form" not in texto.split('id="contenido"')[1].split("<dialog")[0]   # sin acciones de modificación


def test_cp13_detalle_con_menu_pagos_y_saldo(cliente_http, crear_usuario):
    """RF-40 · IU-10: menú del paquete contratado, pagos registrados y saldo pendiente."""
    id_gerente, _, _ = crear_usuario("GERENTE")
    id_cliente, correo, clave = crear_usuario("CLIENTE")
    evento = _evento_de(id_cliente, "XV de Sofía", id_paquete=2, asistentes=50, estado="CONFIRMADO",
                        id_gerente=id_gerente)
    _abonar(evento.id_evento, 5000, "TRANSFERENCIA", "SPEI 4471")
    _abonar(evento.id_evento, 2500.50, "EFECTIVO")

    _entrar(cliente_http, correo, clave)
    respuesta = cliente_http.get(f"/mis-eventos/{evento.clave_proyecto}")
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200 and respuesta.headers["Cache-Control"] == "no-store"

    # Resumen: salón, fecha, horario, invitados y estatus
    assert "XV de Sofía" in texto and "Salón Terraza" in texto and "14:00 a 19:00" in texto
    assert f"{evento.fecha_evento:%d/%m/%Y}" in texto and "Confirmado" in texto
    # Menú del Paquete Ejecutivo (semilla), agrupado por categoría
    for parte in ("Paquete Ejecutivo", "Crema de elote", "Lomo de cerdo en salsa de ciruela",
                  "Pastel de tres leches", "Plato fuerte"):
        assert parte in texto
    # Pagos y saldo: 8,000 de renta + 380 × 50 = 27,000.00; pagado 7,500.50; saldo 19,499.50
    assert "$27,000.00" in texto and "$7,500.50" in texto and "$19,499.50" in texto
    assert "$5,000.00" in texto and "SPEI 4471" in texto and "Transferencia" in texto and "Efectivo" in texto
    # Solo lectura
    assert "<form" not in texto.split('id="contenido"')[1].split("<dialog")[0]

    lista = cliente_http.get("/mis-eventos").get_data(as_text=True)
    assert "$19,499.50" in lista


def test_cp13_evento_ajeno_se_niega_y_regresa_al_panel(cliente_http, dos_clientes):
    """RNF-06: escribir en la dirección la clave del evento de otro cliente no lo muestra."""
    _, correo, clave = dos_clientes["ana"]
    _entrar(cliente_http, correo, clave)
    ajeno = dos_clientes["evento_beto"]

    respuesta = cliente_http.get(f"/mis-eventos/{ajeno.clave_proyecto}")
    assert respuesta.status_code == 302 and respuesta.location.endswith("/mis-eventos")
    texto = cliente_http.get(respuesta.location).get_data(as_text=True)
    assert "No encontramos ese evento entre los tuyos" in texto
    assert "Graduación de Beto" not in texto and ajeno.clave_proyecto not in texto

    # Un evento ajeno y uno que no existe responden exactamente igual: no se revela cuál existe.
    inexistente = cliente_http.get("/mis-eventos/EVT-1990-0001")
    assert (inexistente.status_code, inexistente.location) == (respuesta.status_code, respuesta.location)
    # La pantalla del gerente tampoco es un atajo.
    ficha = cliente_http.get(f"/eventos/{ajeno.id_evento}")
    assert ficha.status_code == 302 and ficha.location.endswith("/mis-eventos")


@pytest.mark.parametrize("clave", ["evt-0000-0000", "1", "EVT-2026-0001%20OR%201=1", "EVT-2026-00011", "EVT-20O6-0001"])
def test_claves_mal_formadas_no_rompen_el_portal(cliente_http, crear_usuario, clave):
    _, correo, clave_acceso = crear_usuario("CLIENTE")
    _entrar(cliente_http, correo, clave_acceso)
    respuesta = cliente_http.get(f"/mis-eventos/{clave}")
    assert respuesta.status_code == 302 and respuesta.location.endswith("/mis-eventos")


def test_la_clave_se_acepta_en_minusculas(cliente_http, dos_clientes):
    _, correo, clave = dos_clientes["ana"]
    _entrar(cliente_http, correo, clave)
    respuesta = cliente_http.get(f"/mis-eventos/{dos_clientes['evento_ana'].clave_proyecto.lower()}")
    assert respuesta.status_code == 200 and "Boda de Ana" in respuesta.get_data(as_text=True)


def test_portal_exige_sesion_de_cliente(cliente_http, crear_usuario, dos_clientes):
    """RF-05: sin sesión se pide autenticación; un gerente es devuelto a su panel."""
    clave_evento = dos_clientes["evento_ana"].clave_proyecto
    for ruta in ("/mis-eventos", f"/mis-eventos/{clave_evento}"):
        assert "/login" in cliente_http.get(ruta).location

    _, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    for ruta in ("/mis-eventos", f"/mis-eventos/{clave_evento}"):
        respuesta = cliente_http.get(ruta)
        assert respuesta.status_code == 302 and respuesta.location.endswith("/panel"), ruta


def test_estados_del_evento_en_el_portal(cliente_http, crear_usuario):
    """Sin eventos se orienta al cliente; un evento cancelado no muestra saldo por cobrar;
    los eventos pasados van aparte de los próximos."""
    id_cliente, correo, clave = crear_usuario("CLIENTE")
    _entrar(cliente_http, correo, clave)
    vacio = cliente_http.get("/mis-eventos").get_data(as_text=True)
    assert "comunícate con el gerente del salón" in vacio

    _evento_de(id_cliente, "Evento cancelado", estado="CANCELADO")
    texto = cliente_http.get("/mis-eventos").get_data(as_text=True)
    assert "Evento cancelado" in texto and "Cancelado" in texto and "Saldo pendiente" not in texto
    assert "Próximos" in texto and "Anteriores" not in texto

    with BaseDatos.transaccion() as cur:
        hoy = RepositorioEventos(cur).hoy()
    _evento_de(id_cliente, "Evento de ayer", estado="CONFIRMADO", dia=hoy.replace(year=hoy.year - 3))
    texto = cliente_http.get("/mis-eventos").get_data(as_text=True)
    assert "Anteriores" in texto and re.search(r"Próximos.*Evento cancelado.*Anteriores.*Evento de ayer", texto, re.S)


def test_liquidado_cuando_el_saldo_llega_a_cero(cliente_http, crear_usuario):
    id_cliente, correo, clave = crear_usuario("CLIENTE")
    evento = _evento_de(id_cliente, "Evento pagado", estado="CONFIRMADO")
    _abonar(evento.id_evento, evento.costo_total)
    _entrar(cliente_http, correo, clave)
    assert "Liquidado" in cliente_http.get("/mis-eventos").get_data(as_text=True)
    detalle = cliente_http.get(f"/mis-eventos/{evento.clave_proyecto}").get_data(as_text=True)
    assert "$0.00" in detalle
