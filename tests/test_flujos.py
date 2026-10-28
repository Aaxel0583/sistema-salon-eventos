"""
Flujos completos a través de la aplicación (Flask test client).
Casos del SRS Anexo C: CP-01, CP-02, CP-03, CP-21, CP-22, CP-25 y RF-05.
"""
import pytest

from tests.conftest import correo_unico, telefono_unico

pytestmark = pytest.mark.integracion


def _entrar(http, identificador, clave):
    return http.post("/login", data={"identificador": identificador, "clave": clave})


def test_cp01_ingreso_redirige_al_panel_del_rol(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("GERENTE")
    respuesta = _entrar(cliente_http, correo.upper(), clave)       # sin distinguir mayúsculas
    assert respuesta.status_code == 302 and respuesta.location.endswith("/panel")

    otro = cliente_http.application.test_client()
    _, correo_c, clave_c = crear_usuario("CLIENTE")
    assert _entrar(otro, correo_c, clave_c).location.endswith("/mis-eventos")


def test_rf05_cliente_no_abre_pantallas_de_gerente(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("CLIENTE")
    _entrar(cliente_http, correo, clave)
    for ruta in ("/panel", "/clientes", "/salones", "/paquetes"):
        respuesta = cliente_http.get(ruta)
        assert respuesta.status_code == 302 and respuesta.location.endswith("/mis-eventos"), ruta


def test_cp02_bloqueo_al_quinto_intento(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("CLIENTE")
    for _ in range(4):
        texto = _entrar(cliente_http, correo, "incorrecta").get_data(as_text=True)
        assert "no son correctos" in texto
    texto = _entrar(cliente_http, correo, "incorrecta").get_data(as_text=True)
    assert "bloqueada" in texto
    # Ya bloqueada, ni con la clave correcta entra.
    assert "bloqueada" in _entrar(cliente_http, correo, clave).get_data(as_text=True)


def test_error_no_revela_si_la_cuenta_existe(cliente_http):
    texto = _entrar(cliente_http, "nadie@prueba.mx", "loquesea").get_data(as_text=True)
    assert "no son correctos" in texto


def test_cp21_cambio_obligatorio_de_clave_inicial(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("CLIENTE", clave="ABCD-EFGH", requiere_cambio=True)
    assert _entrar(cliente_http, correo, "abcd efgh").location.endswith("/clave")   # tolera dictado
    assert cliente_http.get("/mis-eventos").location.endswith("/clave")
    respuesta = cliente_http.post("/clave", data={
        "clave_actual": "ABCD-EFGH", "clave_nueva": "Nueva2026", "confirmacion": "Nueva2026"})
    assert respuesta.location.endswith("/mis-eventos")
    assert cliente_http.get("/mis-eventos").status_code == 200


def test_cp03_alta_de_cliente_y_unicidad(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    celular = telefono_unico()

    respuesta = cliente_http.post("/clientes/nuevo", data={"nombre": "Laura Díaz", "telefono": celular})
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200 and "Clave de acceso de Laura Díaz" in texto
    assert respuesta.headers["Cache-Control"] == "no-store"

    respuesta = cliente_http.post("/clientes/nuevo", data={"nombre": "Otra", "telefono": celular})
    assert respuesta.status_code == 422
    assert "ya pertenece a otro usuario" in respuesta.get_data(as_text=True)

    respuesta = cliente_http.post("/clientes/nuevo", data={"nombre": "Sin contacto"})
    assert "al menos un dato de contacto" in respuesta.get_data(as_text=True)


def test_cp22_regenerar_clave_y_cerrar_sesion(app, crear_usuario):
    gerente_http, cliente_http = app.test_client(), app.test_client()
    _, correo_g, clave_g = crear_usuario("GERENTE")
    id_cliente, correo_c, clave_vieja = crear_usuario("CLIENTE")
    for _ in range(5):
        _entrar(cliente_http, correo_c, "mal")                      # queda bloqueado

    _entrar(gerente_http, correo_g, clave_g)
    texto = gerente_http.get(f"/clientes?q={correo_c[:10]}").get_data(as_text=True)
    assert "Bloqueado" in texto
    texto = gerente_http.post(f"/clientes/{id_cliente}/clave").get_data(as_text=True)
    clave_nueva = texto.split('clave-generada__valor">')[1].split("<")[0]

    assert "no son correctos" in _entrar(cliente_http, correo_c, clave_vieja).get_data(as_text=True)
    assert _entrar(cliente_http, correo_c, clave_nueva).location.endswith("/clave")
    cliente_http.post("/logout")
    assert "/login" in cliente_http.get("/clave").location


def test_cp25_catalogos(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)

    texto = cliente_http.get("/salones").get_data(as_text=True)
    assert texto.count('class="panel salon') == 3

    respuesta = cliente_http.post("/salones/1", data={
        "nombre": "Salón Principal", "capacidad_maxima": "260", "costo_renta": "19500.50", "disponible": "S"})
    assert respuesta.status_code == 302
    assert "19,500.50" in cliente_http.get("/salones").get_data(as_text=True)

    respuesta = cliente_http.post("/paquetes/nuevo", data={
        "nombre": "Paquete Prueba " + correo[:6], "precio_persona": "300", "tipo": "ESTANDAR",
        "platillos": ["1", "4", "10"]})
    assert respuesta.status_code == 302

    respuesta = cliente_http.post("/paquetes/nuevo", data={
        "nombre": "Sin menú", "precio_persona": "300", "tipo": "ESTANDAR"})
    assert "al menos un platillo" in respuesta.get_data(as_text=True)

    respuesta = cliente_http.post("/paquetes/nuevo", data={
        "nombre": "Personalizado", "precio_persona": "300", "tipo": "PERSONALIZADO", "platillos": ["1"]})
    assert "necesita un cliente" in respuesta.get_data(as_text=True)          # CP-06 desde la interfaz


def test_platillo_en_paquete_no_se_elimina(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    cliente_http.post("/platillos/1/eliminar")          # "Crema de elote" está en un paquete
    assert "forma parte de uno o más paquetes" in cliente_http.get("/platillos").get_data(as_text=True)
