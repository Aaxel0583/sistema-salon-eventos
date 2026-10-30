"""
Reglas impuestas en la base, probadas por SQL directo (DA-01, RNF-09).
Casos del SRS Anexo C: CP-03 (parte de BD), CP-04, CP-05, CP-06, CP-23.
"""
import psycopg
import pytest

pytestmark = pytest.mark.integracion


def _sqlstate(error) -> str:
    return error.value.sqlstate


def test_cp04_rechaza_cuarto_salon(conexion):
    with pytest.raises(psycopg.Error) as error:
        conexion.execute("INSERT INTO salon (nombre, capacidad_maxima, costo_renta) VALUES ('Cuarto', 50, 1000)")
    assert _sqlstate(error) == "BF003"


def test_cp05_rechaza_reducir_capacidad_bajo_aforo_agendado(conexion):
    cliente = conexion.execute(
        "INSERT INTO usuario (nombre, correo, rol, clave_hash) VALUES ('C', 'cp05@prueba.mx', 'CLIENTE', 'x') RETURNING id_usuario"
    ).fetchone()["id_usuario"]
    salon = conexion.execute("SELECT id_salon, capacidad_maxima FROM salon ORDER BY id_salon LIMIT 1").fetchone()
    conexion.execute(
        """INSERT INTO evento (clave_proyecto, id_cliente, id_salon, fecha_evento, hora_inicio,
                               hora_fin, num_asistentes, costo_total)
           VALUES ('EVT-2099-0001', %s, %s, CURRENT_DATE + 30, '14:00', '19:00', 80, 1000)""",
        (cliente, salon["id_salon"]),
    )
    # Bajar a 80 sí se permite (igual al aforo agendado)...
    conexion.execute("UPDATE salon SET capacidad_maxima = 80 WHERE id_salon = %s", (salon["id_salon"],))
    # ...bajar a 79 no.
    with pytest.raises(psycopg.Error) as error:
        conexion.execute("UPDATE salon SET capacidad_maxima = 79 WHERE id_salon = %s", (salon["id_salon"],))
    assert _sqlstate(error) == "BF004"
    assert "80 asistentes" in error.value.diag.message_primary


def test_cp05_evento_cancelado_no_bloquea_reduccion(conexion):
    cliente = conexion.execute(
        "INSERT INTO usuario (nombre, telefono, rol, clave_hash) VALUES ('C', '4920000005', 'CLIENTE', 'x') RETURNING id_usuario"
    ).fetchone()["id_usuario"]
    salon = conexion.execute("SELECT id_salon FROM salon ORDER BY id_salon DESC LIMIT 1").fetchone()["id_salon"]
    conexion.execute(
        """INSERT INTO evento (clave_proyecto, id_cliente, id_salon, fecha_evento, hora_inicio,
                               hora_fin, num_asistentes, costo_total, estado)
           VALUES ('EVT-2099-0002', %s, %s, CURRENT_DATE + 10, '14:00', '19:00', 85, 1, 'CANCELADO')""",
        (cliente, salon),
    )
    conexion.execute("UPDATE salon SET capacidad_maxima = 10 WHERE id_salon = %s", (salon,))


def test_cp06_paquete_personalizado_sin_cliente(conexion):
    with pytest.raises(psycopg.errors.CheckViolation) as error:
        conexion.execute("INSERT INTO paquete (nombre, precio_persona, tipo) VALUES ('X', 100, 'PERSONALIZADO')")
    assert error.value.diag.constraint_name == "ck_paquete_dueno"


def test_rn06_usuario_sin_contacto(conexion):
    with pytest.raises(psycopg.errors.CheckViolation) as error:
        conexion.execute("INSERT INTO usuario (nombre, rol, clave_hash) VALUES ('Sin contacto', 'CLIENTE', 'x')")
    assert error.value.diag.constraint_name == "ck_usuario_contacto"


def test_rn07_celular_unico(conexion):
    conexion.execute("INSERT INTO usuario (nombre, telefono, rol, clave_hash) VALUES ('A', '4929999999', 'CLIENTE', 'x')")
    with pytest.raises(psycopg.errors.UniqueViolation) as error:
        conexion.execute("INSERT INTO usuario (nombre, telefono, rol, clave_hash) VALUES ('B', '4929999999', 'CLIENTE', 'x')")
    assert error.value.diag.constraint_name == "uq_usuario_telefono"


def test_rnf18_bitacora_no_se_borra(conexion):
    conexion.execute("INSERT INTO bitacora (accion, entidad) VALUES ('PRUEBA', 'x')")
    with pytest.raises(psycopg.Error):
        conexion.execute("DELETE FROM bitacora")
