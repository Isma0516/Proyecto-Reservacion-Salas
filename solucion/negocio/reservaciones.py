"""
Reglas de negocio para reservaciones: RF-05 (crear), RF-08 (disponibilidad)
y RF-09 (cancelar). Aplica las reglas de negocio RN-01 a RN-13 descritas
en la especificación.
"""
from datetime import date, datetime, time

from solucion.datos import estudiante_repo, reservacion_repo, sala_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.reservacion import Reservacion, ESTADO_CANCELADA
from solucion.modelos.resultado import Resultado
from solucion.modelos.sala import ESTADO_DISPONIBLE
from solucion.negocio import validaciones

MAXIMO_RESERVAS_ACTIVAS_POR_ESTUDIANTE = 3  # RN-11


def _validar_datos_basicos(fecha_str: str, hora_inicio_str: str, duracion: int, cantidad_personas: int):
    """Valida formato/reglas que no dependen de consultar la base de datos."""
    fecha = validaciones.convertir_fecha(fecha_str)
    if fecha is None:
        return None, Resultado(False, "La fecha ingresada no tiene un formato válido (use AAAA-MM-DD).")

    if not validaciones.hora_valida_en_punto(hora_inicio_str):
        return None, Resultado(False, "La hora de inicio debe ser una hora completa (por ejemplo, 14:00).")

    if not validaciones.duracion_valida(duracion):
        return None, Resultado(False, "La duración de la reservación debe ser de una o dos horas.")

    if not validaciones.cantidad_personas_valida(cantidad_personas):
        return None, Resultado(False, "La cantidad de personas debe ser un número entero mayor que cero.")

    if not validaciones.inicia_dentro_del_horario(hora_inicio_str):
        return None, Resultado(False, "La reservación debe iniciar a las 08:00 o después.")

    if not validaciones.finaliza_dentro_del_horario(hora_inicio_str, duracion):
        return None, Resultado(False, "La reservación debe finalizar como máximo a las 20:00.")

    hoy = date.today()
    if fecha < hoy:
        return None, Resultado(False, "No se pueden crear ni consultar reservaciones en una fecha pasada.")

    hora_inicio = validaciones.convertir_hora(hora_inicio_str)
    if fecha == hoy and hora_inicio <= datetime.now().time():
        return None, Resultado(False, "Para el día de hoy, la hora de inicio debe ser posterior a la hora actual.")

    return fecha, None


def _hay_superposicion(codigo_sala: str, fecha_str: str, hora_inicio: time, hora_fin: time,
                        excluir_id: str = None) -> bool:
    """RN-09/RN-10: dos reservas activas se cruzan salvo que una empiece justo cuando termina la otra."""
    activas = reservacion_repo.listar_activas_por_sala_fecha(codigo_sala, fecha_str)
    for existente in activas:
        if excluir_id is not None and existente.id == excluir_id:
            continue
        inicio_existente = validaciones.convertir_hora(existente.hora_inicio)
        if inicio_existente is None:
            continue
        fin_existente = validaciones.calcular_hora_fin(existente.hora_inicio, existente.duracion)
        if fin_existente is None:
            continue
        if hora_inicio < fin_existente and inicio_existente < hora_fin:
            return True
    return False


def crear_reservacion(carne_estudiante: str, codigo_sala: str, fecha_str: str,
                       hora_inicio_str: str, duracion: int, cantidad_personas: int) -> Resultado:
    """RF-05: crea una reservación únicamente si cumple todas las reglas de negocio."""
    if not validaciones.carne_valido(carne_estudiante):
        return Resultado(False, "El carné debe tener exactamente diez caracteres alfanuméricos.")
    if not validaciones.texto_no_vacio(codigo_sala):
        return Resultado(False, "El código de sala es obligatorio.")

    fecha, error = _validar_datos_basicos(fecha_str, hora_inicio_str, duracion, cantidad_personas)
    if error is not None:
        return error

    carne_estudiante = carne_estudiante.strip()
    codigo_sala = codigo_sala.strip()
    fecha_str = fecha_str.strip()
    hora_inicio_str = hora_inicio_str.strip()

    try:
        estudiante = estudiante_repo.obtener_estudiante(carne_estudiante)
        if estudiante is None:
            return Resultado(False, f"No existe un estudiante registrado con el carné {carne_estudiante}.")
        if not estudiante.activo:
            return Resultado(False, "El estudiante no se encuentra activo y no puede reservar.")

        sala = sala_repo.obtener_sala(codigo_sala)
        if sala is None:
            return Resultado(False, f"No existe una sala con el código {codigo_sala}.")
        if sala.estado != ESTADO_DISPONIBLE:
            return Resultado(False, "La sala se encuentra fuera de servicio y no puede reservarse.")
        if cantidad_personas > sala.capacidad:
            return Resultado(False, f"La cantidad de personas supera la capacidad de la sala ({sala.capacidad}).")

        hora_inicio = validaciones.convertir_hora(hora_inicio_str)
        hora_fin = validaciones.calcular_hora_fin(hora_inicio_str, duracion)
        if _hay_superposicion(codigo_sala, fecha_str, hora_inicio, hora_fin):
            return Resultado(False, "El horario solicitado se cruza con otra reservación activa en esa sala.")

        hoy = date.today()
        reservas_activas = reservacion_repo.contar_activas_estudiante_desde(
            carne_estudiante,
            hoy.isoformat(),
        )
        if reservas_activas >= MAXIMO_RESERVAS_ACTIVAS_POR_ESTUDIANTE:
            return Resultado(
                False,
                "El estudiante ya tiene el máximo de tres reservaciones activas presentes o futuras.",
            )

        nuevo_id = reservacion_repo.generar_siguiente_id()
        nueva_reservacion = Reservacion(
            id=nuevo_id,
            carne_estudiante=carne_estudiante,
            codigo_sala=codigo_sala,
            fecha=fecha_str,
            hora_inicio=hora_inicio_str,
            duracion=duracion,
            cantidad_personas=cantidad_personas,
        )
        reservacion_repo.insertar_reservacion(nueva_reservacion)
    except ErrorPersistencia:
        return Resultado(False, "Ocurrió un error al procesar la reservación. No se realizaron cambios.")

    return Resultado(True, f"Reservación {nuevo_id} creada exitosamente.", nueva_reservacion)


def consultar_disponibilidad(codigo_sala: str, fecha_str: str, hora_inicio_str: str, duracion: int) -> Resultado:
    """
    RF-08: determina si una sala puede utilizarse en una fecha/hora/duración
    dadas, sin crear una reservación. `Resultado.datos` es True/False.
    """
    if not validaciones.texto_no_vacio(codigo_sala):
        return Resultado(False, "El código de sala es obligatorio.")

    fecha, error = _validar_datos_basicos(fecha_str, hora_inicio_str, duracion, cantidad_personas=1)
    if error is not None:
        return error

    codigo_sala = codigo_sala.strip()
    fecha_str = fecha_str.strip()
    hora_inicio_str = hora_inicio_str.strip()

    try:
        sala = sala_repo.obtener_sala(codigo_sala)
        if sala is None:
            return Resultado(False, f"No existe una sala con el código {codigo_sala}.")
        if sala.estado != ESTADO_DISPONIBLE:
            return Resultado(True, "La sala está fuera de servicio; no está disponible para reservar.", False)

        hora_inicio = validaciones.convertir_hora(hora_inicio_str)
        hora_fin = validaciones.calcular_hora_fin(hora_inicio_str, duracion)
        if _hay_superposicion(codigo_sala, fecha_str, hora_inicio, hora_fin):
            return Resultado(True, "El horario solicitado no está disponible: se cruza con otra reservación.", False)
    except ErrorPersistencia:
        return Resultado(False, "No fue posible consultar la disponibilidad en este momento.")

    return Resultado(True, "El horario solicitado está disponible.", True)


def cancelar_reservacion(id_reservacion: str) -> Resultado:
    """RF-09/RN-12: cancela una reserva activa; permanece en el historial y libera el horario."""
    if not validaciones.id_reservacion_valido(id_reservacion):
        return Resultado(False, "El identificador de reservación no tiene un formato válido.")

    id_reservacion = id_reservacion.strip()

    try:
        reservacion = reservacion_repo.obtener_reservacion(id_reservacion)
        if reservacion is None:
            return Resultado(False, f"No existe una reservación con el identificador {id_reservacion}.")
        if reservacion.estado == ESTADO_CANCELADA:
            return Resultado(False, "La reservación ya se encuentra cancelada.")

        reservacion_repo.cancelar_reservacion_bd(id_reservacion)
    except ErrorPersistencia:
        return Resultado(False, "Ocurrió un error al cancelar la reservación. No se realizaron cambios.")

    return Resultado(True, f"Reservación {id_reservacion} cancelada. El horario queda disponible.")
    
