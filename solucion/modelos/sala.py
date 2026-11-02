"""Entidad sala de estudio."""
from dataclasses import dataclass

ESTADO_DISPONIBLE = "disponible"
ESTADO_FUERA_SERVICIO = "fuera_de_servicio"


@dataclass
class Sala:
    codigo: str
    nombre: str
    capacidad: int
    estado: str = ESTADO_DISPONIBLE
