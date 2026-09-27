"""Modelo de datos para una reservación (relacionado con RF-05 a RF-09, RF-13, RF-14)."""
from dataclasses import dataclass
from typing import Optional

ESTADO_ACTIVA = "activa"
ESTADO_CANCELADA = "cancelada"


@dataclass
class Reservacion:
    id: str
    carne_estudiante: str
    codigo_sala: str
    fecha: str          # formato "AAAA-MM-DD"
    hora_inicio: str    # formato "HH:MM", siempre en hora completa (RN-04)
    duracion: int        # 1 o 2 horas (RN-06)
    cantidad_personas: int
    estado: str = ESTADO_ACTIVA
    serie_id: Optional[str] = None            # RF-14: agrupa las ocurrencias de una misma serie
    numero_ocurrencia: Optional[int] = None   # RF-14: posición dentro de la serie (1..N)
