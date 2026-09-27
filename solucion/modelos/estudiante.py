"""Modelo de datos para un estudiante (relacionado con RF-02, RF-03, RF-11)."""
from dataclasses import dataclass


@dataclass
class Estudiante:
    carne: str
    nombre: str
    correo: str
    activo: bool = True

