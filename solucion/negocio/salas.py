"""Reglas de negocio para salas (RF-04 consulta; RF-12 gestión queda pendiente)."""
from solucion.datos import sala_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.resultado import Resultado


def consultar_salas() -> Resultado:
    """RF-04: incluye tanto salas disponibles como fuera de servicio."""
    try:
        salas = sala_repo.listar_salas()
    except ErrorPersistencia:
        return Resultado(False, "No fue posible consultar las salas en este momento.")

    return Resultado(True, f"Se encontraron {len(salas)} sala(s).", salas)
