"""
Administración de conexiones y transacciones.

C-10 · IE-01 · RNF-05 · RNF-08 · RNF-11
- Pool de conexiones con verificación previa: el nivel gratuito de Neon
  suspende la instancia por inactividad y deja conexiones muertas en el
  pool. ConnectionPool.check_connection prueba cada conexión antes de
  entregarla y descarta las que ya no responden, de modo que el usuario
  no pierde su sesión (CP-20).
- Toda operación se ejecuta dentro de una transacción: o se guarda todo
  o no se guarda nada (RNF-08, DA-05).
"""
import logging
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.datos.errores import ErrorConexion, traducir_error

log = logging.getLogger(__name__)


class BaseDatos:
    """Fachada única hacia PostgreSQL (patrón Singleton a nivel de clase)."""

    _pool: ConnectionPool | None = None

    @classmethod
    def iniciar(cls, url: str, minimo: int = 1, maximo: int = 5) -> None:
        if cls._pool is not None:
            return
        cls._pool = ConnectionPool(
            conninfo=url,
            min_size=minimo,
            max_size=maximo,
            open=False,
            check=ConnectionPool.check_connection,   # RNF-11
            max_idle=300,                            # suelta conexiones ociosas
            kwargs={"row_factory": dict_row, "connect_timeout": 10},
            name="pool-salon",
        )
        # wait=False: la app arranca aunque la base esté despertando.
        cls._pool.open(wait=False)
        log.info("Pool de conexiones iniciado (%s-%s)", minimo, maximo)

    @classmethod
    def cerrar(cls) -> None:
        if cls._pool is not None:
            cls._pool.close()
            cls._pool = None

    @classmethod
    @contextmanager
    def transaccion(cls) -> Iterator[psycopg.Cursor]:
        """
        Abre una transacción y entrega un cursor.

        Uso:
            with BaseDatos.transaccion() as cur:
                RepositorioUsuarios(cur).insertar(...)
                RepositorioBitacora(cur).registrar(...)

        Al salir sin excepción hace COMMIT; ante cualquier excepción hace
        ROLLBACK y traduce el error de la base a una excepción del dominio.
        """
        if cls._pool is None:
            raise ErrorConexion("La conexión a la base de datos no está iniciada.")
        try:
            with cls._pool.connection(timeout=15) as conexion:
                with conexion.cursor() as cursor:
                    yield cursor
        except psycopg.Error as error:
            # Incluye PoolTimeout, que hereda de OperationalError.
            raise traducir_error(error) from error
