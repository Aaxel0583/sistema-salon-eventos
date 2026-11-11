"""
Normalización y validación de datos capturados.

PKG-03 · RF-01 · RF-07 · RN-06
Normalizar antes de guardar es lo que hace funcionar la unicidad (RN-07):
"Ana@Mail.com" y "ana@mail.com" son el mismo correo, y "492 123 4567",
"(492) 123-4567" y "+52 492 123 4567" son el mismo celular.
"""
import re
from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation

from app.datos.errores import ErrorValidacion

_PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalizar_correo(valor: str | None) -> str | None:
    valor = (valor or "").strip().lower()
    if not valor:
        return None
    if len(valor) > 120 or not _PATRON_CORREO.match(valor):
        raise ErrorValidacion("El correo no tiene un formato válido (ejemplo: nombre@dominio.com).")
    return valor


def normalizar_telefono(valor: str | None) -> str | None:
    """Conserva solo dígitos; acepta lada internacional de México (52)."""
    digitos = re.sub(r"\D", "", valor or "")
    if not digitos:
        return None
    if len(digitos) == 12 and digitos.startswith("52"):
        digitos = digitos[2:]
    if len(digitos) != 10:
        raise ErrorValidacion("El celular debe tener 10 dígitos.")
    return digitos


def interpretar_identificador(valor: str) -> tuple[str, str]:
    """
    Un solo campo acepta correo o celular (RF-01, IU-01).
    Devuelve ("correo", valor) o ("telefono", valor) ya normalizado.
    """
    valor = (valor or "").strip()
    if not valor:
        raise ErrorValidacion("Escribe tu correo o tu número de celular.")
    if "@" in valor:
        return "correo", normalizar_correo(valor)
    return "telefono", normalizar_telefono(valor)


def texto_obligatorio(valor: str | None, campo: str, maximo: int) -> str:
    valor = " ".join((valor or "").split())     # colapsa espacios
    if not valor:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    if len(valor) > maximo:
        raise ErrorValidacion(f"El campo «{campo}» admite hasta {maximo} caracteres.")
    return valor


def texto_opcional(valor: str | None, maximo: int) -> str | None:
    valor = " ".join((valor or "").split())
    return valor[:maximo] if valor else None


# Topes de las columnas: INTEGER y NUMERIC(10,2) en 01_esquema.sql.
_MAX_ENTERO = 2_147_483_647
_MAX_IMPORTE = Decimal("99999999.99")


def entero_positivo(valor: str | None, campo: str) -> int:
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        raise ErrorValidacion(f"El campo «{campo}» debe ser un número entero.") from None
    if numero <= 0:
        raise ErrorValidacion(f"El campo «{campo}» debe ser mayor a cero.")
    if numero > _MAX_ENTERO:
        raise ErrorValidacion(f"El campo «{campo}» es demasiado grande.")
    return numero


def importe(valor: str | None, campo: str) -> Decimal:
    texto = str(valor or "").replace(",", "").replace("$", "").strip()
    try:
        numero = Decimal(texto)
        if not numero.is_finite():          # "NaN" o "Infinity"
            raise InvalidOperation
        numero = numero.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        raise ErrorValidacion(f"El campo «{campo}» debe ser un importe válido.") from None
    if numero < 0:
        raise ErrorValidacion(f"El campo «{campo}» no puede ser negativo.")
    if numero > _MAX_IMPORTE:
        raise ErrorValidacion(f"El campo «{campo}» admite hasta $99,999,999.99.")
    return numero


def fecha(valor: str | None, campo: str) -> date:
    """Acepta AAAA-MM-DD (lo que envía <input type="date">) o DD/MM/AAAA."""
    texto = (valor or "").strip()
    if not texto:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ErrorValidacion(f"El campo «{campo}» debe ser una fecha válida (día/mes/año).")


def hora(valor: str | None, campo: str) -> time:
    """Formato de 24 horas, HH:MM (lo que envía <input type="time">)."""
    texto = (valor or "").strip()
    if not texto:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    for formato in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(texto, formato).time().replace(second=0)
        except ValueError:
            continue
    raise ErrorValidacion(f"El campo «{campo}» debe ser una hora válida en formato de 24 horas (ej. 19:30).")


def id_seleccionado(valor: str | None, campo: str) -> int:
    """Identificador elegido en una lista desplegable."""
    if not str(valor or "").strip():
        raise ErrorValidacion(f"Elige un valor en «{campo}».")
    return entero_positivo(valor, campo)
