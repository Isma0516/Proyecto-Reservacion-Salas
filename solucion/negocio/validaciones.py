"""Funciones de validación reutilizables para la capa de negocio."""
import re
from datetime import date, datetime, time, timedelta
from typing import Optional

PATRON_CARNE = re.compile(r"^[A-Za-z0-9]{10}$")
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PATRON_ID_RESERVACION = re.compile(r"^R\d{4,}$")

HORA_LIMITE_FIN = time(20, 0)  # RN-05


def texto_no_vacio(valor) -> bool:
    """Checks that a value is a non-empty string after trimming whitespace."""
    return isinstance(valor, str) and bool(valor.strip())


def carne_valido(carne) -> bool:
    """RF-02: el carné debe tener exactamente diez caracteres alfanuméricos."""
    return isinstance(carne, str) and bool(PATRON_CARNE.fullmatch(carne.strip()))


def correo_valido(correo) -> bool:
    """Checks a basic e-mail structure without accepting non-string values."""
    return isinstance(correo, str) and bool(PATRON_CORREO.fullmatch(correo.strip()))


def id_reservacion_valido(id_reservacion) -> bool:
    """RN-13: checks the public reservation identifier format (R0001, R0002, ...)."""
    return isinstance(id_reservacion, str) and bool(
        PATRON_ID_RESERVACION.fullmatch(id_reservacion.strip())
    )


def convertir_fecha(fecha_str) -> Optional[date]:
    """Converts AAAA-MM-DD to date; returns None instead of raising on invalid input."""
    if not isinstance(fecha_str, str):
        return None
    try:
        return datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def convertir_hora(hora_str) -> Optional[time]:
    """Converts HH:MM to time; returns None instead of raising on invalid input."""
    if not isinstance(hora_str, str):
        return None
    try:
        return datetime.strptime(hora_str.strip(), "%H:%M").time()
    except ValueError:
        return None


def hora_valida_en_punto(hora_str) -> bool:
    """RN-04: la reservación debe iniciar en una hora completa (HH:00)."""
    hora = convertir_hora(hora_str)
    return hora is not None and hora.minute == 0


def duracion_valida(duracion) -> bool:
    """RN-06: only integer durations of one or two hours are valid."""
    return isinstance(duracion, int) and not isinstance(duracion, bool) and duracion in (1, 2)


def cantidad_personas_valida(cantidad_personas) -> bool:
    """RN-07: the amount must be an integer greater than zero."""
    return (
        isinstance(cantidad_personas, int)
        and not isinstance(cantidad_personas, bool)
        and cantidad_personas > 0
    )


def calcular_hora_fin(hora_inicio_str: str, duracion: int) -> Optional[time]:
    """Calculates the ending time without propagating invalid-input exceptions."""
    hora_inicio = convertir_hora(hora_inicio_str)
    if hora_inicio is None or not duracion_valida(duracion):
        return None
    inicio = datetime.combine(date.today(), hora_inicio)
    return (inicio + timedelta(hours=duracion)).time()


def finaliza_dentro_del_horario(hora_inicio_str: str, duracion: int) -> bool:
    """RN-05: verifies that the reservation ends no later than 20:00 on the same day."""
    hora_inicio = convertir_hora(hora_inicio_str)
    if hora_inicio is None or not duracion_valida(duracion):
        return False

    inicio = datetime.combine(date.today(), hora_inicio)
    fin = inicio + timedelta(hours=duracion)
    limite = datetime.combine(date.today(), HORA_LIMITE_FIN)
    return fin <= limite
