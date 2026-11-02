"""RF-15: resumen y filtros combinables para el panel principal."""
from solucion.datos import reservacion_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.resultado import Resultado
from solucion.negocio.validaciones import convertir_fecha


def resumen():
    try:return Resultado(True,"Panel actualizado.",reservacion_repo.resumen_panel())
    except ErrorPersistencia:return Resultado(False,"No fue posible consultar el panel.")


def filtrar(fecha_desde=None,fecha_hasta=None,sala=None,estado=None,carne=None):
    if fecha_desde and convertir_fecha(fecha_desde) is None:return Resultado(False,"La fecha inicial es inválida.")
    if fecha_hasta and convertir_fecha(fecha_hasta) is None:return Resultado(False,"La fecha final es inválida.")
    if fecha_desde and fecha_hasta and fecha_desde>fecha_hasta:
        return Resultado(False,"La fecha final no puede ser anterior a la inicial.")
    if estado and estado not in ("activa","cancelada"):
        return Resultado(False,"El estado indicado es inválido.")
    try:
        datos=reservacion_repo.filtrar(fecha_desde,fecha_hasta,sala,estado,carne)
        return Resultado(True,f"Se encontraron {len(datos)} reservaciones.",datos)
    except ErrorPersistencia:return Resultado(False,"No fue posible filtrar reservaciones.")
