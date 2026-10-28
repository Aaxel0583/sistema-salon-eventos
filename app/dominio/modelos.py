"""
Clases del dominio.

SDD v2.0 §4.1 · Figura 3 (diagrama de clases)
Cada clase refleja una entidad del modelo de datos y concentra las
operaciones que le son propias. Las reglas críticas (aforo, traslape,
límite de salones) NO se duplican aquí: viven en la base (DA-01). Las
operaciones de estas clases sirven para presentar información, no para
autorizar cambios.

Sprint 1: Usuario, Salon, Platillo y Paquete.
Sprint 2-3: Evento, Pago y Bitacora se agregan en este mismo módulo.
"""
from dataclasses import dataclass, field
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
    def contacto(self) -> str:
        """Dato de contacto para mostrar en listados."""
        partes = [p for p in (self.correo, self.telefono) if p]
        return " / ".join(partes)

    def intentos_restantes(self, maximo: int) -> int:
        return max(0, maximo - self.intentos_fallidos)


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

    def lugares_libres(self, asistentes: int) -> int:
        """Lugares que quedan si se reciben `asistentes` personas (RF-23)."""
        return self.capacidad_maxima - asistentes


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

    def costo_para(self, asistentes: int) -> Decimal:
        """Parte del banquete en la cotización: precio × asistentes (RN-09)."""
        return self.precio_persona * asistentes

    def menu(self) -> dict[str, list[Platillo]]:
        return agrupar_por_categoria(self.platillos)
