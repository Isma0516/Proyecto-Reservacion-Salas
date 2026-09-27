"""
Acceso a datos para salas (soporta RF-04 consulta).

La gestión completa de salas (crear/editar desde la interfaz) corresponde
a RF-12, que queda fuera del alcance de esta entrega. `insertar_sala` se
incluye únicamente como utilidad para cargar datos de prueba/demostración.
"""
from typing import List, Optional

from solucion.datos.conexion import obtener_conexion
from solucion.modelos.sala import Sala


def insertar_sala(sala: Sala) -> None:
    conexion = obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                "INSERT INTO salas (codigo, nombre, capacidad, estado) VALUES (?, ?, ?, ?)",
                (sala.codigo, sala.nombre, sala.capacidad, sala.estado),
            )
    finally:
        conexion.close()


def actualizar_sala(sala: Sala) -> None:
    """RF-12: actualiza nombre, capacidad y estado. El código nunca se modifica."""
    conexion = obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                "UPDATE salas SET nombre = ?, capacidad = ?, estado = ? WHERE codigo = ?",
                (sala.nombre, sala.capacidad, sala.estado, sala.codigo),
            )
    finally:
        conexion.close()


def obtener_sala(codigo: str) -> Optional[Sala]:
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            "SELECT * FROM salas WHERE codigo = ?", (codigo,)
        ).fetchone()
        if fila is None:
            return None
        return _fila_a_sala(fila)
    finally:
        conexion.close()


def listar_salas() -> List[Sala]:
    """RF-04: incluye tanto salas disponibles como fuera de servicio."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            "SELECT * FROM salas ORDER BY codigo ASC"
        ).fetchall()
        return [_fila_a_sala(fila) for fila in filas]
    finally:
        conexion.close()


def _fila_a_sala(fila) -> Sala:
    return Sala(
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        capacidad=fila["capacidad"],
        estado=fila["estado"],
    )
