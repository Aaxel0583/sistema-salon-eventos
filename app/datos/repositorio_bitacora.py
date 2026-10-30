"""
Repositorio de BITACORA · RF-41 · RNF-18

Solo expone inserción y consulta: no existe método para modificar ni
borrar, y la base lo impide además con trg_bitacora_inalterable.
"""
from psycopg import Cursor


class RepositorioBitacora:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    def registrar(self, id_usuario: int | None, accion: str, entidad: str) -> None:
        self._cur.execute(
            "INSERT INTO bitacora (id_usuario, accion, entidad) VALUES (%s, %s, %s)",
            (id_usuario, accion[:40], entidad[:60]),
        )

    def recientes(self, limite: int = 20) -> list[dict]:
        self._cur.execute(
            """SELECT b.fecha, b.accion, b.entidad, u.nombre AS usuario
                 FROM bitacora b
                 LEFT JOIN usuario u ON u.id_usuario = b.id_usuario
                ORDER BY b.fecha DESC, b.id_bitacora DESC
                LIMIT %s""",
            (limite,),
        )
        return self._cur.fetchall()
