"""Acceso a datos para reservaciones (soporta RF-05, RF-08, RF-09)."""
from typing import List, Optional

from solucion.datos.conexion import obtener_conexion
from solucion.modelos.reservacion import Reservacion, ESTADO_ACTIVA, ESTADO_CANCELADA


def insertar_reservacion(reservacion: Reservacion) -> None:
    conexion = obtener_conexion()
    try:
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
    finally:
        conexion.close()


def insertar_serie(reservaciones: List[Reservacion]) -> None:
    """
    RF-14: guarda todas las ocurrencias de una serie recurrente en una sola
    transacción. Si una sola fila fallara, no queda ninguna guardada
    (RNF-06: integridad).
    """
    conexion = obtener_conexion()
    try:
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
    finally:
        conexion.close()


def actualizar_reservacion(reservacion: Reservacion) -> None:
    """RF-13: actualiza fecha, hora, duración, sala y cantidad. El ID no cambia."""
    conexion = obtener_conexion()
    try:
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
    finally:
        conexion.close()


def listar_reservaciones() -> List[Reservacion]:
    """RF-06: historial completo (activas y canceladas), por fecha y luego hora."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            "SELECT * FROM reservaciones ORDER BY fecha ASC, hora_inicio ASC"
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]
    finally:
        conexion.close()


def buscar_por_carne(carne_estudiante: str) -> List[Reservacion]:
    """RF-07: historial de un estudiante, sin distinguir mayúsculas/minúsculas."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            """
            SELECT * FROM reservaciones
            WHERE carne_estudiante = ? COLLATE NOCASE
            ORDER BY fecha ASC, hora_inicio ASC
            """,
            (carne_estudiante,),
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]
    finally:
        conexion.close()


def listar_por_serie(serie_id: str) -> List[Reservacion]:
    """RF-14: todas las ocurrencias (activas o canceladas) de una serie."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            "SELECT * FROM reservaciones WHERE serie_id = ? ORDER BY numero_ocurrencia ASC",
            (serie_id,),
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]
    finally:
        conexion.close()


def cancelar_ocurrencias_futuras_serie(serie_id: str, desde_fecha: str) -> int:
    """
    RF-14: cancela todas las ocurrencias activas de una serie a partir de
    (e incluyendo) `desde_fecha`. Devuelve cuántas filas se cancelaron.
    """
    conexion = obtener_conexion()
    try:
        with conexion:
            cursor = conexion.execute(
                """
                UPDATE reservaciones SET estado = ?
                WHERE serie_id = ? AND estado = ? AND fecha >= ?
                """,
                (ESTADO_CANCELADA, serie_id, ESTADO_ACTIVA, desde_fecha),
            )
            return cursor.rowcount
    finally:
        conexion.close()


def obtener_reservacion(id_reservacion: str) -> Optional[Reservacion]:
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            "SELECT * FROM reservaciones WHERE id = ?", (id_reservacion,)
        ).fetchone()
        if fila is None:
            return None
        return _fila_a_reservacion(fila)
    finally:
        conexion.close()


def listar_activas_por_sala_fecha(codigo_sala: str, fecha: str) -> List[Reservacion]:
    """Usado para validar superposición de horarios (RN-09, RN-10)."""
    conexion = obtener_conexion()
    try:
        filas = conexion.execute(
            """
            SELECT * FROM reservaciones
            WHERE codigo_sala = ? AND fecha = ? AND estado = ?
            """,
            (codigo_sala, fecha, ESTADO_ACTIVA),
        ).fetchall()
        return [_fila_a_reservacion(fila) for fila in filas]
    finally:
        conexion.close()


def contar_activas_estudiante_desde(carne_estudiante: str, fecha_desde: str) -> int:
    """
    Cuenta reservas activas presentes o futuras de un estudiante (RN-11).
    `fecha_desde` normalmente es la fecha de hoy en formato "AAAA-MM-DD".
    """
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            """
            SELECT COUNT(*) AS total FROM reservaciones
            WHERE carne_estudiante = ? AND estado = ? AND fecha >= ?
            """,
            (carne_estudiante, ESTADO_ACTIVA, fecha_desde),
        ).fetchone()
        return fila["total"]
    finally:
        conexion.close()


def cancelar_reservacion_bd(id_reservacion: str) -> None:
    """RF-09/RN-12: la reserva permanece en el historial, solo cambia su estado."""
    conexion = obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                "UPDATE reservaciones SET estado = ? WHERE id = ?",
                (ESTADO_CANCELADA, id_reservacion),
            )
    finally:
        conexion.close()


def generar_siguiente_id() -> str:
    """
    RN-13: genera identificadores R0001, R0002, ... sin reutilizar números,
    incluso si una reserva anterior fue cancelada (nunca se borran filas).
    """
    conexion = obtener_conexion()
    try:
        fila = conexion.execute(
            "SELECT id FROM reservaciones ORDER BY CAST(SUBSTR(id, 2) AS INTEGER) DESC LIMIT 1"
        ).fetchone()
        if fila is None:
            siguiente_numero = 1
        else:
            siguiente_numero = int(fila["id"][1:]) + 1
        return f"R{siguiente_numero:04d}"
    finally:
        conexion.close()


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
