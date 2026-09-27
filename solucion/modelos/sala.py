"""Modelo de datos para una sala de estudio (relacionado con RF-04, RF-12)."""
from dataclasses import dataclass

ESTADO_DISPONIBLE = "disponible"
ESTADO_FUERA_SERVICIO = "fuera_servicio"


@dataclass
class Sala:
    codigo: str
    nombre: str
    capacidad: int
    estado: str = ESTADO_DISPONIBLE

