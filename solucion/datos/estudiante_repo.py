"""Acceso a datos para estudiantes (soporta RF-02, RF-03 y RF-11)."""
from typing import List, Optional

from solucion.datos.conexion import abrir_conexion
from solucion.modelos.estudiante import Estudiante


def existe_carne(carne: str) -> bool:
    with abrir_conexion() as conexion:
        fila = conexion.execute(
            "SELECT 1 FROM estudiantes WHERE carne = ?", (carne,)
        ).fetchone()
        return fila is not None


def insertar_estudiante(estudiante: Estudiante) -> None:
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                "INSERT INTO estudiantes (carne, nombre, correo, activo) VALUES (?, ?, ?, ?)",
                (estudiante.carne, estudiante.nombre, estudiante.correo, int(estudiante.activo)),
            )


def actualizar_estudiante(estudiante: Estudiante) -> None:
    """RF-11: actualiza nombre, correo y estado. El carné nunca se modifica."""
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                "UPDATE estudiantes SET nombre = ?, correo = ?, activo = ? WHERE carne = ?",
                (estudiante.nombre, estudiante.correo, int(estudiante.activo), estudiante.carne),
            )


def obtener_estudiante(carne: str) -> Optional[Estudiante]:
    with abrir_conexion() as conexion:
        fila = conexion.execute(
            "SELECT * FROM estudiantes WHERE carne = ?", (carne,)
        ).fetchone()
        if fila is None:
            return None
        return _fila_a_estudiante(fila)


def listar_estudiantes() -> List[Estudiante]:
    """RF-03: activos e inactivos, ordenados alfabéticamente por nombre."""
    with abrir_conexion() as conexion:
        filas = conexion.execute(
            "SELECT * FROM estudiantes ORDER BY nombre COLLATE NOCASE ASC"
        ).fetchall()
        return [_fila_a_estudiante(fila) for fila in filas]


def _fila_a_estudiante(fila) -> Estudiante:
    return Estudiante(
        carne=fila["carne"],
        nombre=fila["nombre"],
        correo=fila["correo"],
        activo=bool(fila["activo"]),
    )
