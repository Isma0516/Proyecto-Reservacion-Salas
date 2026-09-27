"""Acceso a datos para salas (soporta RF-04 y persistencia de RF-12)."""
from typing import List, Optional

from solucion.datos.conexion import abrir_conexion
from solucion.modelos.sala import Sala


def insertar_sala(sala: Sala) -> None:
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                "INSERT INTO salas (codigo, nombre, capacidad, estado) VALUES (?, ?, ?, ?)",
                (sala.codigo, sala.nombre, sala.capacidad, sala.estado),
            )


def actualizar_sala(sala: Sala) -> None:
    """RF-12: actualiza nombre, capacidad y estado. El código nunca se modifica."""
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                "UPDATE salas SET nombre = ?, capacidad = ?, estado = ? WHERE codigo = ?",
                (sala.nombre, sala.capacidad, sala.estado, sala.codigo),
            )


def obtener_sala(codigo: str) -> Optional[Sala]:
    with abrir_conexion() as conexion:
        fila = conexion.execute(
            "SELECT * FROM salas WHERE codigo = ?", (codigo,)
        ).fetchone()
        if fila is None:
            return None
        return _fila_a_sala(fila)


def listar_salas() -> List[Sala]:
    """RF-04: incluye tanto salas disponibles como fuera de servicio."""
    with abrir_conexion() as conexion:
        filas = conexion.execute(
            "SELECT * FROM salas ORDER BY codigo ASC"
        ).fetchall()
        return [_fila_a_sala(fila) for fila in filas]


def _fila_a_sala(fila) -> Sala:
    return Sala(
        codigo=fila["codigo"],
        nombre=fila["nombre"],
        capacidad=fila["capacidad"],
        estado=fila["estado"],
    )
