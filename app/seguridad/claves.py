"""
Generación y cifrado de claves de acceso.

C-01 / C-02 · RNF-04 · RNF-14 · RF-02 · RF-08
- Cifrado: función de derivación con sal (scrypt, vía Werkzeug). La clave
  en claro nunca se guarda ni se registra en bitácora o logs.
- Clave inicial legible: alfabeto sin caracteres que se confunden al
  dictarla (0/O, 1/I/L), en dos bloques de cuatro: "K7PM-3QXR".
"""
import secrets

from werkzeug.security import check_password_hash, generate_password_hash

ALFABETO_DICTABLE = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"   # sin 0 O 1 I L
LONGITUD_MINIMA = 8


def generar_clave_legible(bloques: int = 2, largo: int = 4) -> str:
    """Clave aleatoria criptográficamente segura y fácil de dictar."""
    return "-".join(
        "".join(secrets.choice(ALFABETO_DICTABLE) for _ in range(largo))
        for _ in range(bloques)
    )


def cifrar(clave: str) -> str:
    return generate_password_hash(clave, method="scrypt")


def verificar(clave_hash: str, clave: str) -> bool:
    return check_password_hash(clave_hash, clave)


# Hash señuelo: cuando el usuario no existe se verifica contra este valor
# para que la respuesta tarde lo mismo y no revele qué cuentas existen.
_HASH_SENUELO = cifrar(secrets.token_hex(16))


def verificar_senuelo(clave: str) -> None:
    check_password_hash(_HASH_SENUELO, clave)


def normalizar_clave_inicial(clave: str) -> str:
    """
    La clave inicial se dicta; el cliente puede escribirla en minúsculas o
    sin guion. Solo se usa como segundo intento cuando la cuenta todavía
    tiene la clave que entregó el gerente.
    """
    limpia = clave.strip().upper().replace(" ", "").replace("-", "")
    if len(limpia) == 8:
        return f"{limpia[:4]}-{limpia[4:]}"
    return clave.strip().upper()


def errores_clave_nueva(clave: str, confirmacion: str, clave_actual: str = "") -> list[str]:
    """Las tres condiciones de IU-02 (SDD Figura 28), verificadas también en el servidor."""
    errores = []
    if len(clave) < LONGITUD_MINIMA:
        errores.append(f"La clave nueva debe tener al menos {LONGITUD_MINIMA} caracteres.")
    if clave_actual and clave == clave_actual:
        errores.append("La clave nueva debe ser distinta de la actual.")
    if clave != confirmacion:
        errores.append("La confirmación no coincide con la clave nueva.")
    return errores
