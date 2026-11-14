"""
CP-20 · Recuperación de conexión (RNF-11).
El servidor cierra a la fuerza las conexiones de la aplicación, como hace
el nivel gratuito de Neon al suspender la instancia. El sistema debe
restablecer la conexión por su cuenta, sin que el usuario pierda la sesión.
"""
import psycopg
import pytest

pytestmark = pytest.mark.integracion


def _cerrar_conexiones_de_la_aplicacion(url) -> int:
    with psycopg.connect(url, autocommit=True) as con:
        return con.execute(
            """SELECT COUNT(pg_terminate_backend(pid))
                 FROM pg_stat_activity
                WHERE datname = current_database() AND pid <> pg_backend_pid()"""
        ).fetchone()[0]


def test_cp20_la_sesion_sobrevive_al_cierre_de_conexiones(base_pruebas, cliente_http, crear_usuario):
    _, correo, clave = crear_usuario("GERENTE")
    cliente_http.post("/login", data={"identificador": correo, "clave": clave})
    assert cliente_http.get("/panel").status_code == 200

    assert _cerrar_conexiones_de_la_aplicacion(base_pruebas) >= 1

    for ruta in ("/panel", "/eventos", "/reportes/cartera"):          # sigue autenticado y con datos
        respuesta = cliente_http.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert "Cerrar sesión" in respuesta.get_data(as_text=True)
