"""Operaciones RF-05 a RF-09, RF-13 y RF-14 con las reglas RN-01 a RN-13."""
from __future__ import annotations

from datetime import date, datetime, timedelta, time
from solucion.datos import estudiante_repo, sala_repo, reservacion_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.reservacion import Reservacion, ESTADO_CANCELADA
from solucion.modelos.resultado import Resultado
from solucion.modelos.sala import ESTADO_DISPONIBLE
from solucion.negocio import validaciones as v

MAXIMO_RESERVAS_ACTIVAS_POR_ESTUDIANTE=3


def _validar_datos_basicos(fecha_str,hora_inicio_str,duracion,cantidad_personas):
    mensaje=v.validar_horario_reserva(fecha_str,hora_inicio_str,duracion,cantidad_personas)
    return v.convertir_fecha(fecha_str), Resultado(False,mensaje) if mensaje else None


def _hay_superposicion(codigo_sala,fecha_str,hora_inicio,hora_fin,excluir_id=None):
    activas=reservacion_repo.listar_activas_por_sala_fecha(codigo_sala,fecha_str)
    for existente in activas:
        if existente.id==excluir_id:continue
        inicio=v.convertir_hora(existente.hora_inicio)
        fin=v.calcular_hora_fin(existente.hora_inicio,existente.duracion)
        if inicio is not None and fin is not None and hora_inicio<fin and inicio<hora_fin:
            return True
    return False


def _validar_reserva(carne,codigo,fecha,hora,duracion,cantidad,excluir_id=None,
                     validar_limite=True, verificar_estudiante=True):
    if not v.carne_valido(carne):
        return None,None,Resultado(False,"El carné debe tener exactamente diez caracteres alfanuméricos.")
    if not v.texto_no_vacio(codigo):
        return None,None,Resultado(False,"El código de sala es obligatorio.")
    _,error=_validar_datos_basicos(fecha,hora,duracion,cantidad)
    if error:return None,None,error
    estudiante=estudiante_repo.obtener_estudiante(carne.strip())
    if not estudiante:
        return None,None,Resultado(False,f"No existe un estudiante registrado con el carné {carne.strip()}.")
    if verificar_estudiante and not estudiante.activo:
        return None,None,Resultado(False,"El estudiante no se encuentra activo y no puede reservar.")
    sala=sala_repo.obtener_sala(codigo.strip().upper())
    if sala is None:return None,None,Resultado(False,f"No existe una sala con el código {codigo.strip()}.")
    if sala.estado!=ESTADO_DISPONIBLE:
        return None,None,Resultado(False,"La sala se encuentra fuera de servicio y no puede reservarse.")
    if cantidad>sala.capacidad:
        return None,None,Resultado(False,f"La cantidad de personas supera la capacidad de la sala ({sala.capacidad}).")
    hi=v.convertir_hora(hora); hf=v.calcular_hora_fin(hora,duracion)
    if _hay_superposicion(sala.codigo,fecha.strip(),hi,hf,excluir_id):
        return None,None,Resultado(False,"El horario solicitado se cruza con otra reservación activa en esa sala.")
    if validar_limite:
        ahora=datetime.now()
        actual=reservacion_repo.contar_activas_estudiante_desde(estudiante.carne,
                         ahora.date().isoformat(),ahora.strftime("%H:%M:%S"))
        if actual>=MAXIMO_RESERVAS_ACTIVAS_POR_ESTUDIANTE:
            return None,None,Resultado(False,"El estudiante ya tiene el máximo de tres reservaciones activas presentes o futuras.")
    return estudiante,sala,None


def crear_reservacion(carne_estudiante,codigo_sala,fecha_str,hora_inicio_str,duracion,cantidad_personas):
    try:
        estudiante,sala,error=_validar_reserva(carne_estudiante,codigo_sala,fecha_str,hora_inicio_str,duracion,cantidad_personas)
        if error:return error
        nueva=Reservacion("",estudiante.carne,sala.codigo,fecha_str.strip(),hora_inicio_str.strip(),duracion,cantidad_personas)
        reservacion_repo.crear_atomica(nueva)
        return Resultado(True,f"Reservación {nueva.id} creada exitosamente.",nueva)
    except ErrorPersistencia:
        return Resultado(False,"Ocurrió un error al procesar la reservación. No se realizaron cambios.")


def consultar_disponibilidad(codigo_sala,fecha_str,hora_inicio_str,duracion):
    if not v.texto_no_vacio(codigo_sala):return Resultado(False,"El código de sala es obligatorio.")
    _,error=_validar_datos_basicos(fecha_str,hora_inicio_str,duracion,1)
    if error:return error
    try:
        sala=sala_repo.obtener_sala(codigo_sala)
        if not sala:return Resultado(False,"La sala indicada no existe.")
        if sala.estado!=ESTADO_DISPONIBLE:return Resultado(True,"La sala está fuera de servicio; no está disponible.",False)
        conflicto=_hay_superposicion(sala.codigo,fecha_str.strip(),v.convertir_hora(hora_inicio_str),v.calcular_hora_fin(hora_inicio_str,duracion))
        if conflicto:return Resultado(True,"El horario solicitado no está disponible: existe un conflicto.",False)
        return Resultado(True,"El horario solicitado está disponible.",True)
    except ErrorPersistencia:return Resultado(False,"No fue posible consultar la disponibilidad.")


def cancelar_reservacion(id_reservacion):
    if not v.id_reservacion_valido(id_reservacion):return Resultado(False,"El identificador de reservación no tiene un formato válido.")
    try:
        reserva=reservacion_repo.obtener_reservacion(id_reservacion.strip())
        if not reserva:return Resultado(False,f"No existe una reservación con el identificador {id_reservacion}.")
        if reserva.estado==ESTADO_CANCELADA:return Resultado(False,"La reservación ya se encuentra cancelada.")
        reservacion_repo.cancelar_reservacion_bd(reserva.id)
        return Resultado(True,f"Reservación {reserva.id} cancelada. El horario queda disponible.")
    except ErrorPersistencia:return Resultado(False,"No fue posible cancelar la reservación. No se realizaron cambios.")


def consultar_reservaciones():
    try:
        datos=reservacion_repo.listar_reservaciones()
        return Resultado(True,f"Se encontraron {len(datos)} reservaciones.",datos)
    except ErrorPersistencia:return Resultado(False,"No fue posible consultar las reservaciones.")


def buscar_reservaciones_estudiante(carne):
    if not v.carne_valido(carne):return Resultado(False,"El carné debe tener exactamente diez caracteres alfanuméricos.")
    try:
        estudiante=estudiante_repo.obtener_estudiante(carne)
        if not estudiante:return Resultado(False,"No existe un estudiante registrado con ese carné.")
        datos=reservacion_repo.buscar_por_carne(estudiante.carne)
        if not datos:return Resultado(True,"El estudiante existe, pero no tiene reservaciones.",[])
        return Resultado(True,f"Se encontraron {len(datos)} reservaciones.",datos)
    except ErrorPersistencia:return Resultado(False,"No fue posible buscar las reservaciones.")


def modificar_reservacion(id_reservacion,codigo_sala,fecha_str,hora_inicio_str,duracion,cantidad_personas):
    if not v.id_reservacion_valido(id_reservacion):return Resultado(False,"El identificador es inválido.")
    try:
        original=reservacion_repo.obtener_reservacion(id_reservacion)
        if not original:return Resultado(False,"No existe la reservación indicada.")
        if original.estado==ESTADO_CANCELADA:return Resultado(False,"Una reservación cancelada no puede modificarse.")
        estudiante,sala,error=_validar_reserva(original.carne_estudiante,codigo_sala,fecha_str,
            hora_inicio_str,duracion,cantidad_personas,excluir_id=original.id,validar_limite=False)
        if error:return error
        actualizada=Reservacion(original.id,estudiante.carne,sala.codigo,fecha_str.strip(),hora_inicio_str.strip(),
                   duracion,cantidad_personas,original.estado,original.serie_id,original.numero_ocurrencia)
        reservacion_repo.actualizar_reservacion(actualizada)
        return Resultado(True,f"Reservación {original.id} modificada correctamente.",actualizada)
    except ErrorPersistencia:return Resultado(False,"No fue posible modificar la reservación.")


def previsualizar_serie_semanal(carne,codigo,fecha_inicial,hora,duracion,cantidad,ocurrencias):
    """RF-14: lista cada fecha y conflicto, sin modificar la base de datos."""
    if type(ocurrencias) is not int or not 2 <= ocurrencias <= 8:
        return Resultado(False,"La serie debe contener entre 2 y 8 ocurrencias.")
    inicio=v.convertir_fecha(fecha_inicial)
    if inicio is None:
        return Resultado(False,"La fecha inicial debe usar AAAA-MM-DD.")
    try:
        elementos=[]
        for i in range(ocurrencias):
            fecha=(inicio+timedelta(weeks=i)).isoformat()
            _,_,error=_validar_reserva(carne,codigo,fecha,hora,duracion,cantidad,validar_limite=False)
            elementos.append({"numero":i+1,"fecha":fecha,"conflicto":error.mensaje if error else None})
        return Resultado(True,"Previsualización completada, sin guardar cambios.",elementos)
    except ErrorPersistencia:
        return Resultado(False,"No fue posible consultar los conflictos de la serie.")


def crear_serie_semanal(carne,codigo,fecha_inicial,hora,duracion,cantidad,ocurrencias):
    """Todas las ocurrencias cumplen reglas y se guardan juntas o ninguna.

    Política RN-11: cada ocurrencia se contabiliza como una reservación activa.
    Por ello una serie de 4-8 no puede crearse para un mismo estudiante mientras
    persista el máximo de tres activas; debe aclararse con el profesor si desea
    una excepción para series. No se altera la regla oficial silenciosamente.
    """
    if type(ocurrencias) is not int or not 2<=ocurrencias<=8:
        return Resultado(False,"La serie debe contener entre 2 y 8 ocurrencias.")
    inicio=v.convertir_fecha(fecha_inicial)
    if inicio is None:return Resultado(False,"La fecha inicial debe usar AAAA-MM-DD.")
    try:
        fechas=[(inicio+timedelta(weeks=i)).isoformat() for i in range(ocurrencias)]
        revisadas=[]; conflictos=[]
        for f in fechas:
            estudiante,sala,error=_validar_reserva(carne,codigo,f,hora,duracion,cantidad,validar_limite=False)
            if error:conflictos.append(f"{f}: {error.mensaje}")
            else:revisadas.append(Reservacion("",estudiante.carne,sala.codigo,f,hora.strip(),duracion,cantidad))
        if conflictos:
            return Resultado(False,"La serie contiene conflictos o datos inválidos: "+"; ".join(conflictos),conflictos)
        ahora=datetime.now()
        n=reservacion_repo.contar_activas_estudiante_desde(estudiante.carne,ahora.date().isoformat(),ahora.strftime("%H:%M:%S"))
        if n+ocurrencias>MAXIMO_RESERVAS_ACTIVAS_POR_ESTUDIANTE:
            return Resultado(False,"La serie supera el máximo de tres reservaciones activas presentes o futuras.")
        creadas=reservacion_repo.crear_serie_atomica(revisadas)
        return Resultado(True,f"Serie {creadas[0].serie_id} creada con {len(creadas)} ocurrencias.",creadas)
    except ErrorPersistencia:return Resultado(False,"No fue posible guardar la serie; no se realizaron cambios parciales.")


def cancelar_ocurrencias_futuras(identificador):
    try:
        r=reservacion_repo.obtener_reservacion(identificador)
        if not r or not r.serie_id:return Resultado(False,"La reservación no pertenece a una serie existente.")
        cantidad=reservacion_repo.cancelar_ocurrencias_futuras_serie(r.serie_id,r.fecha)
        if cantidad==0:return Resultado(False,"No existen ocurrencias futuras activas que cancelar.")
        return Resultado(True,f"Se cancelaron {cantidad} ocurrencias desde {r.fecha}.",cantidad)
    except ErrorPersistencia:return Resultado(False,"No fue posible cancelar las ocurrencias de la serie.")
