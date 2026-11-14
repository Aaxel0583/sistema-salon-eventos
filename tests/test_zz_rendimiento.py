"""
Sprint 3 · RNF-03: los reportes operativos se despliegan en menos de 5
segundos con 500 eventos registrados.

Va al final de la corrida (por eso el nombre del archivo): los 500 eventos
que inserta se quedan en la base de pruebas.
"""
import time

import pytest

from app.datos.conexion import BaseDatos

pytestmark = pytest.mark.integracion

EVENTOS = 500
LIMITE_SEGUNDOS = 5


@pytest.fixture(scope="module")
def base_poblada(app):
    """500 eventos en fechas distintas: 250 confirmados con un abono, 150 realizados y 100 en cotización."""
    from app.datos.repositorio_usuarios import RepositorioUsuarios
    from app.seguridad import claves
    from tests.conftest import correo_unico
    with BaseDatos.transaccion() as cur:
        id_cliente = RepositorioUsuarios(cur).insertar("Cliente de volumen", correo_unico(), None, "CLIENTE",
                                                       claves.cifrar("Inicial-1"))
        cur.execute(
            """INSERT INTO evento (clave_proyecto, id_cliente, id_salon, id_paquete, fecha_evento,
                                   hora_inicio, hora_fin, num_asistentes, costo_total)
               SELECT 'X', %s, 2, 1, CURRENT_DATE - 7000 + g * 20, '20:00', '23:00', 30, 0
                 FROM generate_series(1, %s) g
               RETURNING id_evento""", (id_cliente, EVENTOS))
        ids = [f["id_evento"] for f in cur.fetchall()]
        cur.execute("UPDATE evento SET estado = 'REALIZADO' WHERE id_evento = ANY(%s)", (ids[:150],))
        cur.execute("UPDATE evento SET estado = 'CONFIRMADO' WHERE id_evento = ANY(%s)", (ids[150:400],))
        cur.execute("SELECT fn_registrar_pago(id_evento, 1000, 'EFECTIVO') FROM evento WHERE id_evento = ANY(%s)",
                    (ids[:400],))
    return len(ids)


@pytest.mark.parametrize("ruta", ["/reportes/cartera", "/reportes/activos", "/reportes/realizados",
                                  "/reportes/cartera?formato=csv", "/panel"])
def test_rnf03_reportes_en_menos_de_5_segundos(cliente_http, crear_usuario, base_poblada, ruta):
    assert base_poblada == EVENTOS
    _, correo, clave = crear_usuario("GERENTE")
    cliente_http.post("/login", data={"identificador": correo, "clave": clave})

    inicio = time.perf_counter()
    respuesta = cliente_http.get(ruta)
    duracion = time.perf_counter() - inicio

    assert respuesta.status_code == 200
    assert len(respuesta.get_data()) > 20_000                    # sí trae los cientos de renglones
    assert duracion < LIMITE_SEGUNDOS, f"{ruta} tardó {duracion:.2f} s"
