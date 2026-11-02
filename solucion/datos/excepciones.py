"""Errores controlados por la capa de persistencia."""


class ErrorPersistencia(Exception):
    """Error durante la lectura o escritura de datos."""


class ErrorIntegridadDatos(ErrorPersistencia):
    """Violación de una restricción de integridad."""
