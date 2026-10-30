"""
Utilidad de administración de cuentas · C-09 · IE-03 · PKG-07

Se ejecuta en la estación del responsable, fuera de la interfaz web, y
solo depende de seguridad (PKG-04) y acceso a datos (PKG-05).
Sirve para crear el primer gerente y para recuperar el acceso cuando no
hay ningún gerente que pueda entrar al sistema.

Uso:
  python -m administracion.admin crear-gerente --nombre "Ana López" --correo ana@salon.mx
  python -m administracion.admin regenerar-clave --usuario ana@salon.mx
  python -m administracion.admin desbloquear --usuario 4921234567
"""
import argparse
import sys

from app.config import Configuracion
from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorDominio
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_usuarios import RepositorioUsuarios
from app.dominio.modelos import ROL_GERENTE
from app.seguridad import claves
from app.servicios.validaciones import (interpretar_identificador,
                                        normalizar_correo, normalizar_telefono,
                                        texto_obligatorio)


def _imprimir_clave(nombre: str, clave: str) -> None:
    print(f"\n  Cuenta: {nombre}")
    print(f"  Clave inicial: {clave}")
    print("  Se pedirá cambiarla en el primer ingreso. No se volverá a mostrar.\n")


def crear_gerente(args) -> None:
    nombre = texto_obligatorio(args.nombre, "Nombre", 120)
    correo, telefono = normalizar_correo(args.correo), normalizar_telefono(args.telefono)
    if not correo and not telefono:
        raise ErrorDominio("Indica --correo o --telefono.")
    clave = claves.generar_clave_legible()
    with BaseDatos.transaccion() as cur:
        id_usuario = RepositorioUsuarios(cur).insertar(nombre, correo, telefono,
                                                       ROL_GERENTE, claves.cifrar(clave))
        RepositorioBitacora(cur).registrar(None, "ALTA_GERENTE_CONSOLA", f"usuario:{id_usuario}")
    _imprimir_clave(nombre, clave)


def regenerar_clave(args) -> None:
    campo, valor = interpretar_identificador(args.usuario)
    clave = claves.generar_clave_legible()
    with BaseDatos.transaccion() as cur:
        usuarios = RepositorioUsuarios(cur)
        usuario = usuarios.por_identificador(campo, valor, bloquear=True)
        if usuario is None:
            raise ErrorDominio("No existe una cuenta con ese correo o celular.")
        usuarios.actualizar_clave(usuario.id_usuario, claves.cifrar(clave), requiere_cambio=True)
        RepositorioBitacora(cur).registrar(None, "REGENERAR_CLAVE_CONSOLA", f"usuario:{usuario.id_usuario}")
    _imprimir_clave(usuario.nombre, clave)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="admin", description="Administración de cuentas")
    sub = parser.add_subparsers(dest="orden", required=True)

    p = sub.add_parser("crear-gerente", help="Da de alta una cuenta de gerente")
    p.add_argument("--nombre", required=True)
    p.add_argument("--correo")
    p.add_argument("--telefono")
    p.set_defaults(funcion=crear_gerente)

    for orden in ("regenerar-clave", "desbloquear"):
        p = sub.add_parser(orden, help="Genera una clave inicial nueva y reactiva la cuenta")
        p.add_argument("--usuario", required=True, help="correo o celular de la cuenta")
        p.set_defaults(funcion=regenerar_clave)

    args = parser.parse_args(argv)
    config = Configuracion.desde_entorno()
    BaseDatos.iniciar(config.database_url, 1, 1)
    BaseDatos._pool.wait(timeout=30)          # la utilidad sí espera a que la base despierte
    try:
        args.funcion(args)
        return 0
    except ErrorDominio as error:
        print(f"Error: {error.mensaje}", file=sys.stderr)
        return 1
    finally:
        BaseDatos.cerrar()


if __name__ == "__main__":
    sys.exit(main())
