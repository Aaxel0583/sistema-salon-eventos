"""
Instalador del esquema · PKG-06

Ejecuta en orden los scripts numerados de esta carpeta contra la base
indicada en DATABASE_URL (.env). Útil en Windows, donde no siempre se
tiene psql instalado.

  python -m basedatos.instalar              # 01 a 05
  python -m basedatos.instalar --reiniciar  # 00 (borra todo) y luego 01 a 05
  python -m basedatos.instalar --solo 02_reglas_sprint1.sql 05_reglas_sprint2.sql   # actualizar una base ya instalada

Las advertencias que emite la base (por ejemplo, eventos anteriores que ya
violan una regla recién instalada) se imprimen tal cual.
"""
import argparse
import sys
from pathlib import Path

import psycopg

from app.config import Configuracion

CARPETA = Path(__file__).parent
SCRIPTS = ["01_esquema.sql", "02_reglas_sprint1.sql", "03_semilla.sql", "04_eventos_sprint2.sql",
           "05_reglas_sprint2.sql"]


def _mostrar_aviso(aviso) -> None:
    """Solo las advertencias (RAISE WARNING de los scripts); los NOTICE de rutina se omiten."""
    if aviso.severity_nonlocalized == "WARNING":
        print(f"   Aviso: {aviso.message_primary}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Instala el esquema de la base de datos")
    parser.add_argument("--reiniciar", action="store_true",
                        help="borra el esquema antes de instalar (solo desarrollo)")
    parser.add_argument("--url", help="cadena de conexión distinta a DATABASE_URL")
    parser.add_argument("--solo", nargs="+", metavar="SCRIPT",
                        help="ejecuta solo estos scripts (p. ej. al pasar de un sprint a otro)")
    args = parser.parse_args(argv)

    url = args.url or Configuracion.desde_entorno().database_url
    if args.solo:
        desconocidos = [s for s in args.solo if s not in SCRIPTS]
        if desconocidos:
            print(f"Scripts desconocidos: {', '.join(desconocidos)}", file=sys.stderr)
            return 1
        scripts = args.solo
    else:
        scripts = (["00_limpiar.sql"] if args.reiniciar else []) + SCRIPTS

    if args.reiniciar:
        respuesta = input("Se borrarán TODAS las tablas y datos. Escribe BORRAR para continuar: ")
        if respuesta.strip() != "BORRAR":
            print("Cancelado.")
            return 1

    with psycopg.connect(url, autocommit=True) as conexion:
        conexion.add_notice_handler(_mostrar_aviso)
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
