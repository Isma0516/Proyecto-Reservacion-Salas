"""
Objeto de resultado estándar que devuelven las funciones de la capa de negocio.

Se usa en lugar de dejar que las excepciones internas lleguen a la interfaz,
para cumplir con RNF-05 (una entrada inválida no debe cerrar el programa ni
mostrar trazas técnicas a la persona usuaria).
"""
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Resultado:
    exito: bool
    mensaje: str
    datos: Optional[Any] = None
    
