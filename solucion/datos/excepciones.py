"""Excepciones expuestas por la capa de persistencia.
La capa de negocio utiliza estas excepciones en lugar de depender directamente de
clases de excepción específicas de SQLite. Esto mantiene los detalles de persistencia dentro de
solucion.datos y conserva la separación de responsabilidades.

"""


class ErrorPersistencia(Exception):
    """Error base para fallos al leer o escribir datos persistentes."""


class ErrorIntegridadDatos(ErrorPersistencia):
    """Se genera cuando una operación de persistencia viola una regla de integridad de los datos."""

