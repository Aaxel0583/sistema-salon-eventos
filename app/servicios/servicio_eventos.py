"""
Motor de reservación y gestión de eventos.

C-04 Motor de reservación · HU-005 · CU-06 · RF-12, RF-20 a RF-23
C-08 Tablero del gerente ... HU-006 · CU-06 · RF-28, RF-29 · IB-10, IB-11
Escenarios 2 y 5 (Figuras 5 y 8) · Decisiones DA-01, DA-04 y DA-05

Lo que este servicio NO hace (DA-01): calcular el costo, asignar la clave
ni decidir el aforo o el traslape. La base calcula el costo (RN-09) y
asigna la clave (RN-08); el aforo (BF001) y el traslape (BF002) los
validan los triggers de HU-007. Aquí solo se valida que los datos estén
completos y bien formados, y se traduce la respuesta de la base.
"""
from dataclasses import dataclass, field
from datetime import date, time

from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorNegocio, ErrorNoEncontrado, ErrorValidacion
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_catalogos import RepositorioPaquetes, RepositorioSalones
from app.datos.repositorio_eventos import LIMITE_LISTADO, RepositorioEventos
from app.datos.repositorio_usuarios import RepositorioUsuarios
from app.dominio.modelos import (ESTADOS_EVENTO, Evento, OcupacionSalon, Paquete,
                                 Salon, Usuario)
from app.servicios.servicio_clientes import ClienteRegistrado, ServicioClientes
from app.servicios.validaciones import (entero_positivo, fecha, hora,
                                        id_seleccionado, texto_opcional)


# ---------------------------------------------------------------------
# Objetos de resultado
# ---------------------------------------------------------------------
@dataclass
class DatosReservacion:
    """Lo que IU-06 necesita para armar sus listas y el panel de cotización."""
    salones: list[Salon]
    paquetes: list[Paquete]
    clientes: list[Usuario]
    hoy: date


@dataclass
class ReservacionRegistrada:
    """Resultado de HU-005. Si se dio de alta al cliente, trae su clave inicial (RF-08)."""
    evento: Evento
    cliente_nuevo: ClienteRegistrado | None = None


@dataclass
class Tablero:
    """Contenido de IU-03."""
    indicadores: dict
    ocupacion: list[OcupacionSalon]
    pendientes: list[Evento]          # IB-11: eventos vencidos sin cerrar
    bloqueados: list[Usuario]         # Sprint 1: clientes que esperan clave nueva
    salones: list[Salon]
    clientes: int
    paquetes: int
    hoy: date
    actividad: list[dict] = field(default_factory=list)

    @property
    def salones_no_disponibles(self) -> list[Salon]:
        return [s for s in self.salones if not s.esta_disponible]

    @property
    def hay_pendientes(self) -> bool:
        return bool(self.pendientes or self.bloqueados or self.salones_no_disponibles)


@dataclass
class _Captura:
    """Datos del formulario ya validados en forma (sin tocar la base)."""
    id_salon: int
    id_paquete: int
    nombre_evento: str | None
    fecha_evento: date
    hora_inicio: time
    hora_fin: time
    num_asistentes: int


# ---------------------------------------------------------------------
# C-04 · Motor de reservación
# ---------------------------------------------------------------------
class ServicioReservaciones:

    def __init__(self, clientes: ServicioClientes | None = None):
        self._clientes = clientes or ServicioClientes()

    def datos_formulario(self) -> DatosReservacion:
        with BaseDatos.transaccion() as cur:
            return DatosReservacion(
                salones=RepositorioSalones(cur).listar(),
                paquetes=RepositorioPaquetes(cur).listar(),
                clientes=RepositorioUsuarios(cur).buscar_clientes("", limite=None),
                hoy=RepositorioEventos(cur).hoy(),
            )

    @staticmethod
    def _validar_captura(datos: dict) -> _Captura:
        """Formato y completitud, en el orden en que aparecen los campos en IU-06."""
        captura = _Captura(
            id_salon=id_seleccionado(datos.get("id_salon"), "Salón"),
            id_paquete=id_seleccionado(datos.get("id_paquete"), "Paquete"),
            nombre_evento=texto_opcional(datos.get("nombre_evento"), 120),
            fecha_evento=fecha(datos.get("fecha_evento"), "Fecha"),
            hora_inicio=hora(datos.get("hora_inicio"), "Inicio"),
            hora_fin=hora(datos.get("hora_fin"), "Término"),
            num_asistentes=entero_positivo(datos.get("num_asistentes"), "Invitados"),
        )
        if captura.hora_fin <= captura.hora_inicio:
            raise ErrorValidacion(
                f"La hora de término ({captura.hora_fin:%H:%M}) debe ser posterior a la de inicio "
                f"({captura.hora_inicio:%H:%M}). Un evento no puede pasar de la medianoche."
            )
        return captura

    def registrar(self, id_gerente: int, datos: dict) -> ReservacionRegistrada:
        """
        CU-06 · Registrar y cotizar evento.

        `datos["cliente_nuevo"] == "S"` da de alta al cliente con nombre,
        correo y celular en la MISMA transacción que el evento (RF-12,
        DA-05, Escenario 2): si el evento se rechaza, el cliente tampoco
        queda guardado y su correo o celular no se ocupa.
        """
        captura = self._validar_captura(datos)
        cliente_nuevo = datos.get("cliente_nuevo") == "S"
        if cliente_nuevo:
            # Se valida antes de abrir la transacción para avisar pronto.
            self._clientes.preparar_datos(datos.get("nombre", ""), datos.get("correo", ""),
                                          datos.get("telefono", ""))
        else:
            id_cliente = id_seleccionado(datos.get("id_cliente"), "Cliente")

        with BaseDatos.transaccion() as cur:
            eventos = RepositorioEventos(cur)
            if captura.fecha_evento < eventos.hoy():
                raise ErrorValidacion(
                    f"La fecha {captura.fecha_evento:%d/%m/%Y} ya pasó. "
                    "Elige la fecha de hoy o una posterior."
                )

            registrado = None
            if cliente_nuevo:
                registrado = self._clientes.registrar_en(
                    cur, id_gerente, datos.get("nombre", ""), datos.get("correo", ""),
                    datos.get("telefono", ""),
                )
                id_cliente = registrado.id_cliente
            else:
                cliente = RepositorioUsuarios(cur).por_id(id_cliente)
                if cliente is None or not cliente.es_cliente:
                    raise ErrorValidacion("El cliente seleccionado no existe.")

            self._validar_catalogos(cur, captura, id_cliente)

            id_evento = eventos.insertar(
                id_cliente=id_cliente, id_gerente=id_gerente, id_salon=captura.id_salon,
                id_paquete=captura.id_paquete, nombre_evento=captura.nombre_evento,
                fecha_evento=captura.fecha_evento, hora_inicio=captura.hora_inicio,
                hora_fin=captura.hora_fin, num_asistentes=captura.num_asistentes,
            )
            RepositorioBitacora(cur).registrar(id_gerente, "ALTA_EVENTO", f"evento:{id_evento}")
            return ReservacionRegistrada(eventos.por_id(id_evento), registrado)

    @staticmethod
    def _validar_catalogos(cur, captura: _Captura, id_cliente: int) -> None:
        """Salón disponible y paquete aplicable a este cliente (RN-12)."""
        salon = next((s for s in RepositorioSalones(cur).listar() if s.id_salon == captura.id_salon), None)
        if salon is None:
            raise ErrorValidacion("El salón seleccionado no existe.")
        if not salon.esta_disponible:
            raise ErrorNegocio(f"El {salon.nombre} está marcado como no disponible y no recibe "
                               "reservaciones nuevas. Elige otro salón o cámbialo en Catálogos.")

        paquete = RepositorioPaquetes(cur).por_id(captura.id_paquete)
        if paquete is None:
            raise ErrorValidacion("El paquete seleccionado no existe.")
        if paquete.es_personalizado and paquete.id_cliente != id_cliente:
            raise ErrorNegocio(f"El paquete «{paquete.nombre}» es personalizado de "
                               f"{paquete.nombre_cliente} y no puede usarse para otro cliente.")


# ---------------------------------------------------------------------
# C-08 · Tablero y gestión de eventos
# ---------------------------------------------------------------------
class ServicioEventos:

    limite_listado = LIMITE_LISTADO

    def tablero(self) -> Tablero:
        """IU-03: indicadores, ocupación por salón (IB-10) y pendientes de cierre (IB-11)."""
        with BaseDatos.transaccion() as cur:
            eventos, usuarios = RepositorioEventos(cur), RepositorioUsuarios(cur)
            return Tablero(
                indicadores=eventos.indicadores(),
                ocupacion=eventos.ocupacion_por_salon(),
                pendientes=eventos.pendientes_cierre(),
                bloqueados=usuarios.clientes_bloqueados(),
                salones=RepositorioSalones(cur).listar(),
                clientes=usuarios.contar_por_rol("CLIENTE"),
                paquetes=RepositorioPaquetes(cur).contar(),
                # La fecha sale de la base: su zona horaria es la del salón (conexion.py).
                hoy=eventos.hoy(),
                # Los inicios de sesión son ruido para el gerente; siguen en la bitácora.
                actividad=RepositorioBitacora(cur).recientes(10, excluir=("INICIO_SESION",)),
            )

    def listar(self, estado: str = "", id_salon: str = "", texto: str = "") -> tuple[list[Evento], date]:
        """RF-28. Un filtro con valor desconocido se ignora en vez de fallar.
        Devuelve también la fecha de hoy para señalar los pendientes de cierre."""
        estado = estado.upper() if estado and estado.upper() in ESTADOS_EVENTO else None
        id_salon = int(id_salon) if str(id_salon).isdigit() else None
        with BaseDatos.transaccion() as cur:
            repo = RepositorioEventos(cur)
            return repo.listar(estado, id_salon, texto or ""), repo.hoy()

    def obtener(self, id_evento: int) -> tuple[Evento, Paquete | None, list[Usuario], date]:
        """Ficha del evento (IU-07): evento, paquete con su menú, gerentes y fecha de hoy."""
        with BaseDatos.transaccion() as cur:
            eventos = RepositorioEventos(cur)
            evento = eventos.por_id(id_evento)
            if evento is None:
                raise ErrorNoEncontrado("El evento no existe.")
            paquete = RepositorioPaquetes(cur).por_id(evento.id_paquete) if evento.id_paquete else None
            return evento, paquete, RepositorioUsuarios(cur).listar_gerentes(), eventos.hoy()

    def cambiar_estado(self, id_gerente: int, id_evento: int, nuevo: str) -> Evento:
        """
        RF-30 desde el tablero y la ficha (HU-006). Las transiciones siguen
        el diagrama de estados del SDD §5.3. El cambio no toca la bandera
        de finiquito, que es independiente (RN-11) y la asigna IB-06.
        """
        nuevo = (nuevo or "").strip().upper()
        if not nuevo:
            raise ErrorValidacion("Elige el nuevo estatus del evento.")
        if nuevo not in ESTADOS_EVENTO:
            raise ErrorValidacion("Ese estatus no es válido: usa cotización, confirmado, "
                                  "realizado o cancelado.")
        with BaseDatos.transaccion() as cur:
            eventos = RepositorioEventos(cur)
            if not eventos.bloquear(id_evento):
                raise ErrorNoEncontrado("El evento no existe.")
            evento = eventos.por_id(id_evento)
            motivo = evento.motivo_rechazo_estado(nuevo, eventos.hoy())
            if motivo:
                raise ErrorNegocio(motivo)
            eventos.actualizar_estado(id_evento, nuevo)
            RepositorioBitacora(cur).registrar(id_gerente, "CAMBIO_ESTATUS",
                                               f"evento:{id_evento}:{nuevo}")
            return eventos.por_id(id_evento)

    def asignar_gerente(self, id_gerente_actual: int, id_evento: int, valor: str) -> Evento:
        """RF-29 · el responsable debe ser un usuario con rol de gerente."""
        id_responsable = id_seleccionado(valor, "Gerente responsable")
        with BaseDatos.transaccion() as cur:
            responsable = RepositorioUsuarios(cur).por_id(id_responsable)
            if responsable is None or not responsable.es_gerente:
                raise ErrorValidacion("El responsable debe ser un gerente registrado.")
            eventos = RepositorioEventos(cur)
            if not eventos.asignar_gerente(id_evento, id_responsable):
                raise ErrorNoEncontrado("El evento no existe.")
            RepositorioBitacora(cur).registrar(id_gerente_actual, "ASIGNAR_GERENTE",
                                               f"evento:{id_evento}")
            return eventos.por_id(id_evento)
