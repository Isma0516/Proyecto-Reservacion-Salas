"""Entidad estudiante."""
from dataclasses import dataclass


@dataclass
class Estudiante:
    carne: str
    nombre: str
    correo: str
    activo: bool = True
