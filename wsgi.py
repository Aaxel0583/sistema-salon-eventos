"""
Punto de entrada.
  Desarrollo:  flask --app wsgi run --debug
  Producción:  gunicorn wsgi:app
"""
from app import create_app

app = create_app()
