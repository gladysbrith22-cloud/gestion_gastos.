"""Configuración central de la aplicación."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # En producción define SECRET_KEY como variable de entorno.
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "gastos.db"))
    ADMIN_USER = "admin"
    ADMIN_PASSWORD = "123"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
