"""
Repositorios de los catálogos operativos: SALON, PLATILLO, PAQUETE y
PAQUETE_PLATILLO (HU-003, HU-004).

C-10 · RNF-05 · DA-02
"""
from psycopg import Cursor

from app.dominio.modelos import Paquete, Platillo, Salon


class RepositorioSalones:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    _SELECT = """
        SELECT s.id_salon, s.nombre, s.descripcion, s.capacidad_maxima,
               s.costo_renta, s.disponible,
               (SELECT MAX(e.num_asistentes)
                  FROM evento e
                 WHERE e.id_salon = s.id_salon
                   AND e.estado IN ('COTIZACION', 'CONFIRMADO')
                   AND e.fecha_evento >= CURRENT_DATE) AS mayor_aforo_agendado
          FROM salon s"""

    def listar(self) -> list[Salon]:
        self._cur.execute(self._SELECT + " ORDER BY s.id_salon")
        return [Salon.desde_fila(f) for f in self._cur.fetchall()]

    def por_id(self, id_salon: int) -> Salon | None:
        self._cur.execute(self._SELECT + " WHERE s.id_salon = %s", (id_salon,))
        fila = self._cur.fetchone()
        return Salon.desde_fila(fila) if fila else None

    def actualizar(self, id_salon: int, nombre: str, descripcion: str | None,
                   capacidad: int, costo_renta, disponible: str) -> bool:
        """Las reglas BF004 (capacidad) las impone el trigger, no este código."""
        self._cur.execute(
            """UPDATE salon
                  SET nombre = %s, descripcion = %s, capacidad_maxima = %s,
                      costo_renta = %s, disponible = %s
                WHERE id_salon = %s""",
            (nombre, descripcion, capacidad, costo_renta, disponible, id_salon),
        )
        return self._cur.rowcount == 1


class RepositorioPlatillos:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    def listar(self) -> list[Platillo]:
        self._cur.execute(
            "SELECT id_platillo, nombre, categoria FROM platillo ORDER BY categoria, nombre"
        )
        return [Platillo.desde_fila(f) for f in self._cur.fetchall()]

    def por_id(self, id_platillo: int) -> Platillo | None:
        self._cur.execute(
            "SELECT id_platillo, nombre, categoria FROM platillo WHERE id_platillo = %s",
            (id_platillo,),
        )
        fila = self._cur.fetchone()
        return Platillo.desde_fila(fila) if fila else None

    def insertar(self, nombre: str, categoria: str) -> int:
        self._cur.execute(
            "INSERT INTO platillo (nombre, categoria) VALUES (%s, %s) RETURNING id_platillo",
            (nombre, categoria),
        )
        return self._cur.fetchone()["id_platillo"]

    def actualizar(self, id_platillo: int, nombre: str, categoria: str) -> bool:
        self._cur.execute(
            "UPDATE platillo SET nombre = %s, categoria = %s WHERE id_platillo = %s",
            (nombre, categoria, id_platillo),
        )
        return self._cur.rowcount == 1

    def eliminar(self, id_platillo: int) -> bool:
        """La FK fk_pp_platillo impide borrar un platillo que está en un paquete."""
        self._cur.execute("DELETE FROM platillo WHERE id_platillo = %s", (id_platillo,))
        return self._cur.rowcount == 1

    def contar_existentes(self, ids: list[int]) -> int:
        self._cur.execute(
            "SELECT COUNT(*) AS total FROM platillo WHERE id_platillo = ANY(%s)",
            (ids,),
        )
        return self._cur.fetchone()["total"]


class RepositorioPaquetes:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    _SELECT = """
        SELECT p.id_paquete, p.nombre, p.precio_persona, p.tipo, p.id_cliente,
               u.nombre AS nombre_cliente
          FROM paquete p
          LEFT JOIN usuario u ON u.id_usuario = p.id_cliente"""

    def listar(self) -> list[Paquete]:
        self._cur.execute(self._SELECT + " ORDER BY p.tipo, p.nombre")
        paquetes = [Paquete.desde_fila(f) for f in self._cur.fetchall()]
        self._cargar_platillos(paquetes)
        return paquetes

    def por_id(self, id_paquete: int) -> Paquete | None:
        self._cur.execute(self._SELECT + " WHERE p.id_paquete = %s", (id_paquete,))
        fila = self._cur.fetchone()
        if not fila:
            return None
        paquete = Paquete.desde_fila(fila)
        self._cargar_platillos([paquete])
        return paquete

    def _cargar_platillos(self, paquetes: list[Paquete]) -> None:
        """Una sola consulta para todos los paquetes (evita N+1)."""
        if not paquetes:
            return
        indice = {p.id_paquete: p for p in paquetes}
        self._cur.execute(
            """SELECT pp.id_paquete, pl.id_platillo, pl.nombre, pl.categoria
                 FROM paquete_platillo pp
                 JOIN platillo pl ON pl.id_platillo = pp.id_platillo
                WHERE pp.id_paquete = ANY(%s)
                ORDER BY pl.categoria, pl.nombre""",
            (list(indice),),
        )
        for fila in self._cur.fetchall():
            indice[fila["id_paquete"]].platillos.append(Platillo.desde_fila(fila))

    def insertar(self, nombre: str, precio: object, tipo: str, id_cliente: int | None) -> int:
        self._cur.execute(
            """INSERT INTO paquete (nombre, precio_persona, tipo, id_cliente)
               VALUES (%s, %s, %s, %s) RETURNING id_paquete""",
            (nombre, precio, tipo, id_cliente),
        )
        return self._cur.fetchone()["id_paquete"]

    def actualizar(self, id_paquete: int, nombre: str, precio: object,
                   tipo: str, id_cliente: int | None) -> bool:
        self._cur.execute(
            """UPDATE paquete
                  SET nombre = %s, precio_persona = %s, tipo = %s, id_cliente = %s
                WHERE id_paquete = %s""",
            (nombre, precio, tipo, id_cliente, id_paquete),
        )
        return self._cur.rowcount == 1

    def reemplazar_platillos(self, id_paquete: int, ids_platillo: list[int]) -> None:
        """Se ejecuta dentro de la misma transacción que el paquete (Escenario 4)."""
        self._cur.execute("DELETE FROM paquete_platillo WHERE id_paquete = %s", (id_paquete,))
        self._cur.executemany(
            "INSERT INTO paquete_platillo (id_paquete, id_platillo) VALUES (%s, %s)",
            [(id_paquete, i) for i in ids_platillo],
        )

    def eliminar(self, id_paquete: int) -> bool:
        self._cur.execute("DELETE FROM paquete WHERE id_paquete = %s", (id_paquete,))
        return self._cur.rowcount == 1

    def contar(self) -> int:
        self._cur.execute("SELECT COUNT(*) AS total FROM paquete")
        return self._cur.fetchone()["total"]
