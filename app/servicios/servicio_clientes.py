"""
Gestión de clientes por el gerente.

C-02 Gestión de clientes · HU-002 · CU-03 · RF-07 a RF-11
Escenario 2 (Figura 5) · Decisión DA-05

`registrar_en(cur, ...)` recibe el cursor de una transacción ya abierta.
Así, en el Sprint 2, el motor de reservación (C-04) podrá dar de alta al
cliente y su evento en una sola transacción (RF-12): si el evento se
rechaza, el cliente tampoco queda guardado.
"""
from dataclasses import dataclass

from psycopg import Cursor

from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorNoEncontrado, ErrorValidacion
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_usuarios import LIMITE_BUSQUEDA, RepositorioUsuarios
from app.dominio.modelos import ROL_CLIENTE, Usuario, unir_contacto
from app.seguridad import claves
from app.servicios.validaciones import (normalizar_correo, normalizar_telefono,
                                        texto_obligatorio)


@dataclass
class ClienteRegistrado:
    """Resultado del alta. `clave_inicial` se muestra UNA sola vez (RF-08)."""
    id_cliente: int
    nombre: str
    contacto: str
    clave_inicial: str
    titulo: str = "Cliente registrado"


class ServicioClientes:

    @staticmethod
    def preparar_datos(nombre: str, correo: str, telefono: str) -> tuple[str, str | None, str | None]:
        """Valida antes de tocar la base: primero el contacto, luego su formato."""
        nombre = texto_obligatorio(nombre, "Nombre", 120)
        if not (correo or "").strip() and not (telefono or "").strip():
            raise ErrorValidacion("Captura al menos un dato de contacto: correo o celular.")  # RN-06
        return nombre, normalizar_correo(correo), normalizar_telefono(telefono)

    def registrar(self, id_gerente: int, nombre: str, correo: str, telefono: str) -> ClienteRegistrado:
        with BaseDatos.transaccion() as cur:
            return self.registrar_en(cur, id_gerente, nombre, correo, telefono)

    def registrar_en(self, cur: Cursor, id_gerente: int, nombre: str,
                     correo: str, telefono: str) -> ClienteRegistrado:
        nombre, correo, telefono = self.preparar_datos(nombre, correo, telefono)
        clave_inicial = claves.generar_clave_legible()

        # La unicidad (RN-07) la garantiza la base con uq_usuario_correo y
        # uq_usuario_telefono; C-10 traduce el rechazo a un mensaje claro.
        id_cliente = RepositorioUsuarios(cur).insertar(
            nombre, correo, telefono, ROL_CLIENTE, claves.cifrar(clave_inicial)
        )
        RepositorioBitacora(cur).registrar(id_gerente, "ALTA_CLIENTE", f"usuario:{id_cliente}")
        return ClienteRegistrado(id_cliente, nombre, unir_contacto(correo, telefono), clave_inicial)

    def regenerar_clave(self, id_gerente: int, id_cliente: int) -> ClienteRegistrado:
        """RF-10: nueva clave inicial, reactiva la cuenta y anula la anterior."""
        with BaseDatos.transaccion() as cur:
            usuarios = RepositorioUsuarios(cur)
            cliente = usuarios.por_id(id_cliente)
            if cliente is None or not cliente.es_cliente:
                raise ErrorNoEncontrado("El cliente no existe.")
            clave_inicial = claves.generar_clave_legible()
            usuarios.actualizar_clave(id_cliente, claves.cifrar(clave_inicial), requiere_cambio=True)
            RepositorioBitacora(cur).registrar(id_gerente, "REGENERAR_CLAVE", f"usuario:{id_cliente}")
            titulo = "Cuenta reactivada" if cliente.esta_bloqueado else "Clave nueva"
            return ClienteRegistrado(id_cliente, cliente.nombre, cliente.contacto,
                                     clave_inicial, titulo)

    def buscar(self, texto: str = "", limite: int | None = LIMITE_BUSQUEDA) -> list[Usuario]:
        with BaseDatos.transaccion() as cur:
            return RepositorioUsuarios(cur).buscar_clientes(texto, limite)
