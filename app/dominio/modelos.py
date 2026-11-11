"""
Clases del dominio.

SDD v2.0 §4.1 · Figura 3 (diagrama de clases)
Cada clase refleja una entidad del modelo de datos y concentra las
operaciones que le son propias. Las reglas críticas (aforo, traslape,
límite de salones) NO se duplican aquí: viven en la base (DA-01). Las
operaciones de estas clases sirven para presentar información, no para
autorizar cambios.

Sprint 1: Usuario, Salon, Platillo y Paquete.
Sprint 2: Evento (HU-005, HU-006), OcupacionSalon (IB-10) y Pago en modo de
          solo lectura, para el portal del cliente (HU-008).
Sprint 3: el registro de pagos (IB-06, HU-009) completa la clase Pago.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal

# ---------------------------------------------------------------------
# Catálogos de valores válidos (espejo de los CHECK de la base)
# ---------------------------------------------------------------------
ROL_GERENTE = "GERENTE"
ROL_CLIENTE = "CLIENTE"

ESTADO_ACTIVO = "ACTIVO"
ESTADO_BLOQUEADO = "BLOQUEADO"

CATEGORIAS_PLATILLO = {          # RF-17 · orden de presentación
    "ENTRADA": "Entrada",
    "PLATO_FUERTE": "Plato fuerte",
    "GUARNICION": "Guarnición",
    "POSTRE": "Postre",
    "BEBIDA": "Bebida",
}

TIPO_ESTANDAR = "ESTANDAR"
TIPO_PERSONALIZADO = "PERSONALIZADO"
TIPOS_PAQUETE = {TIPO_ESTANDAR: "Estándar", TIPO_PERSONALIZADO: "Personalizado"}


# ---------------------------------------------------------------------
# Usuario · gerentes y clientes
# ---------------------------------------------------------------------
@dataclass
class Usuario:
    id_usuario: int
    nombre: str
    rol: str
    estado: str
    requiere_cambio_clave: str
    intentos_fallidos: int = 0
    correo: str | None = None
    telefono: str | None = None
    clave_hash: str = field(default="", repr=False)   # nunca se imprime
    num_eventos: int = 0                               # dato de apoyo para IU-04

    @classmethod
    def desde_fila(cls, fila: dict) -> "Usuario":
        return cls(
            id_usuario=fila["id_usuario"],
            nombre=fila["nombre"],
            rol=fila["rol"],
            estado=fila["estado"],
            requiere_cambio_clave=fila["requiere_cambio_clave"],
            intentos_fallidos=fila.get("intentos_fallidos", 0),
            correo=fila.get("correo"),
            telefono=fila.get("telefono"),
            clave_hash=fila.get("clave_hash", ""),
            num_eventos=fila.get("num_eventos", 0),
        )

    @property
    def es_gerente(self) -> bool:
        return self.rol == ROL_GERENTE

    @property
    def es_cliente(self) -> bool:
        return self.rol == ROL_CLIENTE

    @property
    def esta_bloqueado(self) -> bool:
        return self.estado == ESTADO_BLOQUEADO

    @property
    def debe_cambiar_clave(self) -> bool:
        return self.requiere_cambio_clave == "S"

    @property
    def telefono_legible(self) -> str | None:
        """'4921110011' -> '492 111 0011' (formato de IU-04)."""
        t = self.telefono
        if t and len(t) == 10:
            return f"{t[:3]} {t[3:6]} {t[6:]}"
        return t

    @property
    def contacto(self) -> str:
        return unir_contacto(self.correo, self.telefono)


def unir_contacto(correo: str | None, telefono: str | None) -> str:
    """Dato de contacto para mostrar en listados."""
    return " / ".join(p for p in (correo, telefono) if p)


# ---------------------------------------------------------------------
# Salon · uno de los tres espacios autorizados
# ---------------------------------------------------------------------
@dataclass
class Salon:
    id_salon: int
    nombre: str
    capacidad_maxima: int
    costo_renta: Decimal
    disponible: str = "S"
    descripcion: str | None = None
    mayor_aforo_agendado: int | None = None   # dato de apoyo para IU-05

    @classmethod
    def desde_fila(cls, fila: dict) -> "Salon":
        return cls(
            id_salon=fila["id_salon"],
            nombre=fila["nombre"],
            capacidad_maxima=fila["capacidad_maxima"],
            costo_renta=fila["costo_renta"],
            disponible=fila["disponible"],
            descripcion=fila.get("descripcion"),
            mayor_aforo_agendado=fila.get("mayor_aforo_agendado"),
        )

    @property
    def esta_disponible(self) -> bool:
        return self.disponible == "S"


# ---------------------------------------------------------------------
# Platillo · elemento del menú
# ---------------------------------------------------------------------
@dataclass
class Platillo:
    id_platillo: int
    nombre: str
    categoria: str

    @classmethod
    def desde_fila(cls, fila: dict) -> "Platillo":
        return cls(fila["id_platillo"], fila["nombre"], fila["categoria"])

    @property
    def categoria_legible(self) -> str:
        return CATEGORIAS_PLATILLO.get(self.categoria, self.categoria)


def agrupar_por_categoria(platillos: list[Platillo]) -> dict[str, list[Platillo]]:
    """Agrupa respetando el orden oficial de categorías (RF-17)."""
    grupos: dict[str, list[Platillo]] = {c: [] for c in CATEGORIAS_PLATILLO}
    for platillo in platillos:
        grupos.setdefault(platillo.categoria, []).append(platillo)
    return {c: lista for c, lista in grupos.items() if lista}


# ---------------------------------------------------------------------
# Paquete · banquete con precio por persona
# ---------------------------------------------------------------------
@dataclass
class Paquete:
    id_paquete: int
    nombre: str
    precio_persona: Decimal
    tipo: str = TIPO_ESTANDAR
    id_cliente: int | None = None
    nombre_cliente: str | None = None
    platillos: list[Platillo] = field(default_factory=list)

    @classmethod
    def desde_fila(cls, fila: dict) -> "Paquete":
        return cls(
            id_paquete=fila["id_paquete"],
            nombre=fila["nombre"],
            precio_persona=fila["precio_persona"],
            tipo=fila["tipo"],
            id_cliente=fila.get("id_cliente"),
            nombre_cliente=fila.get("nombre_cliente"),
        )

    @property
    def es_personalizado(self) -> bool:
        return self.tipo == TIPO_PERSONALIZADO

    @property
    def tipo_legible(self) -> str:
        return TIPOS_PAQUETE.get(self.tipo, self.tipo)

    def menu(self) -> dict[str, list[Platillo]]:
        return agrupar_por_categoria(self.platillos)


# ---------------------------------------------------------------------
# Evento · compromiso contratado (HU-005, HU-006)
# ---------------------------------------------------------------------
ESTADO_COTIZACION = "COTIZACION"
ESTADO_CONFIRMADO = "CONFIRMADO"
ESTADO_REALIZADO = "REALIZADO"
ESTADO_CANCELADO = "CANCELADO"

ESTADOS_EVENTO = {                # RN-11 · espejo de ck_evento_estado
    ESTADO_COTIZACION: "Cotización",
    ESTADO_CONFIRMADO: "Confirmado",
    ESTADO_REALIZADO: "Realizado",
    ESTADO_CANCELADO: "Cancelado",
}
ESTADOS_ABIERTOS = {ESTADO_COTIZACION, ESTADO_CONFIRMADO}
# RN-02 · D-20: el salón lo aparta el anticipo. Una cotización solo es una
# solicitud de información y no aparta el horario (espejo de IB-03).
ESTADOS_QUE_APARTAN = {ESTADO_CONFIRMADO, ESTADO_REALIZADO}


@dataclass
class Evento:
    """Fila de la vista IB-01 (vw_evento_detalle)."""

    id_evento: int
    clave_proyecto: str
    fecha_evento: date
    hora_inicio: time
    hora_fin: time
    num_asistentes: int
    costo_total: Decimal
    estado: str
    id_cliente: int
    nombre_cliente: str
    id_salon: int
    nombre_salon: str
    capacidad_maxima: int
    nombre_evento: str | None = None
    finiquitado: str = "N"
    fecha_finiquito: date | None = None
    correo_cliente: str | None = None
    telefono_cliente: str | None = None
    id_gerente: int | None = None
    nombre_gerente: str | None = None
    id_paquete: int | None = None
    nombre_paquete: str | None = None
    total_pagado: Decimal = Decimal("0")
    saldo: Decimal = Decimal("0")

    @classmethod
    def desde_fila(cls, fila: dict) -> "Evento":
        campos = cls.__dataclass_fields__
        return cls(**{k: v for k, v in fila.items() if k in campos})

    # ------------------------------ lectura ------------------------------
    @property
    def titulo(self) -> str:
        """Lo que se muestra cuando no se capturó nombre del evento."""
        return self.nombre_evento or f"Evento de {self.nombre_cliente}"

    @property
    def estado_legible(self) -> str:
        return ESTADOS_EVENTO.get(self.estado, self.estado)

    @property
    def esta_abierto(self) -> bool:
        return self.estado in ESTADOS_ABIERTOS

    @property
    def esta_finiquitado(self) -> bool:
        return self.finiquitado == "S"

    @property
    def horario(self) -> str:
        return f"{self.hora_inicio:%H:%M} a {self.hora_fin:%H:%M}"

    @property
    def contacto_cliente(self) -> str:
        return unir_contacto(self.correo_cliente, self.telefono_cliente)

    @property
    def ocupa_salon(self) -> bool:
        """
        RN-02 · D-20: aparta el salón el evento que ya dio anticipo
        (confirmado) o que ya se realizó. Una cotización no lo aparta y un
        cancelado tampoco.
        """
        return self.estado in ESTADOS_QUE_APARTAN

    def coincide_con(self, inicio: time, fin: time) -> bool:
        """¿Su horario se encima con [inicio, fin), sea cual sea su estatus? Los contiguos no (RF-27)."""
        return self.hora_inicio < fin and inicio < self.hora_fin

    def se_traslapa(self, inicio: time, fin: time) -> bool:
        """
        ¿Este evento le quita al salón el horario [inicio, fin)? Solo si lo
        tiene apartado y los horarios se enciman. Sirve para pintar la
        agenda de IU-06 (RF-24); quien autoriza o rechaza es el trigger IB-03.
        """
        return self.ocupa_salon and self.coincide_con(inicio, fin)

    def pendiente_de_cierre(self, hoy: date) -> bool:
        """IB-11 · RN-14: la fecha pasó y nadie ha dicho si se realizó."""
        return self.esta_abierto and self.fecha_evento < hoy

    # ------------------------ ciclo de vida (SDD §5.3) ------------------------
    def estados_siguientes(self, hoy: date) -> list[str]:
        """
        Estatus a los que puede pasar el evento hoy (Figura 25).

        - Cotización -> Confirmado (el cliente dio el anticipo), mientras la fecha no haya
          pasado. La base revisa que nadie haya apartado antes ese horario (BF002, D-20).
        - Cotización o Confirmado -> Realizado, solo si la fecha ya llegó.
        - Cotización o Confirmado -> Cancelado, en cualquier momento.
        - Realizado y Cancelado cierran el ciclo: no tienen salida.
        El sistema nunca cambia el estatus por su cuenta (RN-14, DA-04).
        """
        if not self.esta_abierto:
            return []
        siguientes = []
        if self.estado == ESTADO_COTIZACION and self.fecha_evento >= hoy:
            siguientes.append(ESTADO_CONFIRMADO)
        if self.fecha_evento <= hoy:
            siguientes.append(ESTADO_REALIZADO)
        siguientes.append(ESTADO_CANCELADO)
        return siguientes

    def motivo_rechazo_estado(self, nuevo: str, hoy: date) -> str | None:
        """Explica por qué no procede el cambio (RNF-12); None si procede."""
        if nuevo == self.estado:
            return f"El evento ya está en estatus {self.estado_legible}."
        if not self.esta_abierto:
            return (f"El evento {self.clave_proyecto} está {self.estado_legible.lower()} "
                    "y ya cerró su ciclo: su estatus no se puede cambiar.")
        if nuevo in self.estados_siguientes(hoy):
            return None
        if nuevo == ESTADO_REALIZADO:
            return (f"El evento es el {self.fecha_evento:%d/%m/%Y}: no se puede marcar como "
                    "realizado antes de su fecha.")
        if nuevo == ESTADO_CONFIRMADO and self.fecha_evento < hoy:
            return ("La fecha del evento ya pasó: indica si se realizó o se canceló.")
        return (f"Un evento en {self.estado_legible.lower()} no puede pasar a "
                f"{ESTADOS_EVENTO.get(nuevo, nuevo).lower()}.")


# ---------------------------------------------------------------------
# Pago · abono de un evento (composición con Evento)
# Sprint 2: solo lectura, para que el cliente consulte sus pagos (RF-40).
# ---------------------------------------------------------------------
@dataclass
class Pago:
    id_pago: int
    id_evento: int
    monto: Decimal
    tipo: str
    fecha_pago: datetime
    referencia: str | None = None

    @classmethod
    def desde_fila(cls, fila: dict) -> "Pago":
        campos = cls.__dataclass_fields__
        return cls(**{k: v for k, v in fila.items() if k in campos})

    @property
    def tipo_legible(self) -> str:
        """'TRANSFERENCIA' o 'pago_inicial' -> 'Transferencia', 'Pago inicial'."""
        return self.tipo.replace("_", " ").strip().capitalize()


# ---------------------------------------------------------------------
# OcupacionSalon · medidor del tablero (IB-10)
# ---------------------------------------------------------------------
UMBRAL_OCUPACION_ALTA = 80       # % a partir del cual el medidor se pinta en rojo


@dataclass
class OcupacionSalon:
    id_salon: int
    nombre: str
    capacidad_maxima: int
    eventos_proximos: int
    mayor_aforo: int
    ocupacion_promedio: int
    disponible: str = "S"
    cotizaciones_proximas: int = 0    # D-20: aún no apartan el salón; se muestran aparte

    @classmethod
    def desde_fila(cls, fila: dict) -> "OcupacionSalon":
        campos = cls.__dataclass_fields__
        return cls(**{k: v for k, v in fila.items() if k in campos})

    @property
    def porcentaje(self) -> int:
        """Acotado a 0-100 para el medidor."""
        return max(0, min(100, self.ocupacion_promedio))

    @property
    def es_alta(self) -> bool:
        return self.ocupacion_promedio > UMBRAL_OCUPACION_ALTA


# ---------------------------------------------------------------------
# Textos legibles de las acciones de bitácora (RF-41)
# ---------------------------------------------------------------------
ACCIONES_BITACORA = {
    "INICIO_SESION": "Inicio de sesión",
    "BLOQUEO_CUENTA": "Cuenta bloqueada",
    "CAMBIO_CLAVE": "Cambio de clave",
    "ALTA_CLIENTE": "Alta de cliente",
    "REGENERAR_CLAVE": "Clave regenerada",
    "EDITAR_SALON": "Edición de salón",
    "ALTA_PAQUETE": "Alta de paquete",
    "EDITAR_PAQUETE": "Edición de paquete",
    "BAJA_PAQUETE": "Baja de paquete",
    "ALTA_EVENTO": "Registro de evento",
    "CAMBIO_ESTATUS": "Cambio de estatus de evento",
    "ASIGNAR_GERENTE": "Asignación de gerente",
    "ALTA_GERENTE_CONSOLA": "Alta de gerente (consola)",
    "REGENERAR_CLAVE_CONSOLA": "Clave regenerada (consola)",
}
