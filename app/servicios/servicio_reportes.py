"""
Reportes operativos · C-06 · HU-010, HU-011, HU-012 · CU-09 · RF-35 a RF-38
Escenario 9 (Figura 12) · IE-02 (descarga en CSV)

Cada reporte se define una sola vez como una lista de columnas. La
pantalla (IU-08) y el archivo CSV se generan a partir de esa misma lista
y de las mismas filas, de modo que la descarga entrega exactamente las
columnas visibles (RF-38) y respeta los filtros aplicados.

El semáforo, el saldo y los totales por categoría vienen de las vistas
IB-08 e IB-09: este servicio no los recalcula (DA-01).
"""
import csv
import io
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any, Callable

from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorValidacion
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_catalogos import RepositorioSalones
from app.datos.repositorio_eventos import RepositorioEventos
from app.datos.repositorio_reportes import RepositorioReportes
from app.dominio.modelos import (DIAS_CORTE_CARTERA, ESTADO_CONFIRMADO, ESTADO_COTIZACION,
                                 ESTADOS_EVENTO, SEMAFORO_PROXIMA, SEMAFORO_VENCIDA,
                                 SEMAFORO_VIGENTE, SEMAFOROS, Salon)
from app.servicios.validaciones import fecha as validar_fecha

# Tipos de columna: deciden cómo se presenta el valor en pantalla y en el archivo.
TEXTO, CLAVE, FECHA, MONEDA, ETIQUETA, CONTACTO = "texto", "clave", "fecha", "moneda", "etiqueta", "contacto"

# Color de cada etiqueta (DESIGN.md «El Color Dice Algo»).
_TONO_SEMAFORO = {SEMAFORO_VENCIDA: "roja", SEMAFORO_PROXIMA: "ambar", SEMAFORO_VIGENTE: "verde"}
_TONO_ESTADO = {ESTADO_COTIZACION: "marino", ESTADO_CONFIRMADO: "verde"}

LIQUIDACIONES = {"CON_SALDO": "Con saldo pendiente", "FINIQUITADO": "Finiquitados"}


@dataclass(frozen=True)
class Columna:
    titulo: str
    valor: Callable[[Any], Any]
    tipo: str = TEXTO
    tono: Callable[[Any], str] | None = None      # solo ETIQUETA: color de la píldora
    papel: str = ""                               # "titulo" o "estado": cabecera de la tarjeta en celular


@dataclass(frozen=True)
class Total:
    etiqueta: str
    importe: Decimal | None = None
    cuentas: int | None = None
    tono: str = ""                                # "roja", "ambar", "verde" o vacío
    filtro: str | None = None                     # valor del filtro que aplica al tocarlo
    nota: str = ""


@dataclass
class Reporte:
    clave: str                                    # cartera · activos · realizados
    titulo: str
    descripcion: str
    columnas: list[Columna]
    filas: list
    totales: list[Total]
    hoy: date
    filtros: dict = field(default_factory=dict)
    salones: list[Salon] = field(default_factory=list)
    vacio: str = "No hay registros."

    @property
    def hay_filtros(self) -> bool:
        return any(self.filtros.values())

    @property
    def nombre_archivo(self) -> str:
        return f"{self.clave}_{self.hoy:%Y-%m-%d}.csv"

    def celda_csv(self, columna: Columna, fila) -> str:
        """El mismo dato de la pantalla, en una forma que una hoja de cálculo pueda sumar y ordenar."""
        valor = columna.valor(fila)
        if valor is None:
            return ""
        if columna.tipo == FECHA:
            return f"{valor:%d/%m/%Y}"
        if columna.tipo == MONEDA:
            return f"{valor:.2f}"
        return _texto_seguro(str(valor))

    def a_csv(self) -> str:
        """IE-02 · CSV con separador de coma y codificación UTF-8, con las columnas de la pantalla."""
        salida = io.StringIO()
        escritor = csv.writer(salida, lineterminator="\r\n")
        escritor.writerow([c.titulo for c in self.columnas])
        for fila in self.filas:
            escritor.writerow([self.celda_csv(c, fila) for c in self.columnas])
        return salida.getvalue()


def _texto_seguro(texto: str) -> str:
    """
    Un nombre de evento o de cliente lo captura una persona. Si empieza con
    =, +, - o @, una hoja de cálculo lo ejecutaría como fórmula al abrir el
    archivo; el apóstrofo inicial lo deja como texto.
    """
    return "'" + texto if texto[:1] in ("=", "+", "-", "@", "\t", "\r") else texto


# ---------------------------------------------------------------------
# Definición de columnas (una sola vez por reporte)
# ---------------------------------------------------------------------
_COLUMNAS_CARTERA = [
    Columna("Clave", lambda c: c.clave_proyecto, CLAVE, papel="titulo"),
    Columna("Cliente", lambda c: c.nombre_cliente),
    Columna("Contacto", lambda c: c.contacto_cliente, CONTACTO),
    Columna("Salón", lambda c: c.nombre_salon),
    Columna("Fecha del evento", lambda c: c.fecha_evento, FECHA),
    Columna("Plazo", lambda c: c.plazo),
    Columna("Pagado", lambda c: c.total_pagado, MONEDA),
    Columna("Saldo", lambda c: c.saldo, MONEDA),
    Columna("Semáforo", lambda c: c.semaforo_legible, ETIQUETA,
            tono=lambda c: _TONO_SEMAFORO.get(c.semaforo, "gris"), papel="estado"),
]

_COLUMNAS_ACTIVOS = [
    Columna("Clave", lambda e: e.clave_proyecto, CLAVE, papel="titulo"),
    Columna("Fecha", lambda e: e.fecha_evento, FECHA),
    Columna("Horario", lambda e: e.horario),
    Columna("Cliente", lambda e: e.nombre_cliente),
    Columna("Salón", lambda e: e.nombre_salon),
    Columna("Paquete", lambda e: e.nombre_paquete or "Sin paquete"),
    Columna("Aforo", lambda e: e.aforo),
    Columna("Costo", lambda e: e.costo_total, MONEDA),
    # Una cotización no es deuda (DESIGN.md «Dinero por estatus»): sin saldo en pantalla ni en el CSV
    Columna("Saldo", lambda e: None if e.estado == ESTADO_COTIZACION else e.saldo, MONEDA),
    Columna("Estatus", lambda e: e.estado_legible, ETIQUETA,
            tono=lambda e: _TONO_ESTADO.get(e.estado, "gris"), papel="estado"),
]

_COLUMNAS_REALIZADOS = [
    Columna("Clave", lambda e: e.clave_proyecto, CLAVE, papel="titulo"),
    Columna("Fecha", lambda e: e.fecha_evento, FECHA),
    Columna("Cliente", lambda e: e.nombre_cliente),
    Columna("Salón", lambda e: e.nombre_salon),
    Columna("Costo", lambda e: e.costo_total, MONEDA),
    Columna("Pagado", lambda e: e.total_pagado, MONEDA),
    Columna("Saldo", lambda e: e.saldo, MONEDA),
    Columna("Liquidación", lambda e: "Finiquitado" if e.esta_finiquitado else "Con saldo", ETIQUETA,
            tono=lambda e: "verde" if e.esta_finiquitado else "ambar", papel="estado"),
]


def _suma(filas, campo: str) -> Decimal:
    return sum((getattr(f, campo) for f in filas), Decimal("0"))


def _fecha_opcional(valor: str | None, campo: str) -> date | None:
    """Un filtro de fecha vacío no filtra; uno mal escrito se rechaza con su mensaje."""
    if not (valor or "").strip():
        return None
    return validar_fecha(valor, campo)


class ServicioReportes:

    semaforos = SEMAFOROS
    estados_activos = {ESTADO_COTIZACION: ESTADOS_EVENTO[ESTADO_COTIZACION],
                       ESTADO_CONFIRMADO: ESTADOS_EVENTO[ESTADO_CONFIRMADO]}
    liquidaciones = LIQUIDACIONES

    # ------------------------- HU-010 · Cartera -------------------------
    def cartera(self, semaforo: str = "") -> Reporte:
        """RF-37 · Cuentas no liquidadas con su semáforo y el total adeudado por categoría."""
        semaforo = semaforo.upper() if semaforo and semaforo.upper() in SEMAFOROS else ""
        with BaseDatos.transaccion() as cur:
            repo = RepositorioReportes(cur)
            filas = repo.cartera(semaforo or None)
            por_categoria = repo.totales_cartera()
            hoy = RepositorioEventos(cur).hoy()

        notas = {SEMAFORO_VENCIDA: "La fecha del evento ya pasó",
                 SEMAFORO_PROXIMA: f"El evento es en {DIAS_CORTE_CARTERA} días o menos",
                 SEMAFORO_VIGENTE: f"Faltan más de {DIAS_CORTE_CARTERA} días"}
        totales = []
        for codigo, texto in SEMAFOROS.items():
            dato = por_categoria.get(codigo, {})
            totales.append(Total(texto, dato.get("adeudo", Decimal("0")), dato.get("cuentas", 0),
                                 _TONO_SEMAFORO[codigo], codigo, notas[codigo]))
        totales.append(Total("Total por cobrar",
                             sum((t.importe for t in totales), Decimal("0")),
                             sum(t.cuentas for t in totales), filtro="", nota="Todas las cuentas"))
        return Reporte(
            clave="cartera", titulo="Cartera por cobrar",
            descripcion=(f"Eventos confirmados o realizados con saldo pendiente. El corte de cobranza "
                         f"preventiva es de {DIAS_CORTE_CARTERA} días antes del evento."),
            columnas=_COLUMNAS_CARTERA, filas=filas, totales=totales, hoy=hoy,
            filtros={"semaforo": semaforo},
            vacio=("Ninguna cuenta está en esa categoría." if semaforo
                   else "No hay cuentas por cobrar: ningún evento confirmado o realizado tiene saldo pendiente."),
        )

    # --------------------- HU-011 · Proyectos activos ---------------------
    def activos(self, estado: str = "", id_salon: str = "") -> Reporte:
        """RF-35 · Eventos en cotización o confirmados, ordenados por fecha."""
        estado = estado.upper() if estado and estado.upper() in self.estados_activos else ""
        salon = int(id_salon) if str(id_salon).isdigit() else None
        with BaseDatos.transaccion() as cur:
            filas = RepositorioReportes(cur).activos(estado or None, salon)
            salones = RepositorioSalones(cur).listar()
            hoy = RepositorioEventos(cur).hoy()
        if salon and salon not in {s.id_salon for s in salones}:
            salon = None
        confirmados = [f for f in filas if f.estado == ESTADO_CONFIRMADO]
        totales = [
            Total("Eventos activos", cuentas=len(filas),
                  nota=f"{len(confirmados)} confirmados · {len(filas) - len(confirmados)} en cotización"),
            Total("Costo comprometido", _suma(filas, "costo_total"), nota="Suma del costo de los eventos listados"),
            Total("Saldo por cobrar", _suma(confirmados, "saldo"), nota="Solo eventos confirmados"),
        ]
        return Reporte(
            clave="activos", titulo="Proyectos activos",
            descripcion="Eventos en cotización o confirmados, del más cercano al más lejano.",
            columnas=_COLUMNAS_ACTIVOS, filas=filas, totales=totales, hoy=hoy,
            filtros={"estado": estado, "salon": str(salon) if salon else ""}, salones=salones,
            vacio="No hay eventos en cotización ni confirmados.",
        )

    # -------------------- HU-012 · Proyectos realizados --------------------
    def realizados(self, desde: str = "", hasta: str = "", liquidacion: str = "") -> Reporte:
        """RF-36 · Histórico de eventos realizados con costo, pagado y saldo restante."""
        fecha_desde = _fecha_opcional(desde, "Desde")
        fecha_hasta = _fecha_opcional(hasta, "Hasta")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ErrorValidacion("La fecha «Desde» no puede ser posterior a la fecha «Hasta».")
        liquidacion = liquidacion.upper() if liquidacion and liquidacion.upper() in LIQUIDACIONES else ""
        with BaseDatos.transaccion() as cur:
            filas = RepositorioReportes(cur).realizados(fecha_desde, fecha_hasta, liquidacion or None)
            hoy = RepositorioEventos(cur).hoy()
        con_saldo = [f for f in filas if f.saldo > 0]
        totales = [
            Total("Eventos realizados", cuentas=len(filas),
                  nota=f"{len(filas) - len(con_saldo)} liquidados · {len(con_saldo)} con saldo"),
            Total("Costo", _suma(filas, "costo_total"), nota="Precio pactado de los eventos listados"),
            Total("Pagado", _suma(filas, "total_pagado"), tono="verde"),
            Total("Saldo restante", _suma(filas, "saldo"), tono="ambar" if con_saldo else ""),
        ]
        return Reporte(
            clave="realizados", titulo="Proyectos realizados",
            descripcion="Eventos que ya se llevaron a cabo, del más reciente al más antiguo.",
            columnas=_COLUMNAS_REALIZADOS, filas=filas, totales=totales, hoy=hoy,
            filtros={"desde": f"{fecha_desde:%Y-%m-%d}" if fecha_desde else "",
                     "hasta": f"{fecha_hasta:%Y-%m-%d}" if fecha_hasta else "",
                     "liquidacion": liquidacion},
            vacio="Aún no hay eventos realizados.",
        )

    # ---------------------------- RF-41 ----------------------------
    @staticmethod
    def registrar_descarga(id_gerente: int, reporte: Reporte) -> None:
        """La descarga saca del sistema datos de contacto de los clientes: queda en bitácora."""
        with BaseDatos.transaccion() as cur:
            RepositorioBitacora(cur).registrar(id_gerente, "DESCARGA_REPORTE", f"reporte:{reporte.clave}")
