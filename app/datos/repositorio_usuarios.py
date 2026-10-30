"""
Repositorio de la tabla USUARIO.

C-10 · RNF-05: todas las sentencias usan parámetros enlazados (%s);
nunca se concatenan valores. DA-02: el SQL vive solo en este paquete.
Cada repositorio recibe el cursor de una transacción abierta, de modo que
varios repositorios pueden participar en la misma transacción (DA-05).
"""
import re

from psycopg import Cursor

from app.dominio.modelos import ROL_CLIENTE, Usuario

LIMITE_BUSQUEDA = 100       # filas del directorio; la pantalla avisa al llegar aquí

_COLUMNAS = """id_usuario, nombre, correo, telefono, rol, clave_hash,
               requiere_cambio_clave, intentos_fallidos, estado"""


class RepositorioUsuarios:
    def __init__(self, cursor: Cursor):
        self._cur = cursor

    # ---------------------------- consultas ----------------------------
    def por_id(self, id_usuario: int) -> Usuario | None:
        self._cur.execute(
            f"SELECT {_COLUMNAS} FROM usuario WHERE id_usuario = %s",
            (id_usuario,),
        )
        fila = self._cur.fetchone()
        return Usuario.desde_fila(fila) if fila else None

    def por_identificador(self, campo: str, valor: str, bloquear: bool = False) -> Usuario | None:
        """
        Busca por correo o por teléfono. `campo` lo decide el código
        (nunca el usuario), por eso se elige de una lista cerrada.
        `bloquear=True` toma la fila con FOR UPDATE para que dos intentos
        de acceso simultáneos no se pisen al contar fallos.
        """
        columna = {"correo": "correo", "telefono": "telefono"}[campo]
        candado = " FOR UPDATE" if bloquear else ""
        self._cur.execute(
            f"SELECT {_COLUMNAS} FROM usuario WHERE {columna} = %s{candado}",
            (valor,),
        )
        fila = self._cur.fetchone()
        return Usuario.desde_fila(fila) if fila else None

    def buscar_clientes(self, texto: str = "", limite: int | None = LIMITE_BUSQUEDA) -> list[Usuario]:
        """Directorio de clientes con búsqueda por nombre, correo o celular (RF-11).
        `limite=None` trae a todos (LIMIT NULL en PostgreSQL)."""
        # Se escapan los comodines para que "%" o "_" se busquen literalmente.
        limpio = texto.strip().lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        patron = f"%{limpio}%"
        # El celular se guarda solo con dígitos: "492 111" debe encontrar "4921110011".
        # Solo si el texto parece celular: "juan23@" no debe traer todo celular con "23".
        parece_celular = re.fullmatch(r"[\d\s()+.-]*\d[\d\s()+.-]*", texto.strip())
        patron_tel = "%" + re.sub(r"\D", "", texto) + "%" if parece_celular else patron
        self._cur.execute(
            f"""SELECT {_COLUMNAS},
                       (SELECT COUNT(*) FROM evento e
                         WHERE e.id_cliente = usuario.id_usuario) AS num_eventos
                  FROM usuario
                 WHERE rol = %s
                   AND (LOWER(nombre) LIKE %s
                        OR COALESCE(correo, '') LIKE %s
                        OR COALESCE(telefono, '') LIKE %s)
                 ORDER BY nombre
                 LIMIT %s""",
            (ROL_CLIENTE, patron, patron, patron_tel, limite),
        )
        return [Usuario.desde_fila(f) for f in self._cur.fetchall()]

    def contar_por_rol(self, rol: str) -> int:
        self._cur.execute("SELECT COUNT(*) AS total FROM usuario WHERE rol = %s", (rol,))
        return self._cur.fetchone()["total"]

    # --------------------------- operaciones ---------------------------
    def insertar(self, nombre: str, correo: str | None, telefono: str | None,
                 rol: str, clave_hash: str) -> int:
        self._cur.execute(
            """INSERT INTO usuario (nombre, correo, telefono, rol, clave_hash,
                                    requiere_cambio_clave, intentos_fallidos, estado)
               VALUES (%s, %s, %s, %s, %s, 'S', 0, 'ACTIVO')
               RETURNING id_usuario""",
            (nombre, correo, telefono, rol, clave_hash),
        )
        return self._cur.fetchone()["id_usuario"]

    def registrar_fallo(self, id_usuario: int, maximo: int) -> Usuario:
        """Suma un intento fallido y bloquea al llegar al máximo (RF-03)."""
        self._cur.execute(
            f"""UPDATE usuario
                   SET intentos_fallidos = intentos_fallidos + 1,
                       estado = CASE WHEN intentos_fallidos + 1 >= %s
                                     THEN 'BLOQUEADO' ELSE estado END
                 WHERE id_usuario = %s
             RETURNING {_COLUMNAS}""",
            (maximo, id_usuario),
        )
        return Usuario.desde_fila(self._cur.fetchone())

    def reiniciar_intentos(self, id_usuario: int) -> None:
        self._cur.execute(
            "UPDATE usuario SET intentos_fallidos = 0 WHERE id_usuario = %s",
            (id_usuario,),
        )

    def actualizar_clave(self, id_usuario: int, clave_hash: str, requiere_cambio: bool) -> None:
        """
        Cambio de clave (RF-04) o regeneración por el gerente (RF-10).
        La regeneración también reactiva la cuenta y limpia los intentos.
        """
        self._cur.execute(
            """UPDATE usuario
                  SET clave_hash = %s,
                      requiere_cambio_clave = %s,
                      intentos_fallidos = 0,
                      estado = 'ACTIVO'
                WHERE id_usuario = %s""",
            (clave_hash, "S" if requiere_cambio else "N", id_usuario),
        )
