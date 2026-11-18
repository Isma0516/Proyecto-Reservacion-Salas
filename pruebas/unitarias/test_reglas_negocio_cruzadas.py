"""
Pruebas unitarias cruzadas - Fase 5, Parte 2: reglas de negocio RN-01 a RN-12.

Equipo evaluador. Cada prueba corresponde a un caso del Plan de pruebas (Fase 4,
sección 3 de la Parte II, 37 casos) y lleva su identificador en el nombre (test_CP_RNxx_yy_...).

- No modifica el código productivo: solo invoca solucion.negocio.reservaciones.
- Usa una base SQLite temporal por prueba (conexion.configurar_ruta_bd), sembrada
  con los datos iniciales del sistema.
- Los casos que dependen de la hora actual fijan el reloj con unittest.mock.patch.

Ejecución desde la raíz del repositorio:
    python -m unittest pruebas.unitarias.test_reglas_negocio_cruzadas -v
"""
import os
import tempfile
import unittest
from contextlib import ExitStack
from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from solucion.datos import conexion, datos_iniciales, estudiante_repo, reservacion_repo
from solucion.modelos.reservacion import Reservacion
from solucion.negocio import reservaciones

ANDREA = "A001234567"    # activa
CARLOS = "B009876543"    # activo
DANIELA = "C004567890"   # inactiva


def dia(n):
    """Fecha AAAA-MM-DD relativa a hoy (D+n)."""
    return (date.today() + timedelta(days=n)).isoformat()


def reloj(hora, minuto=0):
    """Fija la fecha y hora del sistema que ve el módulo de reservaciones."""
    momento = datetime.combine(date.today(), time(hora, minuto))

    class FechaFija(date):
        @classmethod
        def today(cls):
            return momento.date()

    class FechaHoraFija(datetime):
        @classmethod
        def now(cls, tz=None):
            return momento

    # Desde la Fase 6 la hora actual también se consulta en validaciones y en el
    # repositorio de reservaciones, por lo que el reloj se fija en los tres módulos.
    pila = ExitStack()
    for modulo in ("solucion.negocio.reservaciones", "solucion.negocio.validaciones",
                   "solucion.datos.reservacion_repo"):
        pila.enter_context(patch.multiple(modulo, date=FechaFija, datetime=FechaHoraFija))
    return pila


class BaseReglas(unittest.TestCase):
    """PB: BD temporal con los datos iniciales y sin reservaciones."""

    def setUp(self):
        archivo = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        archivo.close()
        self.ruta_bd = archivo.name
        conexion.configurar_ruta_bd(self.ruta_bd)
        conexion.inicializar_bd()
        datos_iniciales.sembrar_datos_iniciales()

    def tearDown(self):
        os.unlink(self.ruta_bd)

    # --- utilidades -------------------------------------------------------
    def crear(self, carne=ANDREA, sala="S01", fecha=None, hora="10:00", duracion=1, personas=2):
        return reservaciones.crear_reservacion(carne, sala, fecha or dia(1), hora, duracion, personas)

    def total(self):
        return len(reservacion_repo.listar_reservaciones())

    def insertar(self, id_, carne, sala, fecha, hora, duracion=1, estado="activa"):
        """Preparación directa de datos (por ejemplo, reservas en el pasado)."""
        reservacion_repo.insertar_reservacion(
            Reservacion(id_, carne, sala, fecha, hora, duracion, 2, estado=estado))

    def assertAceptada(self, resultado):
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(resultado.datos.estado, "activa")

    def assertRechazada(self, resultado, palabra_clave, total_previo=0):
        self.assertFalse(resultado.exito, "Se esperaba rechazo, pero se aceptó: " + resultado.mensaje)
        self.assertIn(palabra_clave.lower(), resultado.mensaje.lower())
        self.assertEqual(self.total(), total_previo, "Se guardó un registro pese al rechazo")


# ===========================================================================
class RN01EstudianteActivo(BaseReglas):
    def test_CP_RN01_01_estudiante_activo(self):
        r = self.crear()
        self.assertAceptada(r)
        self.assertEqual(r.datos.id, "R0001")

    def test_CP_RN01_02_estudiante_inactivo(self):
        self.assertRechazada(self.crear(carne=DANIELA), "activo")

    def test_CP_RN01_03_estudiante_no_registrado(self):
        self.assertRechazada(self.crear(carne="Z999999999"), "no existe")

    def test_CP_RN01_04_carne_activo_en_minusculas(self):
        """Sección 5.1: la comparación del carné no distingue mayúsculas (H-RN-06)."""
        self.assertAceptada(self.crear(carne="a001234567"))


class RN02Fecha(BaseReglas):
    def test_CP_RN02_01_fecha_actual_con_hora_futura(self):
        with reloj(9, 30):
            self.assertAceptada(self.crear(fecha=dia(0), hora="10:00"))

    def test_CP_RN02_02_fecha_pasada(self):
        self.assertRechazada(self.crear(fecha=dia(-1)), "pasada")

    def test_CP_RN02_03_fecha_inexistente(self):
        self.assertRechazada(self.crear(fecha="2027-02-30"), "formato")

    def test_CP_RN02_04_fecha_sin_ceros(self):
        """RN-02 exige AAAA-MM-DD; '2027-1-5' no cumple el formato (H-RN-04)."""
        self.assertRechazada(self.crear(fecha="2027-1-5"), "formato")


class RN03HoraActual(BaseReglas):
    def test_CP_RN03_01_hoy_siguiente_hora(self):
        with reloj(14, 30):
            self.assertAceptada(self.crear(fecha=dia(0), hora="15:00"))

    def test_CP_RN03_02_hoy_hora_pasada(self):
        with reloj(14, 30):
            self.assertRechazada(self.crear(fecha=dia(0), hora="14:00"), "posterior a la hora actual")


class RN04HoraCompleta(BaseReglas):
    def test_CP_RN04_01_un_minuto_despues(self):
        self.assertRechazada(self.crear(hora="10:01"), "hora completa")

    def test_CP_RN04_02_hora_sin_cero_inicial(self):
        """RN-04 y la sección 5.3 exigen HH:MM; '9:00' no cumple el formato (H-RN-04)."""
        self.assertRechazada(self.crear(hora="9:00"), "hora")


class RN05Horario(BaseReglas):
    def test_CP_RN05_01_inicio_0800(self):
        self.assertAceptada(self.crear(hora="08:00"))

    def test_CP_RN05_02_inicio_0700(self):
        self.assertRechazada(self.crear(hora="07:00"), "08:00")

    def test_CP_RN05_03_termina_exactamente_2000(self):
        self.assertAceptada(self.crear(hora="19:00", duracion=1))

    def test_CP_RN05_04_termina_2100(self):
        self.assertRechazada(self.crear(hora="19:00", duracion=2), "20:00")


class RN06Duracion(BaseReglas):
    def test_CP_RN06_01_una_hora(self):
        self.assertAceptada(self.crear(duracion=1))

    def test_CP_RN06_02_dos_horas(self):
        self.assertAceptada(self.crear(duracion=2))

    def test_CP_RN06_03_duracion_0_y_3(self):
        for duracion in (0, 3):
            with self.subTest(duracion=duracion):
                self.assertRechazada(self.crear(duracion=duracion), "una o dos horas")


class RN07Capacidad(BaseReglas):
    def test_CP_RN07_01_capacidad_exacta(self):
        self.assertAceptada(self.crear(sala="S01", personas=4))

    def test_CP_RN07_02_una_persona(self):
        self.assertAceptada(self.crear(sala="S05", personas=1))

    def test_CP_RN07_03_capacidad_excedida(self):
        self.assertRechazada(self.crear(sala="S01", personas=5), "capacidad")

    def test_CP_RN07_04_cantidad_cero_y_negativa(self):
        for cantidad in (0, -1):
            with self.subTest(cantidad=cantidad):
                self.assertRechazada(self.crear(personas=cantidad), "mayor que cero")

    def test_CP_RN07_05_cantidad_decimal(self):
        self.assertRechazada(self.crear(personas=2.5), "entero")


class RN08Sala(BaseReglas):
    def test_CP_RN08_01_sala_fuera_de_servicio(self):
        self.assertRechazada(self.crear(sala="S04"), "fuera de servicio")

    def test_CP_RN08_02_sala_inexistente(self):
        self.assertRechazada(self.crear(sala="S99"), "no existe una sala")


class RN09Superposicion(BaseReglas):
    def preparar(self, hora, duracion, fecha=None):
        r = self.crear(carne=CARLOS, sala="S03", fecha=fecha or dia(2), hora=hora, duracion=duracion)
        self.assertTrue(r.exito, r.mensaje)

    def test_CP_RN09_01_conflicto_total(self):
        self.preparar("10:00", 1)
        self.assertRechazada(self.crear(sala="S03", fecha=dia(2), hora="10:00", duracion=1), "se cruza", 1)

    def test_CP_RN09_02_conflicto_parcial(self):
        self.preparar("10:00", 2)
        self.assertRechazada(self.crear(sala="S03", fecha=dia(2), hora="11:00", duracion=1), "se cruza", 1)

    def test_CP_RN09_03_reserva_envolvente(self):
        self.preparar("10:00", 1)
        self.assertRechazada(self.crear(sala="S03", fecha=dia(2), hora="09:00", duracion=2), "se cruza", 1)

    def test_CP_RN09_04_misma_fecha_en_otro_formato(self):
        """No deben coexistir dos reservas activas en S03 el 2027-01-05 a las 10:00 (H-RN-05)."""
        self.preparar("10:00", 1, fecha="2027-01-05")
        r = self.crear(sala="S03", fecha="2027-1-5", hora="10:00", duracion=1)
        activas = [x for x in reservacion_repo.listar_reservaciones()
                   if x.codigo_sala == "S03" and x.hora_inicio == "10:00" and x.estado == "activa"]
        self.assertFalse(r.exito, "Se aceptó una segunda reserva en el mismo horario: " + r.mensaje)
        self.assertEqual(len(activas), 1)


class RN10Consecutivas(BaseReglas):
    def test_CP_RN10_01_inicia_cuando_termina_la_anterior(self):
        self.crear(carne=CARLOS, sala="S03", fecha=dia(2), hora="10:00", duracion=1)
        self.assertAceptada(self.crear(sala="S03", fecha=dia(2), hora="11:00"))


class RN11Limite(BaseReglas):
    def tres_reservas(self):
        return [self.crear(fecha=dia(n)) for n in (1, 2, 3)]

    def test_CP_RN11_01_tercera_reserva(self):
        self.crear(fecha=dia(1))
        self.crear(fecha=dia(2))
        self.assertAceptada(self.crear(fecha=dia(3)))

    def test_CP_RN11_02_cuarta_reserva(self):
        self.tres_reservas()
        self.assertRechazada(self.crear(fecha=dia(4)), "máximo", 3)

    def test_CP_RN11_03_nueva_tras_cancelar_una(self):
        primeras = self.tres_reservas()
        self.assertTrue(reservaciones.cancelar_reservacion(primeras[0].datos.id).exito)
        self.assertAceptada(self.crear(fecha=dia(4)))

    def test_CP_RN11_04_reserva_de_hoy_ya_terminada_no_cuenta(self):
        """Criterio a confirmar (H-RN-03): 'presente' significa que la reserva aún no ha terminado."""
        self.insertar("R0001", ANDREA, "S01", dia(0), "08:00")
        with reloj(14, 30):
            self.assertTrue(self.crear(fecha=dia(1)).exito)
            self.assertTrue(self.crear(fecha=dia(2)).exito)
            self.assertAceptada(self.crear(fecha=dia(3)))


class RN12Canceladas(BaseReglas):
    def test_CP_RN12_01_cancelada_permanece_en_historial(self):
        creada = self.crear()
        self.assertTrue(reservaciones.cancelar_reservacion(creada.datos.id).exito)
        historial = reservacion_repo.listar_reservaciones()
        self.assertEqual(len(historial), 1)
        self.assertEqual(historial[0].id, "R0001")
        self.assertEqual(historial[0].estado, "cancelada")
        self.assertEqual((historial[0].codigo_sala, historial[0].hora_inicio), ("S01", "10:00"))

    def test_CP_RN12_02_cancelada_libera_el_horario(self):
        creada = self.crear()
        reservaciones.cancelar_reservacion(creada.datos.id)
        r = self.crear(carne=CARLOS)
        self.assertAceptada(r)
        self.assertEqual(r.datos.id, "R0002")


if __name__ == "__main__":
    unittest.main()
