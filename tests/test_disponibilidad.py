"""
Sprint 2 · Parte 2 · Control de aforo y disponibilidad (HU-007, CU-07).
Casos del SRS Anexo C: CP-10, CP-11, CP-12 y CP-19 completo.

Las reglas RN-01 (BF001) y RN-02 (BF002) viven en la base (DA-01, RNF-09).
La primera mitad las prueba por SQL directo, sin la aplicación, como pide
el Anexo C; la segunda comprueba que la pantalla las traduce a un aviso
comprensible con los valores (RNF-12) y que la agenda se consulta (RF-24).
"""
import re
import threading

import psycopg
import pytest

from app.datos.conexion import BaseDatos
from tests.conftest import correo_unico, fecha_libre, telefono_unico

pytestmark = pytest.mark.integracion

TERRAZA = 3          # semilla: Salón Terraza, 90 personas (el salón de CP-10)


# ------------------------------- apoyo -------------------------------
def _cliente_sql(con) -> int:
    return con.execute(
        "INSERT INTO usuario (nombre, correo, rol, clave_hash) VALUES ('C', %s, 'CLIENTE', 'x') RETURNING id_usuario",
        (correo_unico("hu007"),)).fetchone()["id_usuario"]


def _insertar_sql(con, cliente, dia, inicio, fin, asistentes=40, salon=TERRAZA, estado="COTIZACION") -> int:
    """INSERT directo a EVENTO: el camino que la aplicación no controla."""
    return con.execute(
        """INSERT INTO evento (id_cliente, id_salon, id_paquete, fecha_evento, hora_inicio, hora_fin,
                               num_asistentes, estado)
           VALUES (%s, %s, 1, %s, %s, %s, %s, %s) RETURNING id_evento""",
        (cliente, salon, dia, inicio, fin, asistentes, estado)).fetchone()["id_evento"]


def _rechazo(con, sql, parametros):
    """Ejecuta dentro de un SAVEPOINT para que la conexión siga usable tras el rechazo."""
    with pytest.raises(psycopg.Error) as error:
        with con.transaction():
            con.execute(sql, parametros)
    return error.value


def _consulta(sql, parametros=()):
    with BaseDatos.transaccion() as cur:
        cur.execute(sql, parametros)
        return cur.fetchall()


def _entrar(http, identificador, clave):
    return http.post("/login", data={"identificador": identificador, "clave": clave})


@pytest.fixture
def gerente(cliente_http, crear_usuario):
    id_gerente, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    return id_gerente


def _reservar(http, id_cliente="", **cambios):
    datos = {"id_cliente": str(id_cliente), "id_salon": str(TERRAZA), "id_paquete": "1",
             "fecha_evento": fecha_libre().isoformat(), "hora_inicio": "14:00", "hora_fin": "19:00",
             "num_asistentes": "60", "nombre_evento": "HU-007"}
    datos.update(cambios)
    return http.post("/eventos/nuevo", data=datos)


# =====================================================================
# Reglas en la base, por SQL directo (DA-01 · RNF-09)
# =====================================================================
def test_cp10_bd_rechaza_sobrecupo_con_ambos_valores(conexion):
    """CP-10 · RF-25 · RN-01: 150 asistentes en un salón de 90."""
    cliente = _cliente_sql(conexion)
    capacidad = conexion.execute("SELECT capacidad_maxima FROM salon WHERE id_salon = %s",
                                 (TERRAZA,)).fetchone()["capacidad_maxima"]
    assert capacidad == 90
    dia = fecha_libre()

    with pytest.raises(psycopg.Error) as error:
        with conexion.transaction():
            _insertar_sql(conexion, cliente, dia, "14:00", "19:00", asistentes=150)
    assert error.value.sqlstate == "BF001"
    mensaje = error.value.diag.message_primary
    assert "90" in mensaje and "150" in mensaje and "Salón Terraza" in mensaje     # RNF-12

    # El límite exacto sí se acepta; uno más, no.
    id_evento = _insertar_sql(conexion, cliente, dia, "14:00", "19:00", asistentes=90)
    error = _rechazo(conexion, "UPDATE evento SET num_asistentes = 91 WHERE id_evento = %s", (id_evento,))
    assert error.sqlstate == "BF001"


def test_bf001_tambien_al_cambiar_de_salon(conexion):
    """Un evento de 120 personas cabe en el Jardín (150) y no puede pasarse a la Terraza (90)."""
    cliente = _cliente_sql(conexion)
    id_evento = _insertar_sql(conexion, cliente, fecha_libre(), "10:00", "12:00", asistentes=120, salon=2)
    error = _rechazo(conexion, "UPDATE evento SET id_salon = %s WHERE id_evento = %s", (TERRAZA, id_evento))
    assert error.sqlstate == "BF001"


def test_bf001_no_estorba_el_cierre_de_un_evento_anterior(conexion):
    """RN-04 permite bajar la capacidad cuando el evento grande ya pasó; cerrar ese evento
    como realizado no debe tropezar con el aforo actual."""
    cliente = _cliente_sql(conexion)
    conexion.execute("UPDATE evento SET estado = 'CANCELADO' WHERE id_salon = %s", (TERRAZA,))
    id_evento = _insertar_sql(conexion, cliente, "2020-05-10", "10:00", "12:00", asistentes=85,
                              estado="CONFIRMADO")
    conexion.execute("UPDATE salon SET capacidad_maxima = 50 WHERE id_salon = %s", (TERRAZA,))
    conexion.execute("UPDATE evento SET estado = 'REALIZADO' WHERE id_evento = %s", (id_evento,))
    assert conexion.execute("SELECT estado FROM evento WHERE id_evento = %s",
                            (id_evento,)).fetchone()["estado"] == "REALIZADO"


def test_cp11_bd_rechaza_traslape(conexion):
    """CP-11 · RF-26 · RN-02: 20:00–23:00 en un salón ocupado de 19:00 a 23:59."""
    cliente = _cliente_sql(conexion)
    dia = fecha_libre()
    ocupante = _insertar_sql(conexion, cliente, dia, "19:00", "23:59")
    clave = conexion.execute("SELECT clave_proyecto FROM evento WHERE id_evento = %s",
                             (ocupante,)).fetchone()["clave_proyecto"]

    with pytest.raises(psycopg.Error) as error:
        with conexion.transaction():
            _insertar_sql(conexion, cliente, dia, "20:00", "23:00")
    assert error.value.sqlstate == "BF002"
    mensaje = error.value.diag.message_primary
    assert clave in mensaje and "19:00" in mensaje and "23:59" in mensaje          # RNF-12
    assert f"{dia:%d/%m/%Y}" in mensaje


@pytest.mark.parametrize("inicio, fin", [
    ("18:00", "19:30"),      # se encima por el inicio
    ("23:00", "23:59"),      # se encima por el final
    ("20:00", "21:00"),      # queda dentro
    ("17:00", "23:59"),      # lo envuelve
    ("19:00", "23:59"),      # idéntico
])
def test_bf002_todas_las_formas_de_traslape(conexion, inicio, fin):
    cliente = _cliente_sql(conexion)
    dia = fecha_libre()
    _insertar_sql(conexion, cliente, dia, "19:00", "23:59")
    with pytest.raises(psycopg.Error) as error:
        with conexion.transaction():
            _insertar_sql(conexion, cliente, dia, inicio, fin)
    assert error.value.sqlstate == "BF002"


def test_cp12_bd_acepta_horarios_que_no_se_enciman(conexion):
    """CP-12 · RF-27: 08:00–13:00 con otro de 14:00–19:00 la misma fecha."""
    cliente = _cliente_sql(conexion)
    dia = fecha_libre()
    _insertar_sql(conexion, cliente, dia, "14:00", "19:00")
    _insertar_sql(conexion, cliente, dia, "08:00", "13:00")               # CP-12
    _insertar_sql(conexion, cliente, dia, "13:00", "14:00")               # contiguo por ambos lados
    _insertar_sql(conexion, cliente, dia, "14:00", "19:00", salon=2)      # mismo horario, otro salón
    total = conexion.execute("SELECT COUNT(*) AS n FROM evento WHERE fecha_evento = %s", (dia,)).fetchone()["n"]
    assert total == 4


def test_rn02_un_evento_cancelado_no_ocupa_el_salon(conexion):
    cliente = _cliente_sql(conexion)
    dia = fecha_libre()
    cancelado = _insertar_sql(conexion, cliente, dia, "19:00", "23:00", estado="CANCELADO")
    nuevo = _insertar_sql(conexion, cliente, dia, "20:00", "22:00")       # el horario quedó libre

    # Reactivar el cancelado ahora sí chocaría con el nuevo.
    error = _rechazo(conexion, "UPDATE evento SET estado = 'COTIZACION' WHERE id_evento = %s", (cancelado,))
    assert error.sqlstate == "BF002"
    # Cancelar el nuevo libera el horario otra vez.
    conexion.execute("UPDATE evento SET estado = 'CANCELADO' WHERE id_evento = %s", (nuevo,))
    conexion.execute("UPDATE evento SET estado = 'COTIZACION' WHERE id_evento = %s", (cancelado,))


def test_bf002_tambien_al_mover_un_evento(conexion):
    cliente = _cliente_sql(conexion)
    dia, otro_dia = fecha_libre(), fecha_libre()
    _insertar_sql(conexion, cliente, dia, "14:00", "19:00")
    movible = _insertar_sql(conexion, cliente, otro_dia, "16:00", "20:00")

    error = _rechazo(conexion, "UPDATE evento SET fecha_evento = %s WHERE id_evento = %s", (dia, movible))
    assert error.sqlstate == "BF002"
    # Recorrer su propio horario o cambiar su estatus no choca consigo mismo.
    conexion.execute("UPDATE evento SET hora_inicio = '17:00', hora_fin = '21:00' WHERE id_evento = %s", (movible,))
    conexion.execute("UPDATE evento SET estado = 'CONFIRMADO' WHERE id_evento = %s", (movible,))
    # Moverlo al otro día en un horario libre sí procede.
    conexion.execute("UPDATE evento SET fecha_evento = %s, hora_inicio = '19:00', hora_fin = '23:00' "
                     "WHERE id_evento = %s", (dia, movible))


def test_bf001_se_evalua_antes_que_bf002(conexion):
    """Figura 19: primero el aforo, después la agenda."""
    cliente = _cliente_sql(conexion)
    dia = fecha_libre()
    _insertar_sql(conexion, cliente, dia, "14:00", "19:00")
    with pytest.raises(psycopg.Error) as error:
        with conexion.transaction():
            _insertar_sql(conexion, cliente, dia, "15:00", "18:00", asistentes=500)
    assert error.value.sqlstate == "BF001"


def test_bf002_dos_reservas_simultaneas_solo_entra_una(base_pruebas):
    """Dos gerentes guardan el mismo horario al mismo tiempo: la segunda transacción
    espera a la primera y, al ver su evento, se rechaza (candado por salón)."""
    dia = fecha_libre()
    with psycopg.connect(base_pruebas, autocommit=True) as preparacion:
        cliente = preparacion.execute(
            "INSERT INTO usuario (nombre, correo, rol, clave_hash) VALUES ('C', %s, 'CLIENTE', 'x') RETURNING id_usuario",
            (correo_unico("simultaneo"),)).fetchone()[0]

    sql = """INSERT INTO evento (id_cliente, id_salon, id_paquete, fecha_evento, hora_inicio, hora_fin, num_asistentes)
             VALUES (%s, %s, 1, %s, '14:00', '19:00', 40)"""
    resultado = {}

    def segunda():
        try:
            with psycopg.connect(base_pruebas) as con:
                con.execute(sql, (cliente, TERRAZA, dia))
            resultado["estado"] = "guardado"
        except psycopg.Error as error:
            resultado["estado"] = error.sqlstate

    with psycopg.connect(base_pruebas) as primera:
        primera.execute(sql, (cliente, TERRAZA, dia))          # sin COMMIT todavía
        hilo = threading.Thread(target=segunda)
        hilo.start()
        hilo.join(timeout=1.5)
        assert hilo.is_alive(), "la segunda reserva debió esperar a la primera"
        primera.commit()
    hilo.join(timeout=10)
    assert resultado["estado"] == "BF002"
    with psycopg.connect(base_pruebas) as verificacion:
        guardados = verificacion.execute("SELECT COUNT(*) FROM evento WHERE id_salon = %s AND fecha_evento = %s",
                                         (TERRAZA, dia)).fetchone()[0]
    assert guardados == 1


# =====================================================================
# La pantalla traduce el rechazo y consulta la agenda (C-04 · IU-06)
# =====================================================================
def test_cp10_pantalla_advierte_y_rechaza_sobrecupo(cliente_http, gerente, crear_usuario):
    """CP-10 completo: aviso durante la captura y rechazo BF001 al guardar."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    formulario = cliente_http.get("/eventos/nuevo").get_data(as_text=True)
    assert 'data-capacidad="90"' in formulario and "data-aviso-aforo" in formulario      # RF-23

    dia = fecha_libre().isoformat()
    respuesta = _reservar(cliente_http, id_cliente, num_asistentes="150", fecha_evento=dia)
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 422
    assert "admite 90 personas y el evento es para 150" in texto                          # RF-25 · RNF-12
    assert 'value="150"' in texto                                                         # no se pierde la captura
    assert _consulta("SELECT 1 FROM evento WHERE id_salon = %s AND fecha_evento = %s", (TERRAZA, dia)) == []


def test_cp11_agenda_muestra_el_evento_y_la_pantalla_rechaza_el_traslape(cliente_http, gerente, crear_usuario):
    """CP-11 completo: la consulta de agenda lista el evento programado (RF-24) y guardar se rechaza (RF-26)."""
    id_cliente, _, _ = crear_usuario("CLIENTE")
    dia = fecha_libre().isoformat()
    primero = _reservar(cliente_http, id_cliente, fecha_evento=dia, hora_inicio="19:00", hora_fin="23:59",
                        nombre_evento="Boda ocupante")
    assert primero.status_code == 302
    clave = _consulta("SELECT clave_proyecto FROM evento WHERE id_salon = %s AND fecha_evento = %s",
                      (TERRAZA, dia))[0]["clave_proyecto"]

    agenda = cliente_http.get("/api/agenda", query_string={"salon": TERRAZA, "fecha": dia,
                                                           "inicio": "20:00", "fin": "23:00"})
    assert agenda.status_code == 200 and agenda.is_json
    datos = agenda.get_json()
    assert datos["libre"] is False and datos["salon"]["capacidad"] == 90
    assert [(e["clave"], e["inicio"], e["fin"], e["traslapa"]) for e in datos["eventos"]] == \
           [(clave, "19:00", "23:59", True)]
    assert datos["eventos"][0]["titulo"] == "Boda ocupante"

    respuesta = _reservar(cliente_http, id_cliente, fecha_evento=dia, hora_inicio="20:00", hora_fin="23:00")
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 422
    assert "ya está ocupado" in texto and clave in texto and "19:00 a 23:59" in texto     # RNF-12
    assert len(_consulta("SELECT 1 FROM evento WHERE id_salon = %s AND fecha_evento = %s", (TERRAZA, dia))) == 1


def test_cp12_pantalla_acepta_dos_eventos_el_mismo_dia(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    dia = fecha_libre().isoformat()
    assert _reservar(cliente_http, id_cliente, fecha_evento=dia, hora_inicio="14:00", hora_fin="19:00").status_code == 302

    agenda = cliente_http.get("/api/agenda", query_string={"salon": TERRAZA, "fecha": dia,
                                                           "inicio": "08:00", "fin": "13:00"}).get_json()
    assert agenda["libre"] is True and len(agenda["eventos"]) == 1 and not agenda["eventos"][0]["traslapa"]

    assert _reservar(cliente_http, id_cliente, fecha_evento=dia, hora_inicio="08:00", hora_fin="13:00").status_code == 302
    assert len(_consulta("SELECT 1 FROM evento WHERE id_salon = %s AND fecha_evento = %s", (TERRAZA, dia))) == 2


def test_cp19_alta_conjunta_con_sobrecupo_no_deja_al_cliente(cliente_http, gerente):
    """CP-19 completo · RF-12 · RNF-08 · DA-05: el rechazo BF001 revierte también el alta del cliente."""
    celular, correo = telefono_unico(), correo_unico("cp19")
    respuesta = _reservar(cliente_http, "", cliente_nuevo="S", nombre="No debe quedar",
                          telefono=celular, correo=correo, num_asistentes="150")
    assert respuesta.status_code == 422
    assert "admite 90 personas" in respuesta.get_data(as_text=True)
    assert _consulta("SELECT 1 FROM usuario WHERE telefono = %s OR correo = %s", (celular, correo)) == []
    assert _consulta("SELECT 1 FROM bitacora b JOIN usuario u ON b.entidad = 'usuario:' || u.id_usuario "
                     "WHERE u.telefono = %s", (celular,)) == []

    # El mismo celular sigue libre: corregido el aforo, el alta conjunta procede.
    respuesta = _reservar(cliente_http, "", cliente_nuevo="S", nombre="Ahora sí",
                          telefono=celular, num_asistentes="80")
    assert respuesta.status_code == 200 and "Cliente registrado: Ahora sí" in respuesta.get_data(as_text=True)


def test_rf24_agenda_sin_horario_y_con_eventos_cancelados(cliente_http, gerente, crear_usuario):
    id_cliente, _, _ = crear_usuario("CLIENTE")
    dia = fecha_libre().isoformat()
    libre = cliente_http.get("/api/agenda", query_string={"salon": TERRAZA, "fecha": dia}).get_json()
    assert libre["eventos"] == [] and libre["libre"] is None                 # sin horario no hay veredicto

    respuesta = _reservar(cliente_http, id_cliente, fecha_evento=dia)
    id_evento = int(re.search(r"/eventos/(\d+)$", respuesta.location).group(1))
    cliente_http.post(f"/eventos/{id_evento}/estado", data={"estado": "CANCELADO"})
    agenda = cliente_http.get("/api/agenda", query_string={"salon": TERRAZA, "fecha": dia,
                                                           "inicio": "15:00", "fin": "18:00"}).get_json()
    assert agenda["eventos"] == [] and agenda["libre"] is True               # RN-02: el cancelado no ocupa


@pytest.mark.parametrize("parametros, estado", [
    ({"salon": "", "fecha": "2027-01-01"}, 400),
    ({"salon": "3", "fecha": "no-es-fecha"}, 400),
    ({"salon": "3", "fecha": "2027-01-01", "inicio": "25:99", "fin": "26:00"}, 400),
    ({"salon": "999", "fecha": "2027-01-01"}, 404),
])
def test_rf24_agenda_valida_sus_parametros(cliente_http, gerente, parametros, estado):
    respuesta = cliente_http.get("/api/agenda", query_string=parametros)
    assert respuesta.status_code == estado and "error" in respuesta.get_json()


def test_rf24_formulario_trae_el_bloque_de_agenda(cliente_http, gerente):
    texto = cliente_http.get("/eventos/nuevo").get_data(as_text=True)
    assert 'data-url="/api/agenda"' in texto and "data-aviso-traslape" in texto


def test_rf05_la_agenda_es_solo_para_el_gerente(cliente_http, crear_usuario):
    sin_sesion = cliente_http.get("/api/agenda", query_string={"salon": TERRAZA, "fecha": "2027-01-01"})
    assert sin_sesion.status_code == 302 and "/login" in sin_sesion.location

    _, correo, clave = crear_usuario("CLIENTE")
    _entrar(cliente_http, correo, clave)
    como_cliente = cliente_http.get("/api/agenda", query_string={"salon": TERRAZA, "fecha": "2027-01-01"})
    assert como_cliente.status_code == 302 and como_cliente.location.endswith("/mis-eventos")
