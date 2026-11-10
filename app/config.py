"""
Configuración de la instalación.

Componente transversal · Decisión DA-06 · RD-06 · RNF-07 · RNF-17
Todo lo que cambia entre una instalación y otra (nombre del negocio,
conexión, llave de sesión) se lee del archivo .env y nunca del código.
"""
import os
from dataclasses import dataclass
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class ErrorConfiguracion(RuntimeError):
    """Falta un parámetro obligatorio en el archivo .env."""


def _obligatoria(nombre: str) -> str:
    valor = os.getenv(nombre, "").strip()
    if not valor:
        raise ErrorConfiguracion(
            f"Falta la variable {nombre} en el archivo .env. "
            "Copia .env.example como .env y complétalo."
        )
    return valor


@dataclass(frozen=True)
class Configuracion:
    """Parámetros de la instalación, inmutables durante la ejecución."""

    nombre_negocio: str
    database_url: str
    secret_key: str
    cookie_segura: bool
    pool_min: int
    pool_max: int

    # Reglas fijas del dominio (SRS); no dependen de la instalación.
    MAX_INTENTOS_FALLIDOS: int = 5          # RF-03
    DURACION_SESION: timedelta = timedelta(hours=8)

    @classmethod
    def desde_entorno(cls) -> "Configuracion":
        return cls(
            nombre_negocio=os.getenv("NOMBRE_NEGOCIO", "Salón de Eventos").strip(),
            database_url=_obligatoria("DATABASE_URL"),
            secret_key=_obligatoria("SECRET_KEY"),
            cookie_segura=os.getenv("COOKIE_SEGURA", "0") == "1",
            pool_min=int(os.getenv("POOL_MIN", "1")),
            pool_max=int(os.getenv("POOL_MAX", "5")),
        )
