"""Acceso a datos para reservaciones."""
from typing import List, Optional

from solucion.datos.conexion import abrir_conexion
from solucion.modelos.reservacion import Reservacion, ESTADO_ACTIVA, ESTADO_CANCELADA


def insertar_reservacion(reservacion: Reservacion) -> None:
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                """
                INSERT INTO reservaciones
                    (id, carne_estudiante, codigo_sala, fecha, hora_inicio,
                     duracion, cantidad_personas, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reservacion.id,
                    reservacion.carne_estudiante,
                    reservacion.codigo_sala,
                    reservacion.fecha,
                    reservacion.hora_inicio,
                    reservacion.duracion,
                    reservacion.cantidad_personas,
                    reservacion.estado,
                ),
            )


def insertar_serie(reservaciones: List[Reservacion]) -> None:
    """RF-14/RNF-06: guarda toda la serie en una única transacción."""
    with abrir_conexion() as conexion:
        with conexion:
            conexion.executemany(
                """
                INSERT INTO reservaciones
                    (id, carne_estudiante, codigo_sala, fecha, hora_inicio,
                     duracion, cantidad_personas, estado, serie_id, numero_ocurrencia)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        r.id, r.carne_estudiante, r.codigo_sala, r.fecha, r.hora_inicio,
                        r.duracion, r.cantidad_personas, r.estado, r.serie_id, r.numero_ocurrencia,
                    )
                    for r in reservaciones
                ],
            )


def actualizar_reservacion(reservacion: Reservacion) -> None:
    """RF-13: actualiza datos editables sin cambiar el identificador."""
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                """
                UPDATE reservaciones
                SET codigo_sala = ?, fecha = ?, hora_inicio = ?, duracion = ?, cantidad_personas = ?
                WHERE id = ?
                """,
                (
                    reservacion.codigo_sala, reservacion.fecha, reservacion.hora_inicio,
                    reservacion.duracion, reservacion.cantidad_personas, reservacion.id,
                ),
            )


def listar_reservaciones() -> List[Reservacion]:
    """RF-06: historial completo, ordenado por fecha y hora."""
    with abrir_conexion() as conexion:
        filas = conexion.execute(
            "SELECT * FROM reservaciones ORDER BY fecha ASC, hora_inicio ASC"
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]


def buscar_por_carne(carne_estudiante: str) -> List[Reservacion]:
    """RF-07: historial sin distinguir mayúsculas/minúsculas."""
    with abrir_conexion() as conexion:
        filas = conexion.execute(
            """
            SELECT * FROM reservaciones
            WHERE carne_estudiante = ? COLLATE NOCASE
            ORDER BY fecha ASC, hora_inicio ASC
            """,
            (carne_estudiante,),
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]


def listar_por_serie(serie_id: str) -> List[Reservacion]:
    """RF-14: devuelve todas las ocurrencias de una serie."""
    with abrir_conexion() as conexion:
        filas = conexion.execute(
            "SELECT * FROM reservaciones WHERE serie_id = ? ORDER BY numero_ocurrencia ASC",
            (serie_id,),
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]


def cancelar_ocurrencias_futuras_serie(serie_id: str, desde_fecha: str) -> int:
    """RF-14: cancela ocurrencias activas desde una fecha incluida."""
    with abrir_conexion() as conexion:
        with conexion:
            cursor = conexion.execute(
                """
                UPDATE reservaciones SET estado = ?
                WHERE serie_id = ? AND estado = ? AND fecha >= ?
                """,
                (ESTADO_CANCELADA, serie_id, ESTADO_ACTIVA, desde_fecha),
            )
            return cursor.rowcount


def obtener_reservacion(id_reservacion: str) -> Optional[Reservacion]:
    with abrir_conexion() as conexion:
        fila = conexion.execute(
            "SELECT * FROM reservaciones WHERE id = ?", (id_reservacion,)
        ).fetchone()
        if fila is None:
            return None
        return _fila_a_reservacion(fila)


def listar_activas_por_sala_fecha(codigo_sala: str, fecha: str) -> List[Reservacion]:
    """Usado para validar superposición de horarios (RN-09, RN-10)."""
    with abrir_conexion() as conexion:
        filas = conexion.execute(
            """
            SELECT * FROM reservaciones
            WHERE codigo_sala = ? AND fecha = ? AND estado = ?
            """,
            (codigo_sala, fecha, ESTADO_ACTIVA),
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]


def contar_activas_estudiante_desde(carne_estudiante: str, fecha_desde: str) -> int:
    """RN-11: cuenta reservas activas presentes o futuras de un estudiante."""
    with abrir_conexion() as conexion:
        fila = conexion.execute(
            """
            SELECT COUNT(*) AS total FROM reservaciones
            WHERE carne_estudiante = ? AND estado = ? AND fecha >= ?
            """,
            (carne_estudiante, ESTADO_ACTIVA, fecha_desde),
        ).fetchone()
        return fila["total"]


def cancelar_reservacion_bd(id_reservacion: str) -> None:
    """RF-09/RN-12: conserva la reserva y solo cambia su estado."""
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                "UPDATE reservaciones SET estado = ? WHERE id = ?",
                (ESTADO_CANCELADA, id_reservacion),
            )


def generar_siguiente_id() -> str:
    """RN-13: genera R0001, R0002, ... sin reutilizar números."""
    with abrir_conexion() as conexion:
        fila = conexion.execute(
            "SELECT id FROM reservaciones ORDER BY CAST(SUBSTR(id, 2) AS INTEGER) DESC LIMIT 1"
        ).fetchone()
        if fila is None:
            siguiente_numero = 1
        else:
            siguiente_numero = int(fila["id"][1:]) + 1
        return f"R{siguiente_numero:04d}"


def _fila_a_reservacion(fila) -> Reservacion:
    columnas = fila.keys()
    return Reservacion(
        id=fila["id"],
        carne_estudiante=fila["carne_estudiante"],
        codigo_sala=fila["codigo_sala"],
        fecha=fila["fecha"],
        hora_inicio=fila["hora_inicio"],
        duracion=fila["duracion"],
        cantidad_personas=fila["cantidad_personas"],
        estado=fila["estado"],
        serie_id=fila["serie_id"] if "serie_id" in columnas else None,
        numero_ocurrencia=fila["numero_ocurrencia"] if "numero_ocurrencia" in columnas else None,
    )


