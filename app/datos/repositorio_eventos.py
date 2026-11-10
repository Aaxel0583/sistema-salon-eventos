"""
Repositorio de EVENTO y de las vistas IB-01, IB-10 e IB-11.

C-10 · RNF-05 · DA-02 · HU-005 a HU-008
La clave de proyecto (IB-07) y el costo (RN-09) los asigna la base al
insertar: este repositorio no los calcula ni los envía. El aforo (IB-02)
y la disponibilidad (IB-03) los valida la base: aquí solo se consulta la
agenda para mostrarla (RF-24).
"""
from datetime import date, time

from psycopg import Cursor

from app.dominio.modelos import (ESTADO_CANCELADO, ESTADOS_ABIERTOS, Evento,
                                 OcupacionSalon, Pago)

LIMITE_LISTADO = 200        # filas del listado; la pantalla avisa al llegar aquí


def _patron_busqueda(texto: str) -> str:
    """Escapa los comodines para que "%" o "_" se busquen literalmente."""
    limpio = texto.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{limpio}%"


class RepositorioEventos:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    # ---------------------------- consultas ----------------------------
    def hoy(self) -> date:
        """
        La fecha de hoy según la base (zona America/Mexico_City, ver conexion.py).
        Se usa la misma referencia que las vistas IB-10 e IB-11, de modo que
        la aplicación y el tablero nunca discrepen sobre qué evento ya pasó.
        """
        self._cur.execute("SELECT CURRENT_DATE AS hoy")
        return self._cur.fetchone()["hoy"]

    def por_id(self, id_evento: int) -> Evento | None:
        self._cur.execute("SELECT * FROM vw_evento_detalle WHERE id_evento = %s", (id_evento,))
        fila = self._cur.fetchone()
        return Evento.desde_fila(fila) if fila else None

    def bloquear(self, id_evento: int) -> bool:
        """Toma la fila con FOR UPDATE para que dos cambios simultáneos no se pisen."""
        self._cur.execute("SELECT id_evento FROM evento WHERE id_evento = %s FOR UPDATE", (id_evento,))
        return self._cur.fetchone() is not None

    def listar(self, estado: str | None = None, id_salon: int | None = None,
               texto: str = "", limite: int = LIMITE_LISTADO) -> list[Evento]:
        """
        RF-28 · Listado con filtros por estatus, salón y texto (clave, nombre
        del evento o cliente). Cada filtro es un fragmento fijo con su
        parámetro: ningún valor se concatena al SQL (RNF-05).
        Orden: primero los próximos (del más cercano al más lejano) y
        después los pasados (del más reciente al más antiguo).
        """
        condiciones, parametros = [], []
        if estado:
            condiciones.append("estado = %s")
            parametros.append(estado)
        if id_salon:
            condiciones.append("id_salon = %s")
            parametros.append(id_salon)
        if texto.strip():
            patron = _patron_busqueda(texto)
            condiciones.append("(LOWER(clave_proyecto) LIKE %s OR LOWER(COALESCE(nombre_evento, '')) LIKE %s"
                               " OR LOWER(nombre_cliente) LIKE %s)")
            parametros += [patron, patron, patron]
        donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        self._cur.execute(
            f"""SELECT * FROM vw_evento_detalle
                {donde}
                ORDER BY (fecha_evento < CURRENT_DATE),
                         CASE WHEN fecha_evento >= CURRENT_DATE THEN fecha_evento END ASC,
                         fecha_evento DESC, hora_inicio, id_evento
                LIMIT %s""",
            (*parametros, limite),
        )
        return [Evento.desde_fila(f) for f in self._cur.fetchall()]

    def agenda(self, id_salon: int, fecha_evento: date) -> list[Evento]:
        """
        RF-24 · Eventos que ocupan el salón en una fecha, por hora de inicio.
        Un evento cancelado no ocupa el salón (RN-02). Se apoya en el índice
        ix_evento_salon_fecha (RNF-02).
        """
        self._cur.execute(
            """SELECT * FROM vw_evento_detalle
                WHERE id_salon = %s AND fecha_evento = %s AND estado <> %s
                ORDER BY hora_inicio, id_evento""",
            (id_salon, fecha_evento, ESTADO_CANCELADO),
        )
        return [Evento.desde_fila(f) for f in self._cur.fetchall()]

    def de_cliente(self, id_cliente: int) -> list[Evento]:
        """
        RF-39 · Eventos de los que el cliente es titular. El filtro por
        titular va en la consulta, no en la plantilla (RNF-06). Mismo orden
        que el listado: primero los próximos, después los pasados.
        """
        self._cur.execute(
            """SELECT * FROM vw_evento_detalle
                WHERE id_cliente = %s
                ORDER BY (fecha_evento < CURRENT_DATE),
                         CASE WHEN fecha_evento >= CURRENT_DATE THEN fecha_evento END ASC,
                         fecha_evento DESC, hora_inicio, id_evento""",
            (id_cliente,),
        )
        return [Evento.desde_fila(f) for f in self._cur.fetchall()]

    def por_clave_de_cliente(self, clave_proyecto: str, id_cliente: int) -> Evento | None:
        """
        RF-39, RNF-06 · El evento solo se encuentra si la clave Y el titular
        coinciden: para quien no es su dueño, un evento ajeno y uno que no
        existe son lo mismo.
        """
        self._cur.execute(
            "SELECT * FROM vw_evento_detalle WHERE clave_proyecto = %s AND id_cliente = %s",
            (clave_proyecto, id_cliente),
        )
        fila = self._cur.fetchone()
        return Evento.desde_fila(fila) if fila else None

    def pagos(self, id_evento: int) -> list[Pago]:
        """RF-40 · Abonos del evento, del más antiguo al más reciente."""
        self._cur.execute(
            """SELECT id_pago, id_evento, monto, tipo, referencia, fecha_pago
                 FROM pago
                WHERE id_evento = %s
                ORDER BY fecha_pago, id_pago""",
            (id_evento,),
        )
        return [Pago.desde_fila(f) for f in self._cur.fetchall()]

    def pendientes_cierre(self) -> list[Evento]:
        """IB-11 · RN-14."""
        self._cur.execute("SELECT * FROM vw_pendientes_cierre ORDER BY fecha_evento, hora_inicio")
        return [Evento.desde_fila(f) for f in self._cur.fetchall()]

    def ocupacion_por_salon(self) -> list[OcupacionSalon]:
        """IB-10."""
        self._cur.execute("SELECT * FROM vw_ocupacion_salon ORDER BY id_salon")
        return [OcupacionSalon.desde_fila(f) for f in self._cur.fetchall()]

    def indicadores(self) -> dict:
        """
        Cifras del tablero (IU-03), todas sobre la vista IB-01:
        - activos: eventos en cotización o confirmados.
        - por_cobrar: saldo de los eventos confirmados y realizados (compromisos
          firmes); una cotización todavía no es una cuenta por cobrar.
        - finiquitados: eventos con la marca de finiquito.
        """
        self._cur.execute(
            """SELECT COUNT(*) FILTER (WHERE estado = ANY(%s))                         AS activos,
                      COALESCE(SUM(saldo) FILTER (WHERE estado IN ('CONFIRMADO', 'REALIZADO')
                                                    AND finiquitado = 'N'), 0)        AS por_cobrar,
                      COUNT(*) FILTER (WHERE finiquitado = 'S')                       AS finiquitados
                 FROM vw_evento_detalle""",
            (list(ESTADOS_ABIERTOS),),
        )
        return self._cur.fetchone()

    # --------------------------- operaciones ---------------------------
    def insertar(self, id_cliente: int, id_gerente: int, id_salon: int, id_paquete: int,
                 nombre_evento: str | None, fecha_evento: date, hora_inicio: time,
                 hora_fin: time, num_asistentes: int) -> int:
        """
        El estado inicial es COTIZACION (DEFAULT de la tabla). La clave y el
        costo los llenan los triggers trg_evento_clave y trg_evento_costo.
        """
        self._cur.execute(
            """INSERT INTO evento (id_cliente, id_gerente, id_salon, id_paquete, nombre_evento,
                                   fecha_evento, hora_inicio, hora_fin, num_asistentes)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id_evento""",
            (id_cliente, id_gerente, id_salon, id_paquete, nombre_evento,
             fecha_evento, hora_inicio, hora_fin, num_asistentes),
        )
        return self._cur.fetchone()["id_evento"]

    def actualizar_estado(self, id_evento: int, estado: str) -> bool:
        """RN-11 lo vigila ck_evento_estado. La bandera de finiquito no se toca."""
        self._cur.execute("UPDATE evento SET estado = %s WHERE id_evento = %s", (estado, id_evento))
        return self._cur.rowcount == 1

    def asignar_gerente(self, id_evento: int, id_gerente: int) -> bool:
        """RF-29."""
        self._cur.execute("UPDATE evento SET id_gerente = %s WHERE id_evento = %s",
                          (id_gerente, id_evento))
        return self._cur.rowcount == 1
