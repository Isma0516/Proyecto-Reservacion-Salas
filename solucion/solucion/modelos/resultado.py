"""Resultado controlado de una operación de negocio."""
from dataclasses import dataclass
from typing import Any


@dataclass
class Resultado:
    exito: bool
    mensaje: str
    datos: Any = None
