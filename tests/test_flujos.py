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

    assert 'name="nombre"' in cliente_http.get("/clientes/nuevo").get_data(as_text=True)   # formulario de alta

    respuesta = cliente_http.post("/clientes/nuevo", data={"nombre": "Laura Díaz", "telefono": celular})
    texto = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200 and "Cliente registrado: Laura Díaz" in texto
    assert "no volverá a mostrarse" in texto
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


def test_cambio_de_clave_cierra_las_demas_sesiones(app, crear_usuario):
    """RF-10: una sesión abierta con la clave anterior deja de valer."""
    otra_pc, esta_pc, gerente_http = app.test_client(), app.test_client(), app.test_client()
    id_cliente, correo, clave = crear_usuario("CLIENTE")
    _entrar(otra_pc, correo, clave)
    _entrar(esta_pc, correo, clave)

    respuesta = esta_pc.post("/clave", data={
        "clave_actual": clave, "clave_nueva": "Otra-2026", "confirmacion": "Otra-2026"})
    assert respuesta.location.endswith("/mis-eventos")
    assert esta_pc.get("/mis-eventos").status_code == 200            # quien cambió sigue dentro
    assert "/login" in otra_pc.get("/mis-eventos").location          # la otra sesión ya no

    _, correo_g, clave_g = crear_usuario("GERENTE")
    _entrar(gerente_http, correo_g, clave_g)
    gerente_http.post(f"/clientes/{id_cliente}/clave")
    assert "/login" in esta_pc.get("/mis-eventos").location          # regeneración del gerente


def test_editar_paquete_reemplaza_el_menu(cliente_http, crear_usuario):
    from app.datos.conexion import BaseDatos
    _, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    nombre = "Editable " + correo[:8]
    cliente_http.post("/paquetes/nuevo", data={
        "nombre": nombre, "precio_persona": "300", "tipo": "ESTANDAR", "platillos": ["1", "4"]})
    with BaseDatos.transaccion() as cur:
        cur.execute("SELECT id_paquete FROM paquete WHERE nombre = %s", (nombre,))
        id_paquete = cur.fetchone()["id_paquete"]

    respuesta = cliente_http.post(f"/paquetes/{id_paquete}", data={
        "nombre": nombre, "precio_persona": "350", "tipo": "ESTANDAR", "platillos": ["4", "10"]})
    assert respuesta.status_code == 302
    # Si la validación falla, el menú anterior queda intacto (misma transacción).
    respuesta = cliente_http.post(f"/paquetes/{id_paquete}", data={
        "nombre": nombre, "precio_persona": "NaN", "tipo": "ESTANDAR", "platillos": ["1"]})
    assert respuesta.status_code == 422

    with BaseDatos.transaccion() as cur:
        cur.execute("SELECT id_platillo FROM paquete_platillo WHERE id_paquete = %s ORDER BY 1",
                    (id_paquete,))
        assert [f["id_platillo"] for f in cur.fetchall()] == [4, 10]
        cur.execute("SELECT precio_persona FROM paquete WHERE id_paquete = %s", (id_paquete,))
        assert str(cur.fetchone()["precio_persona"]) == "350.00"


def test_buscar_celular_con_espacios(cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("GERENTE")
    _entrar(cliente_http, correo, clave)
    telefono = telefono_unico()
    cliente_http.post("/clientes/nuevo", data={"nombre": "Celular Espacios", "correo": "", "telefono": telefono})
    legible = f"{telefono[:3]} {telefono[3:6]} {telefono[6:]}"         # como se ve en la tabla
    assert "Celular Espacios" in cliente_http.get("/clientes", query_string={"q": legible}).get_data(as_text=True)
