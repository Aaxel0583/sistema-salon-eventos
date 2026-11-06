"""
Sprint 2 · Parte 1 · Motor de reservas y tablero (HU-005, HU-006).
Casos del SRS Anexo C: CP-07, CP-08, CP-09, CP-24 y la parte de CP-19 que
no depende del aforo (atomicidad del alta conjunta, DA-05).
CP-10, CP-11, CP-12 y CP-19 completo se prueban con HU-007 (Parte 2).
"""
import re
import uuid
from datetime import date, timedelta

import psycopg
import pytest

from app.datos.conexion import BaseDatos
from app.datos.repositorio_eventos import RepositorioEventos
from tests.conftest import correo_unico, telefono_unico

pytestmark = pytest.mark.integracion


# ------------------------------- apoyo -------------------------------
def _entrar(http, identificador, clave):
    return http.post("/login", data={"identificador": identificador, "clave": clave})


@pytest.fixture
def gerente(cliente_http, crear_usuario):
    id_gerente, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    return id_gerente


def _fecha_futura() -> str:
    """Una fecha distinta por prueba, para no chocar con los traslapes de HU-007."""
    return (date.today() + timedelta(days=400 + uuid.uuid4().int % 3000)).isoformat()


def _consulta(sql, parametros=()):
    with BaseDatos.transaccion() as cur:
        cur.execute(sql, parametros)
        return cur.fetchall()


def _salon(id_salon=1):
    return _consulta("SELECT * FROM salon WHERE id_salon = %s", (id_salon,))[0]


def _paquete(id_paquete=1):
    return _consulta("SELECT * FROM paquete WHERE id_paquete = %s", (id_paquete,))[0]


def _reservar(http, id_cliente="", **cambios):
    datos = {"id_cliente": str(id_cliente), "id_salon": "3", "id_paquete": "1",
             "fecha_evento": _fecha_futura(), "hora_inicio": "14:00", "hora_fin": "19:00",
             "num_asistentes": "60", "nombre_evento": "Prueba " + uuid.uuid4().hex[:6]}
    datos.update(cambios)
    return http.post("/eventos/nuevo", data=datos)


def _en_tabla(texto: str, evento) -> bool:
    """¿El evento aparece como fila? (su clave también puede venir en un aviso)."""
    return f'href="/eventos/{evento.id_evento}"' in texto


def _id_de(respuesta) -> int:
    return int(re.search(r"/eventos/(\d+)$", respuesta.location).group(1))


def _evento(id_evento):
    with BaseDatos.transaccion() as cur:
        return RepositorioEventos(cur).por_id(id_evento)


def _insertar_directo(id_cliente, dias, id_salon=2, estado="COTIZACION", asistentes=40):
    """Evento capturado sin pasar por la pantalla (p. ej. uno ya vencido)."""
    with BaseDatos.transaccion() as cur:
        repo = RepositorioEventos(cur)
        id_evento = repo.insertar(id_cliente, None, id_salon, 1, "Directo",
                                  repo.hoy() + timedelta(days=dias), "10:00", "12:00", asistentes)
        if estado != "COTIZACION":
            repo.actualizar_estado(id_evento, estado)
    return id_evento


# ----------------------------- HU-005 -----------------------------
def test_cp07_registro_y_cotizacion(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    respuesta = _reservar(cliente_http, id_cliente, id_salon="3", id_paquete="2", num_asistentes="75")
    assert respuesta.status_code == 302

    evento = _evento(_id_de(respuesta))
    renta, precio = _salon(3)["costo_renta"], _paquete(2)["precio_persona"]
    assert evento.estado == "COTIZACION"                                # criterio de HU-005
    assert evento.costo_total == renta + precio * 75                    # RN-09
    assert evento.id_gerente == gerente and evento.id_cliente == id_cliente
    assert evento.saldo == evento.costo_total and evento.finiquitado == "N"

    texto = cliente_http.get(respuesta.location).get_data(as_text=True)
    assert evento.clave_proyecto in texto and "registrado en cotización" in texto

    bitacora = _consulta("SELECT accion FROM bitacora WHERE entidad = %s", (f"evento:{evento.id_evento}",))
    assert [b["accion"] for b in bitacora] == ["ALTA_EVENTO"]


def test_cp08_clave_formato_consecutivo_e_inmutable(conexion):
    anio = conexion.execute("SELECT to_char(CURRENT_DATE, 'YYYY') AS a").fetchone()["a"]
    cliente = conexion.execute(
        "INSERT INTO usuario (nombre, correo, rol, clave_hash) VALUES ('C', %s, 'CLIENTE', 'x') RETURNING id_usuario",
        (correo_unico("cp08"),)).fetchone()["id_usuario"]
    insertar = """INSERT INTO evento (clave_proyecto, id_cliente, id_salon, id_paquete, fecha_evento,
                                      hora_inicio, hora_fin, num_asistentes, costo_total)
                  VALUES (%s, %s, 1, 1, CURRENT_DATE + 900, '10:00', '12:00', 10, 0)
                  RETURNING clave_proyecto, costo_total"""
    # La clave y el costo que mande el INSERT se ignoran: los asigna la base (DA-01).
    primera = conexion.execute(insertar, ("EVT-1999-0001", cliente)).fetchone()
    segunda = conexion.execute(insertar, ("X", cliente)).fetchone()
    assert re.fullmatch(rf"EVT-{anio}-\d{{4}}", primera["clave_proyecto"])
    assert int(segunda["clave_proyecto"][-4:]) == int(primera["clave_proyecto"][-4:]) + 1
    assert primera["costo_total"] > 0

    with pytest.raises(psycopg.Error) as error:
        conexion.execute("UPDATE evento SET clave_proyecto = 'EVT-2026-9999' WHERE clave_proyecto = %s",
                         (primera["clave_proyecto"],))
    assert error.value.sqlstate == "BF008"


def test_rn09_costo_se_recalcula_y_se_conserva(conexion):
    cliente = conexion.execute(
        "INSERT INTO usuario (nombre, correo, rol, clave_hash) VALUES ('C', %s, 'CLIENTE', 'x') RETURNING id_usuario",
        (correo_unico("rn09"),)).fetchone()["id_usuario"]
    id_evento = conexion.execute(
        """INSERT INTO evento (id_cliente, id_salon, id_paquete, fecha_evento, hora_inicio, hora_fin, num_asistentes)
           VALUES (%s, 2, 3, CURRENT_DATE + 950, '10:00', '12:00', 50) RETURNING id_evento""",
        (cliente,)).fetchone()["id_evento"]
    costo = lambda: conexion.execute("SELECT costo_total FROM evento WHERE id_evento = %s",   # noqa: E731
                                     (id_evento,)).fetchone()["costo_total"]
    renta = conexion.execute("SELECT costo_renta FROM salon WHERE id_salon = 2").fetchone()["costo_renta"]
    precio = conexion.execute("SELECT precio_persona FROM paquete WHERE id_paquete = 3").fetchone()["precio_persona"]
    assert costo() == renta + precio * 50

    conexion.execute("UPDATE evento SET num_asistentes = 60 WHERE id_evento = %s", (id_evento,))
    assert costo() == renta + precio * 60                     # se recalcula al editar el evento

    conexion.execute("UPDATE salon SET costo_renta = costo_renta + 1000 WHERE id_salon = 2")
    assert costo() == renta + precio * 60                     # el precio pactado no cambia
    assert conexion.execute("SELECT fn_cotizar(2, NULL, 999) AS c").fetchone()["c"] == renta + 1000

    with pytest.raises(psycopg.Error) as error:
        conexion.execute("SELECT fn_cotizar(99, 1, 10)")
    assert error.value.sqlstate == "BF009"


def test_rf12_alta_conjunta_entrega_la_clave_una_vez(cliente_http, gerente):
    celular = telefono_unico()
    respuesta = _reservar(cliente_http, "", cliente_nuevo="S", nombre="Familia Robles", telefono=celular)
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200 and "Cliente registrado: Familia Robles" in texto
    assert "no volverá a mostrarse" in texto and respuesta.headers["Cache-Control"] == "no-store"

    cliente = _consulta("SELECT id_usuario, rol FROM usuario WHERE telefono = %s", (celular,))[0]
    assert cliente["rol"] == "CLIENTE"
    eventos = _consulta("SELECT clave_proyecto FROM evento WHERE id_cliente = %s", (cliente["id_usuario"],))
    assert len(eventos) == 1 and eventos[0]["clave_proyecto"] in texto


def test_da05_si_el_evento_se_rechaza_el_cliente_no_se_guarda(cliente_http, gerente, crear_usuario):
    """Escenario 2: la transacción la abre C-04; el rechazo revierte también el alta."""
    dueno, _, _ = crear_usuario("CLIENTE")
    with BaseDatos.transaccion() as cur:
        cur.execute("""INSERT INTO paquete (nombre, precio_persona, tipo, id_cliente)
                       VALUES (%s, 450, 'PERSONALIZADO', %s) RETURNING id_paquete""",
                    ("Exclusivo " + uuid.uuid4().hex[:6], dueno))
        id_personalizado = cur.fetchone()["id_paquete"]

    celular = telefono_unico()
    respuesta = _reservar(cliente_http, "", cliente_nuevo="S", nombre="No debe quedar",
                          telefono=celular, id_paquete=str(id_personalizado))
    assert respuesta.status_code == 422
    assert "es personalizado de" in respuesta.get_data(as_text=True)
    assert _consulta("SELECT 1 FROM usuario WHERE telefono = %s", (celular,)) == []

    # El dueño del paquete sí puede usarlo.
    assert _reservar(cliente_http, dueno, id_paquete=str(id_personalizado)).status_code == 302


@pytest.mark.parametrize("cambios, mensaje", [
    ({"fecha_evento": "2020-01-10"}, "ya pasó"),
    ({"hora_inicio": "20:00", "hora_fin": "18:00"}, "debe ser posterior"),
    ({"id_salon": ""}, "Elige un valor en «Salón»"),
    ({"id_cliente": ""}, "Elige un valor en «Cliente»"),
])
def test_rechazos_conservan_lo_capturado(cliente_http, gerente, crear_usuario, cambios, mensaje):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    datos = {"id_cliente": id_cliente, "nombre_evento": "XV Años Conservado", **cambios}
    respuesta = _reservar(cliente_http, **datos)
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 422 and mensaje in texto
    assert 'value="XV Años Conservado"' in texto                          # no se pierde la captura


def test_salon_no_disponible_no_recibe_reservaciones(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    sql_disponible = "UPDATE salon SET disponible = %s WHERE id_salon = 3"
    with BaseDatos.transaccion() as cur:
        cur.execute(sql_disponible, ("N",))
    try:
        respuesta = _reservar(cliente_http, id_cliente)
        assert respuesta.status_code == 422 and "no disponible" in respuesta.get_data(as_text=True)
    finally:
        with BaseDatos.transaccion() as cur:
            cur.execute(sql_disponible, ("S",))


def test_formulario_trae_datos_para_cotizar_en_vivo(cliente_http, gerente, crear_usuario):
    """RF-21 y RF-23 se calculan en el navegador con los datos de cada opción (RNF-01)."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    texto = cliente_http.get(f"/eventos/nuevo?cliente={id_cliente}").get_data(as_text=True)
    salon = _salon(3)
    assert f'data-renta="{salon["costo_renta"]}" data-capacidad="{salon["capacidad_maxima"]}"' in texto
    assert 'data-precio="' in texto and "data-cot-total" in texto and "data-cot-lugares" in texto
    assert f'<option value="{id_cliente}" selected' in texto                # llegada desde el directorio
    assert f'/eventos/nuevo?cliente={id_cliente}' in cliente_http.get("/clientes").get_data(as_text=True)


# ----------------------------- HU-006 -----------------------------
def test_cp09_filtrado_del_listado(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    marca = uuid.uuid4().hex[:8]
    en_terraza = _evento(_id_de(_reservar(cliente_http, id_cliente, id_salon="3", nombre_evento=f"Terraza {marca}")))
    en_jardin = _evento(_id_de(_reservar(cliente_http, id_cliente, id_salon="2", nombre_evento=f"Jardín {marca}")))
    cliente_http.post(f"/eventos/{en_jardin.id_evento}/estado", data={"estado": "CONFIRMADO"})

    texto = cliente_http.get("/eventos", query_string={"q": marca, "salon": "3"}).get_data(as_text=True)
    assert _en_tabla(texto, en_terraza) and not _en_tabla(texto, en_jardin)

    texto = cliente_http.get("/eventos", query_string={"q": marca, "estado": "CONFIRMADO"}).get_data(as_text=True)
    assert _en_tabla(texto, en_jardin) and not _en_tabla(texto, en_terraza)

    texto = cliente_http.get("/eventos", query_string={"q": en_terraza.clave_proyecto.lower()}).get_data(as_text=True)
    assert _en_tabla(texto, en_terraza) and not _en_tabla(texto, en_jardin)   # búsqueda por clave

    texto = cliente_http.get("/eventos", query_string={"q": "nadie-" + marca}).get_data(as_text=True)
    assert "Ningún evento coincide" in texto


def test_cp24_gerente_responsable_y_estatus(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    otro_gerente, _, _ = crear_usuario("GERENTE")
    evento = _evento(_id_de(_reservar(cliente_http, id_cliente)))
    ruta = f"/eventos/{evento.id_evento}"

    assert cliente_http.post(ruta, data={"id_gerente": str(otro_gerente)}).status_code == 302
    assert _evento(evento.id_evento).id_gerente == otro_gerente             # RF-29
    cliente_http.post(ruta, data={"id_gerente": str(id_cliente)})          # un cliente no puede ser responsable
    assert _evento(evento.id_evento).id_gerente == otro_gerente

    cliente_http.post(f"{ruta}/estado", data={"estado": "CONFIRMADO"})
    assert _evento(evento.id_evento).estado == "CONFIRMADO"

    respuesta = cliente_http.post(f"{ruta}/estado", data={"estado": "PAGADO"}, follow_redirects=True)
    assert "no es válido" in respuesta.get_data(as_text=True)              # RN-11
    respuesta = cliente_http.post(f"{ruta}/estado", data={"estado": "REALIZADO"}, follow_redirects=True)
    assert "antes de su fecha" in respuesta.get_data(as_text=True)         # SDD §5.3
    actual = _evento(evento.id_evento)
    assert actual.estado == "CONFIRMADO" and actual.finiquitado == "N"     # la bandera no cambia

    acciones = [b["accion"] for b in _consulta(
        "SELECT accion FROM bitacora WHERE entidad LIKE %s ORDER BY id_bitacora", (f"evento:{evento.id_evento}%",))]
    assert acciones == ["ALTA_EVENTO", "ASIGNAR_GERENTE", "CAMBIO_ESTATUS"]  # RF-41 · CP-23 (parte)


def test_tablero_pendientes_de_cierre(cliente_http, gerente, crear_usuario):
    """IB-11 · RN-14 · DA-04: el sistema avisa, el gerente decide."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    vencido = _evento(_insertar_directo(id_cliente, dias=-5, estado="CONFIRMADO"))
    texto = cliente_http.get("/panel").get_data(as_text=True)
    assert "siguen abiertos" in texto or "sigue abierto" in texto
    assert _en_tabla(texto, vencido)
    assert _evento(vencido.id_evento).estado == "CONFIRMADO"               # nadie lo cerró solo

    respuesta = cliente_http.post(f"/eventos/{vencido.id_evento}/estado",
                                  data={"estado": "REALIZADO", "volver": "panel"})
    assert respuesta.location.endswith("/panel")
    assert _evento(vencido.id_evento).estado == "REALIZADO"
    texto = cliente_http.get("/panel").get_data(as_text=True)
    assert "quedó en estatus Realizado" in texto and not _en_tabla(texto, vencido)

    respuesta = cliente_http.post(f"/eventos/{vencido.id_evento}/estado",
                                  data={"estado": "CANCELADO"}, follow_redirects=True)
    assert "cerró su ciclo" in respuesta.get_data(as_text=True)            # Realizado es final


def test_ib10_ocupacion_cuenta_solo_eventos_proximos_vigentes(crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")

    def ocupacion():
        with BaseDatos.transaccion() as cur:
            return {o.id_salon: o for o in RepositorioEventos(cur).ocupacion_por_salon()}

    antes = ocupacion()[1]
    _insertar_directo(id_cliente, dias=1200, id_salon=1, asistentes=125)
    _insertar_directo(id_cliente, dias=1201, id_salon=1, estado="CANCELADO")   # no cuenta
    _insertar_directo(id_cliente, dias=-30, id_salon=1)                       # pasado: no cuenta
    despues = ocupacion()[1]
    assert despues.eventos_proximos == antes.eventos_proximos + 1
    assert despues.mayor_aforo >= 125


def test_indicadores_del_tablero(crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    with BaseDatos.transaccion() as cur:
        antes = RepositorioEventos(cur).indicadores()
    confirmado = _evento(_insertar_directo(id_cliente, dias=1300, estado="CONFIRMADO"))
    _insertar_directo(id_cliente, dias=1301)                                  # cotización: no es por cobrar
    with BaseDatos.transaccion() as cur:
        despues = RepositorioEventos(cur).indicadores()
    assert despues["activos"] == antes["activos"] + 2
    assert despues["por_cobrar"] == antes["por_cobrar"] + confirmado.saldo


def test_rf05_cliente_no_entra_a_eventos(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("CLIENTE")
    _entrar(cliente_http, correo, clave)
    for ruta in ("/eventos", "/eventos/nuevo", "/eventos/1"):
        respuesta = cliente_http.get(ruta)
        assert respuesta.status_code == 302 and respuesta.location.endswith("/mis-eventos"), ruta
    assert cliente_http.post("/eventos/1/estado", data={"estado": "CANCELADO"}).location.endswith("/mis-eventos")
