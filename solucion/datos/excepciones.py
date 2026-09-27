"""Exceptions exposed by the persistence layer.

The business layer uses these exceptions instead of depending directly on
SQLite-specific exception classes. This keeps persistence details inside
``solucion.datos`` and preserves separation of responsibilities.
"""


class ErrorPersistencia(Exception):
    """Base error for failures while reading or writing persistent data."""


class ErrorIntegridadDatos(ErrorPersistencia):
    """Raised when a persistence operation violates a data integrity rule."""
