"""Validaciones de formato y reglas de negocio (RF-02, RN-02 a RN-07)."""
import re
from datetime import date, datetime, time, timedelta

PATRON_CARNE = re.compile(r"^[A-Za-z0-9]{10}$")
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_FECHA = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
PATRON_HORA = re.compile(r"^[0-9]{2}:[0-9]{2}$")
PATRON_ID_RESERVACION = re.compile(r"^R[0-9]{4,}$")


def texto_no_vacio(valor):
    return isinstance(valor, str) and bool(valor.strip())


def carne_valido(carne):
    return isinstance(carne, str) and bool(PATRON_CARNE.fullmatch(carne.strip()))


def nombre_valido(nombre):
    return isinstance(nombre, str) and sum(not c.isspace() for c in nombre.strip()) >= 3


def correo_valido(correo):
    return isinstance(correo, str) and bool(PATRON_CORREO.fullmatch(correo.strip()))


def id_reservacion_valido(identificador):
    return isinstance(identificador, str) and bool(PATRON_ID_RESERVACION.fullmatch(identificador.strip()))


def convertir_fecha(valor):
    if not isinstance(valor, str) or not PATRON_FECHA.fullmatch(valor.strip()):
        return None
    try:
        return datetime.strptime(valor.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def convertir_hora(valor):
    if not isinstance(valor, str) or not PATRON_HORA.fullmatch(valor.strip()):
        return None
    try:
        return datetime.strptime(valor.strip(), "%H:%M").time()
    except ValueError:
        return None


def hora_valida_en_punto(valor):
    hora = convertir_hora(valor)
    return hora is not None and hora.minute == 0


def duracion_valida(valor):
    return type(valor) is int and valor in (1, 2)


def cantidad_personas_valida(valor):
    return type(valor) is int and valor > 0


def calcular_hora_fin(hora_inicio, duracion):
    inicio = convertir_hora(hora_inicio)
    if inicio is None or not duracion_valida(duracion):
        return None
    return (datetime.combine(date.today(), inicio) + timedelta(hours=duracion)).time()


def inicia_dentro_del_horario(hora):
    inicio = convertir_hora(hora)
    return inicio is not None and inicio >= time(8, 0)



def finaliza_dentro_del_horario(hora, duracion):
    """Verifica que la reserva finalice como máximo a las 20:00."""
    inicio = convertir_hora(hora)

    if inicio is None or not duracion_valida(duracion):
        return False

    fecha_actual = date.today()
    fecha_hora_inicio = datetime.combine(fecha_actual, inicio)
    fecha_hora_fin = fecha_hora_inicio + timedelta(hours=duracion)
    fecha_hora_limite = datetime.combine(fecha_actual, time(20, 0))

    return fecha_hora_fin <= fecha_hora_limite

def validar_horario_reserva(fecha_str, hora_str, duracion, cantidad, ahora=None):
    """Valida entrada común antes de consultar o modificar la BD.

    Devuelve el mensaje de error o None. `ahora` facilita pruebas deterministas.
    """
    ahora = ahora or datetime.now()
    fecha = convertir_fecha(fecha_str)
    if fecha is None:
        return "La fecha ingresada no tiene un formato válido (use AAAA-MM-DD)."
    if not hora_valida_en_punto(hora_str):
        return "La hora de inicio debe ser una hora completa con formato HH:MM (por ejemplo, 14:00)."
    if not duracion_valida(duracion):
        return "La duración de la reservación debe ser de una o dos horas."
    if not cantidad_personas_valida(cantidad):
        return "La cantidad de personas debe ser un número entero mayor que cero."
    if not inicia_dentro_del_horario(hora_str):
        return "La reservación debe iniciar a las 08:00 o después."
    if not finaliza_dentro_del_horario(hora_str, duracion):
        return "La reservación debe finalizar como máximo a las 20:00."
    if fecha < ahora.date():
        return "No se pueden crear ni consultar reservaciones en una fecha pasada."
    if fecha == ahora.date() and convertir_hora(hora_str) <= ahora.time():
        return "Para el día de hoy, la hora de inicio debe ser posterior a la hora actual."
    return None
