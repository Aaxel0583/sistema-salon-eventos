"""
Configuración común de pruebas.

Las pruebas unitarias no tocan la base. Las de integración (marcadas
`integracion`) reinstalan el esquema en TEST_DATABASE_URL al inicio de la
sesión: NUNCA apuntes esa variable a la base real.
"""
import os
import uuid
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()
URL_PRUEBAS = os.getenv("TEST_DATABASE_URL")
CARPETA_BD = Path(__file__).resolve().parent.parent / "basedatos"


def pytest_collection_modifyitems(config, items):
    if URL_PRUEBAS:
        return
    saltar = pytest.mark.skip(reason="Define TEST_DATABASE_URL para las pruebas de integración")
    for item in items:
        if "integracion" in item.keywords:
            item.add_marker(saltar)


@pytest.fixture(scope="session")
def base_pruebas():
    import psycopg
    with psycopg.connect(URL_PRUEBAS, autocommit=True) as conexion:
        for script in ("00_limpiar.sql", "01_esquema.sql", "02_reglas_sprint1.sql", "03_semilla.sql"):
            conexion.execute((CARPETA_BD / script).read_text(encoding="utf-8"))
    return URL_PRUEBAS


@pytest.fixture
def conexion(base_pruebas):
    """Conexión directa por SQL, para probar las reglas sin la aplicación (DA-01)."""
    import psycopg
    from psycopg.rows import dict_row
    with psycopg.connect(base_pruebas, row_factory=dict_row) as con:
        yield con
        con.rollback()


@pytest.fixture(scope="session")
def app(base_pruebas):
    os.environ["DATABASE_URL"] = base_pruebas
    os.environ.setdefault("SECRET_KEY", "pruebas")
    from app import create_app
    aplicacion = create_app()
    aplicacion.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    return aplicacion


@pytest.fixture
def cliente_http(app):
    return app.test_client()


def correo_unico(prefijo: str = "u") -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:8]}@prueba.mx"


def telefono_unico() -> str:
    return "49" + str(uuid.uuid4().int)[:8]


@pytest.fixture
def crear_usuario(base_pruebas):
    """Crea un usuario directamente y devuelve (identificador, clave)."""
    from app.datos.conexion import BaseDatos
    from app.datos.repositorio_usuarios import RepositorioUsuarios
    from app.seguridad import claves

    def _crear(rol="CLIENTE", clave="Inicial-1", requiere_cambio=False, correo=None):
        correo = correo or correo_unico(rol.lower())
        with BaseDatos.transaccion() as cur:
            repo = RepositorioUsuarios(cur)
            id_usuario = repo.insertar(f"Prueba {rol}", correo, None, rol, claves.cifrar(clave))
            if not requiere_cambio:
                repo.actualizar_clave(id_usuario, claves.cifrar(clave), requiere_cambio=False)
        return id_usuario, correo, clave
    return _crear
