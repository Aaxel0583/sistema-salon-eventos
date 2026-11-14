"""
Catálogos operativos: salones, platillos y paquetes.

C-03 Catálogos · HU-003, HU-004 · CU-04, CU-05 · RF-13 a RF-19
Escenarios 3 y 4 (Figuras 6 y 7)

Este servicio valida formato y completitud; las reglas de negocio
(BF003 límite de salones, BF004 reducción de capacidad, RN-12 dueño del
paquete) las decide la base y aquí solo se propagan ya traducidas.
"""
from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorNoEncontrado, ErrorValidacion
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_catalogos import (RepositorioPaquetes,
                                             RepositorioPlatillos,
                                             RepositorioSalones)
from app.datos.repositorio_usuarios import RepositorioUsuarios
from app.dominio.modelos import (CATEGORIAS_PLATILLO, TIPO_ESTANDAR,
                                 TIPO_PERSONALIZADO, TIPOS_PAQUETE, Paquete,
                                 Platillo, Salon)
from app.servicios.validaciones import (entero_positivo, importe,
                                        texto_obligatorio, texto_opcional)


class ServicioSalones:
    """CU-04 Administrar salones."""

    def listar(self) -> list[Salon]:
        with BaseDatos.transaccion() as cur:
            return RepositorioSalones(cur).listar()

    def actualizar(self, id_gerente: int, id_salon: int, datos: dict) -> None:
        nombre = texto_obligatorio(datos.get("nombre"), "Nombre", 80)
        descripcion = texto_opcional(datos.get("descripcion"), 255)
        capacidad = entero_positivo(datos.get("capacidad_maxima"), "Capacidad máxima")
        costo = importe(datos.get("costo_renta"), "Costo de renta")
        disponible = "S" if datos.get("disponible") == "S" else "N"

        with BaseDatos.transaccion() as cur:
            if not RepositorioSalones(cur).actualizar(id_salon, nombre, descripcion,
                                                       capacidad, costo, disponible):
                raise ErrorNoEncontrado("El salón no existe.")
            RepositorioBitacora(cur).registrar(id_gerente, "EDITAR_SALON", f"salon:{id_salon}")


class ServicioPlatillos:
    """CU-05 (parte de platillos)."""

    def listar(self) -> list[Platillo]:
        with BaseDatos.transaccion() as cur:
            return RepositorioPlatillos(cur).listar()

    @staticmethod
    def _validar(datos: dict) -> tuple[str, str]:
        nombre = texto_obligatorio(datos.get("nombre"), "Nombre del platillo", 80)
        categoria = (datos.get("categoria") or "").strip().upper()
        if categoria not in CATEGORIAS_PLATILLO:
            raise ErrorValidacion("Elige una categoría válida para el platillo.")
        return nombre, categoria

    def crear(self, datos: dict) -> int:
        nombre, categoria = self._validar(datos)
        with BaseDatos.transaccion() as cur:
            return RepositorioPlatillos(cur).insertar(nombre, categoria)

    def actualizar(self, id_platillo: int, datos: dict) -> None:
        nombre, categoria = self._validar(datos)
        with BaseDatos.transaccion() as cur:
            if not RepositorioPlatillos(cur).actualizar(id_platillo, nombre, categoria):
                raise ErrorNoEncontrado("El platillo no existe.")

    def eliminar(self, id_platillo: int) -> None:
        with BaseDatos.transaccion() as cur:
            if not RepositorioPlatillos(cur).eliminar(id_platillo):
                raise ErrorNoEncontrado("El platillo no existe.")


class ServicioPaquetes:
    """CU-05 (armado de paquetes) · Escenario 4."""

    def listar(self) -> list[Paquete]:
        with BaseDatos.transaccion() as cur:
            return RepositorioPaquetes(cur).listar()

    def obtener(self, id_paquete: int) -> Paquete:
        with BaseDatos.transaccion() as cur:
            paquete = RepositorioPaquetes(cur).por_id(id_paquete)
        if paquete is None:
            raise ErrorNoEncontrado("El paquete no existe.")
        return paquete

    @staticmethod
    def _validar(datos: dict, ids_platillo: list[str]) -> tuple:
        nombre = texto_obligatorio(datos.get("nombre"), "Nombre del paquete", 80)
        precio = importe(datos.get("precio_persona"), "Precio por persona")
        tipo = (datos.get("tipo") or TIPO_ESTANDAR).upper()
        if tipo not in TIPOS_PAQUETE:
            raise ErrorValidacion("Elige un tipo de paquete válido.")

        id_cliente = None
        if tipo == TIPO_PERSONALIZADO:
            if not datos.get("id_cliente"):
                raise ErrorValidacion("Un paquete personalizado necesita un cliente asignado.")  # RN-12
            id_cliente = entero_positivo(datos.get("id_cliente"), "Cliente")

        try:
            platillos = sorted({int(i) for i in ids_platillo})
        except ValueError:
            raise ErrorValidacion("La selección de platillos no es válida.") from None
        if not platillos:
            raise ErrorValidacion("Un paquete debe incluir al menos un platillo.")
        return nombre, precio, tipo, id_cliente, platillos

    def guardar(self, id_gerente: int, datos: dict, ids_platillo: list[str],
                id_paquete: int | None = None) -> int:
        """
        Crea o edita un paquete y su menú en UNA transacción: si algo falla
        a la mitad, no queda un paquete sin platillos.
        """
        nombre, precio, tipo, id_cliente, platillos = self._validar(datos, ids_platillo)

        with BaseDatos.transaccion() as cur:
            if id_cliente is not None:
                cliente = RepositorioUsuarios(cur).por_id(id_cliente)
                if cliente is None or not cliente.es_cliente:
                    raise ErrorValidacion("El cliente seleccionado no existe.")
            repo_platillos = RepositorioPlatillos(cur)
            if repo_platillos.contar_existentes(platillos) != len(platillos):
                raise ErrorValidacion("Uno de los platillos seleccionados ya no existe.")

            repo = RepositorioPaquetes(cur)
            if id_paquete is None:
                id_paquete = repo.insertar(nombre, precio, tipo, id_cliente)
                accion = "ALTA_PAQUETE"
            else:
                if not repo.actualizar(id_paquete, nombre, precio, tipo, id_cliente):
                    raise ErrorNoEncontrado("El paquete no existe.")
                accion = "EDITAR_PAQUETE"
            repo.reemplazar_platillos(id_paquete, platillos)
            RepositorioBitacora(cur).registrar(id_gerente, accion, f"paquete:{id_paquete}")
            return id_paquete

    def eliminar(self, id_gerente: int, id_paquete: int) -> None:
        with BaseDatos.transaccion() as cur:
            if not RepositorioPaquetes(cur).eliminar(id_paquete):
                raise ErrorNoEncontrado("El paquete no existe.")
            RepositorioBitacora(cur).registrar(id_gerente, "BAJA_PAQUETE", f"paquete:{id_paquete}")
