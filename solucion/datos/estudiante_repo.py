"""Acceso a datos para estudiantes (soporta RF-02 registro y RF-03 consulta)."""
from typing import List, Optional

from solucion.datos.conexion import obtener_conexion
from solucion.modelos.estudiante import Estudiante


def existe_carne(carne: str) -> bool:
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            "SELECT 1 FROM estudiantes WHERE carne = ?", (carne,)
        ).fetchone()
        return fila is not None
    finally:
        conexion.close()


def insertar_estudiante(estudiante: Estudiante) -> None:
    conexion = obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                "INSERT INTO estudiantes (carne, nombre, correo, activo) VALUES (?, ?, ?, ?)",
                (estudiante.carne, estudiante.nombre, estudiante.correo, int(estudiante.activo)),
            )
    finally:
        conexion.close()


def actualizar_estudiante(estudiante: Estudiante) -> None:
    """RF-11: actualiza nombre, correo y estado. El carné nunca se modifica."""
    conexion = obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                "UPDATE estudiantes SET nombre = ?, correo = ?, activo = ? WHERE carne = ?",
                (estudiante.nombre, estudiante.correo, int(estudiante.activo), estudiante.carne),
            )
    finally:
        conexion.close()


def obtener_estudiante(carne: str) -> Optional[Estudiante]:
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            "SELECT * FROM estudiantes WHERE carne = ?", (carne,)
        ).fetchone()
        if fila is None:
            return None
        return _fila_a_estudiante(fila)
    finally:
        conexion.close()


def listar_estudiantes() -> List[Estudiante]:
    """RF-03: activos e inactivos, ordenados alfabéticamente por nombre."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            "SELECT * FROM estudiantes ORDER BY nombre COLLATE NOCASE ASC"
        ).fetchall()
        return [_fila_a_estudiante(fila) for fila in filas]
    finally:
        conexion.close()


def _fila_a_estudiante(fila) -> Estudiante:
    return Estudiante(
        carne=fila["carne"],
        nombre=fila["nombre"],
        correo=fila["correo"],
        activo=bool(fila["activo"]),
    )
