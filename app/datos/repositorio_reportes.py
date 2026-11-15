"""
Repositorio de los reportes operativos · C-10 · HU-010 a HU-012

Lee las vistas IB-08 (cartera con semáforo) e IB-09 (proyectos activos y
realizados). El semáforo, el saldo y los totales se calculan en la base:
aquí solo se filtra y se ordena. Cada filtro es un fragmento fijo con su
parámetro; ningún valor se concatena al SQL (RNF-05).
"""
from datetime import date

from psycopg import Cursor

from app.datos.repositorio_eventos import COLUMNAS_APARTADO
from app.dominio.modelos import CuentaCartera, Evento, ProyectoActivo


class RepositorioReportes:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    # ------------------------- IB-08 · Cartera -------------------------
    def cartera(self, semaforo: str | None = None) -> list[CuentaCartera]:
        """RF-37 · De lo más urgente a lo menos: por fecha del evento."""
        condicion, parametros = ("WHERE semaforo = %s", (semaforo,)) if semaforo else ("", ())
        self._cur.execute(
            f"""SELECT * FROM vw_cartera
                {condicion}
                ORDER BY fecha_evento, hora_inicio, id_evento""",
            parametros,
        )
        return [CuentaCartera.desde_fila(f) for f in self._cur.fetchall()]

    def totales_cartera(self) -> dict[str, dict]:
        """RF-37 · Cuentas y total adeudado por categoría del semáforo: {'VENCIDA': {...}, ...}."""
        self._cur.execute(
            """SELECT semaforo, COUNT(*)::INTEGER AS cuentas, COALESCE(SUM(saldo), 0) AS adeudo
                 FROM vw_cartera
                GROUP BY semaforo"""
        )
        return {f["semaforo"]: f for f in self._cur.fetchall()}

    # --------------------- IB-09 · Proyectos activos ---------------------
    def activos(self, estado: str | None = None, id_salon: int | None = None) -> list[ProyectoActivo]:
        """RF-35 · Ordenado por fecha del evento."""
        condiciones, parametros = [], []
        if estado:
            condiciones.append("estado = %s")
            parametros.append(estado)
        if id_salon:
            condiciones.append("id_salon = %s")
            parametros.append(id_salon)
        donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        self._cur.execute(
            f"""SELECT v.*, {COLUMNAS_APARTADO} FROM vw_proyectos_activos v
                {donde}
                ORDER BY fecha_evento, hora_inicio, id_evento""",
            parametros,
        )
        return [ProyectoActivo.desde_fila(f) for f in self._cur.fetchall()]

    # -------------------- IB-09 · Proyectos realizados --------------------
    def realizados(self, desde: date | None = None, hasta: date | None = None,
                   liquidacion: str | None = None) -> list[Evento]:
        """RF-36 · Del más reciente al más antiguo."""
        condiciones, parametros = [], []
        if desde:
            condiciones.append("fecha_evento >= %s")
            parametros.append(desde)
        if hasta:
            condiciones.append("fecha_evento <= %s")
            parametros.append(hasta)
        if liquidacion == "CON_SALDO":
            condiciones.append("saldo > 0")
        elif liquidacion == "FINIQUITADO":
            condiciones.append("finiquitado = 'S'")
        donde = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
        self._cur.execute(
            f"""SELECT * FROM vw_proyectos_realizados
                {donde}
                ORDER BY fecha_evento DESC, hora_inicio, id_evento""",
            parametros,
        )
        return [Evento.desde_fila(f) for f in self._cur.fetchall()]
