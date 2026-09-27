"""Acceso a datos para el historial de auditoría (RF-17)."""
from datetime import datetime
from typing import List, NamedTuple, Optional

from solucion.datos.conexion import abrir_conexion


class RegistroAuditoria(NamedTuple):
    id: int
    fecha_hora: str
    tipo_accion: str
    entidad: str
    identificador: str
    detalle: Optional[str]


def registrar(tipo_accion: str, entidad: str, identificador: str, detalle: str = None) -> None:
    """Registra una acción exitosa; no expone edición ni borrado del historial."""
    with abrir_conexion() as conexion:
        with conexion:
            conexion.execute(
                """
                INSERT INTO auditoria (fecha_hora, tipo_accion, entidad, identificador, detalle)
                VALUES (?, ?, ?, ?, ?)
                """,
                (datetime.now().isoformat(timespec="seconds"), tipo_accion, entidad, identificador, detalle),
            )


def listar(entidad: str = None, identificador: str = None) -> List[RegistroAuditoria]:
    """Consulta el historial, opcionalmente filtrado por entidad y/o identificador."""
    with abrir_conexion() as conexion:
        consulta = "SELECT * FROM auditoria WHERE 1 = 1"
        parametros = []
        if entidad is not None:
            consulta += " AND entidad = ?"
            parametros.append(entidad)
        if identificador is not None:
            consulta += " AND identificador = ?"
            parametros.append(identificador)
        consulta += " ORDER BY id ASC"
        filas = conexion.execute(consulta, parametros).fetchall()
        return [
            RegistroAuditoria(
                id=fila["id"],
                fecha_hora=fila["fecha_hora"],
                tipo_accion=fila["tipo_accion"],
                entidad=fila["entidad"],
                identificador=fila["identificador"],
                detalle=fila["detalle"],
            )
            for fila in filas
        ]
        
