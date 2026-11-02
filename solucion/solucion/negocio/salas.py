"""Flujos RF-04 y RF-12, incluyendo restricciones de capacidad futura."""
from datetime import datetime
from solucion.datos import sala_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.resultado import Resultado
from solucion.modelos.sala import Sala, ESTADO_DISPONIBLE, ESTADO_FUERA_SERVICIO
from solucion.negocio import validaciones as v


def consultar_salas():
    try:
        datos=sala_repo.listar_salas()
        return Resultado(True,f"Se encontraron {len(datos)} salas.",datos)
    except ErrorPersistencia:
        return Resultado(False,"No fue posible consultar salas.")


def _validar(nombre,capacidad,estado):
    if not v.texto_no_vacio(nombre): return "El nombre de la sala es obligatorio."
    if type(capacidad) is not int or capacidad <= 0: return "La capacidad debe ser un entero mayor que cero."
    if estado not in (ESTADO_DISPONIBLE,ESTADO_FUERA_SERVICIO): return "El estado de sala es inválido."
    return None


def registrar_sala(codigo,nombre,capacidad,estado=ESTADO_DISPONIBLE):
    if not v.texto_no_vacio(codigo):return Resultado(False,"El código de sala es obligatorio.")
    err=_validar(nombre,capacidad,estado)
    if err:return Resultado(False,err)
    codigo=codigo.strip().upper()
    try:
        if sala_repo.obtener_sala(codigo):return Resultado(False,"Ya existe una sala con ese código.")
        sala=Sala(codigo,nombre.strip(),capacidad,estado)
        sala_repo.insertar_sala(sala)
        return Resultado(True,"Sala registrada correctamente.",sala)
    except ErrorPersistencia:return Resultado(False,"No fue posible registrar la sala.")


def modificar_sala(codigo,nombre,capacidad,estado):
    err=_validar(nombre,capacidad,estado)
    if err:return Resultado(False,err)
    try:
        sala=sala_repo.obtener_sala(codigo)
        if sala is None:return Resultado(False,"La sala indicada no existe.")
        ahora=datetime.now()
        mayor=sala_repo.maximo_personas_futuras(sala.codigo,ahora.date().isoformat(),ahora.strftime("%H:%M:%S"))
        if capacidad < mayor:
            return Resultado(False,f"La capacidad no puede ser inferior a {mayor}, porque existen reservaciones futuras.")
        sala_repo.actualizar_sala(sala.codigo,nombre.strip(),capacidad,estado)
        return Resultado(True,"Sala actualizada correctamente; su código permanece sin cambios.")
    except ErrorPersistencia:return Resultado(False,"No fue posible modificar la sala.")


def intentar_cambiar_codigo(codigo_actual,codigo_nuevo):
    return Resultado(False,"El código de sala no puede modificarse.")
