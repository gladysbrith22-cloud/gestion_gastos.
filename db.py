"""Capa de acceso a datos (SQLite)."""
import os
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS gastos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL,
    fecha       TEXT    NOT NULL,              -- formato ISO: YYYY-MM-DD
    descripcion TEXT    NOT NULL,
    monto       REAL    NOT NULL CHECK (monto > 0),
    creado_en   TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_gastos_usuario_fecha ON gastos (usuario_id, fecha);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas y el usuario administrador si no existen."""
    path = current_app.config["DATABASE"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    db = get_db()
    db.executescript(SCHEMA)
    existe = db.execute(
        "SELECT 1 FROM usuarios WHERE username = ?", (current_app.config["ADMIN_USER"],)
    ).fetchone()
    if not existe:
        db.execute(
            "INSERT INTO usuarios (username, password_hash) VALUES (?, ?)",
            (
                current_app.config["ADMIN_USER"],
                generate_password_hash(current_app.config["ADMIN_PASSWORD"]),
            ),
        )
        db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
