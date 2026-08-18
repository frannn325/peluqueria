"""Funciones sencillas para trabajar con la base de datos SQLite."""

import sqlite3
from pathlib import Path


RUTA_BASE_DE_DATOS = Path(__file__).parent / "barberia.db"

SERVICIOS_INICIALES = [
    ("Corte clásico", 8000),
    ("Corte + ceja", 8500),
    ("Tintura", 25000),
]


def obtener_conexion():
    """Abre una conexión con SQLite y permite acceder por nombre a las columnas."""
    conexion = sqlite3.connect(RUTA_BASE_DE_DATOS)
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_base_de_datos():
    """Crea la tabla servicios y carga los datos iniciales una sola vez."""
    with obtener_conexion() as conexion:
        conexion.execute(
            """
            CREATE TABLE IF NOT EXISTS servicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                precio INTEGER NOT NULL
            )
            """
        )

        cantidad_de_servicios = conexion.execute(
            "SELECT COUNT(*) FROM servicios"
        ).fetchone()[0]

        if cantidad_de_servicios == 0:
            conexion.executemany(
                "INSERT INTO servicios (nombre, precio) VALUES (?, ?)",
                SERVICIOS_INICIALES,
            )


def obtener_servicios():
    """Devuelve todos los servicios guardados en la base de datos."""
    with obtener_conexion() as conexion:
        return conexion.execute(
            "SELECT id, nombre, precio FROM servicios ORDER BY id"
        ).fetchall()
