"""
Instalador del esquema · PKG-06

Ejecuta en orden los scripts numerados de esta carpeta contra la base
indicada en DATABASE_URL (.env). Útil en Windows, donde no siempre se
tiene psql instalado.

  python -m basedatos.instalar              # 01, 02, 03
  python -m basedatos.instalar --reiniciar  # 00 (borra todo) y luego 01, 02, 03
"""
import argparse
import sys
from pathlib import Path

import psycopg

from app.config import Configuracion

CARPETA = Path(__file__).parent
SCRIPTS = ["01_esquema.sql", "02_reglas_sprint1.sql", "03_semilla.sql"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Instala el esquema de la base de datos")
    parser.add_argument("--reiniciar", action="store_true",
                        help="borra el esquema antes de instalar (solo desarrollo)")
    parser.add_argument("--url", help="cadena de conexión distinta a DATABASE_URL")
    args = parser.parse_args(argv)

    url = args.url or Configuracion.desde_entorno().database_url
    scripts = (["00_limpiar.sql"] if args.reiniciar else []) + SCRIPTS

    if args.reiniciar:
        respuesta = input("Se borrarán TODAS las tablas y datos. Escribe BORRAR para continuar: ")
        if respuesta.strip() != "BORRAR":
            print("Cancelado.")
            return 1

    with psycopg.connect(url, autocommit=True) as conexion:
        for nombre in scripts:
            print(f"-> {nombre}")
            try:
                conexion.execute((CARPETA / nombre).read_text(encoding="utf-8"))
            except psycopg.Error as error:
                print(f"   Falló: {error}", file=sys.stderr)
                return 1
    print("Esquema instalado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
