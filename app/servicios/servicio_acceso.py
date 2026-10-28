"""
Autenticación y cambio de clave.

C-01 Autenticación y sesión · HU-001 · CU-01, CU-02
RF-01 a RF-04, RF-41 · Escenario 1 (Figura 4) · Diagrama de actividades
(Figura 13).

Reglas de diseño aplicadas:
- El mensaje de error no distingue "usuario inexistente" de "clave
  incorrecta" (no revela qué cuentas existen).
- Al quinto fallo consecutivo la cuenta se bloquea y se informa (RF-03).
- Con la clave inicial, el acceso queda limitado al cambio de clave (RF-04).
"""
from dataclasses import dataclass

from app.datos.conexion import BaseDatos
from app.datos.errores import ErrorNegocio, ErrorValidacion
from app.datos.repositorio_bitacora import RepositorioBitacora
from app.datos.repositorio_usuarios import RepositorioUsuarios
from app.dominio.modelos import Usuario
from app.seguridad import claves
from app.servicios.validaciones import interpretar_identificador

MENSAJE_GENERICO = "El correo, el celular o la clave no son correctos."
MENSAJE_BLOQUEO = ("Tu cuenta quedó bloqueada por intentos fallidos. "
                   "Pide al gerente del salón que te genere una clave nueva.")


@dataclass
class ResultadoAcceso:
    exito: bool
    usuario: Usuario | None = None
    mensaje: str = ""


class ServicioAcceso:
    def __init__(self, max_intentos: int = 5):
        self._max_intentos = max_intentos

    def autenticar(self, identificador: str, clave: str) -> ResultadoAcceso:
        try:
            campo, valor = interpretar_identificador(identificador)
        except ErrorValidacion:
            claves.verificar_senuelo(clave or "")
            return ResultadoAcceso(False, mensaje=MENSAJE_GENERICO)

        if not clave:
            return ResultadoAcceso(False, mensaje="Escribe tu clave de acceso.")

        with BaseDatos.transaccion() as cur:
            usuarios = RepositorioUsuarios(cur)
            bitacora = RepositorioBitacora(cur)
            usuario = usuarios.por_identificador(campo, valor, bloquear=True)

            if usuario is None:
                claves.verificar_senuelo(clave)
                return ResultadoAcceso(False, mensaje=MENSAJE_GENERICO)

            if usuario.esta_bloqueado:
                # Solo se confirma el bloqueo a quien demuestra conocer la clave.
                if self._clave_correcta(usuario, clave):
                    return ResultadoAcceso(False, mensaje=MENSAJE_BLOQUEO)
                return ResultadoAcceso(False, mensaje=MENSAJE_GENERICO)

            if not self._clave_correcta(usuario, clave):
                actualizado = usuarios.registrar_fallo(usuario.id_usuario, self._max_intentos)
                if actualizado.esta_bloqueado:
                    bitacora.registrar(usuario.id_usuario, "BLOQUEO_CUENTA",
                                       f"usuario:{usuario.id_usuario}")
                    return ResultadoAcceso(False, mensaje=MENSAJE_BLOQUEO)
                return ResultadoAcceso(False, mensaje=MENSAJE_GENERICO)

            usuarios.reiniciar_intentos(usuario.id_usuario)
            bitacora.registrar(usuario.id_usuario, "INICIO_SESION", f"usuario:{usuario.id_usuario}")
            return ResultadoAcceso(True, usuario=usuario)

    @staticmethod
    def _clave_correcta(usuario: Usuario, clave: str) -> bool:
        if claves.verificar(usuario.clave_hash, clave):
            return True
        # La clave inicial se dicta: se tolera minúsculas, espacios o sin guion.
        if usuario.debe_cambiar_clave:
            return claves.verificar(usuario.clave_hash, claves.normalizar_clave_inicial(clave))
        return False

    def cambiar_clave(self, usuario: Usuario, clave_actual: str,
                      clave_nueva: str, confirmacion: str) -> None:
        """CU-02 · RF-04 · IU-02."""
        errores = claves.errores_clave_nueva(clave_nueva, confirmacion)
        if errores:
            raise ErrorValidacion(" ".join(errores))

        with BaseDatos.transaccion() as cur:
            usuarios = RepositorioUsuarios(cur)
            vigente = usuarios.por_id(usuario.id_usuario)
            if vigente is None or not self._clave_correcta(vigente, clave_actual):
                raise ErrorNegocio("La clave actual no es correcta.")
            if claves.verificar(vigente.clave_hash, clave_nueva):
                raise ErrorValidacion("La clave nueva debe ser distinta de la actual.")

            usuarios.actualizar_clave(usuario.id_usuario, claves.cifrar(clave_nueva),
                                      requiere_cambio=False)
            RepositorioBitacora(cur).registrar(usuario.id_usuario, "CAMBIO_CLAVE",
                                               f"usuario:{usuario.id_usuario}")
