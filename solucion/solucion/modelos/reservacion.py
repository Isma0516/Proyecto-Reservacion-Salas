"""Entidad reservación."""
from dataclasses import dataclass
from typing import Optional

ESTADO_ACTIVA = "activa"
ESTADO_CANCELADA = "cancelada"


@dataclass
class Reservacion:
    id: str
    carne_estudiante: str
    codigo_sala: str
    fecha: str
    hora_inicio: str
    duracion: int
    cantidad_personas: int
    estado: str = ESTADO_ACTIVA
    serie_id: Optional[str] = None
    numero_ocurrencia: Optional[int] = None
