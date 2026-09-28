"""Pruebas de regresión para las reglas críticas de reservación."""

import os
import tempfile
import unittest
from datetime import date, timedelta

from solucion.datos import conexion, estudiante_repo, reservacion_repo, sala_repo
from solucion.modelos.estudiante import Estudiante
from solucion.modelos.reservacion import Reservacion
from solucion.modelos.sala import Sala
from solucion.negocio import reservaciones


class PruebasReglasReservacion(unittest.TestCase):
    def setUp(self):
        archivo = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.ruta_bd = archivo.name
        archivo.close()
        conexion.configurar_ruta_bd(self.ruta_bd)
        conexion.inicializar_bd()

        estudiante_repo.insertar_estudiante(
            Estudiante("EST0000001", "Estudiante Activo", "activo@ejemplo.com")
        )
        estudiante_repo.insertar_estudiante(
            Estudiante("EST0000002", "Estudiante Inactivo", "inactivo@ejemplo.com", False)
        )
        sala_repo.insertar_sala(Sala("S01", "Sala pequeña", 4, "disponible"))
        sala_repo.insertar_sala(Sala("S02", "Sala cerrada", 8, "fuera_servicio"))
        self.manana = (date.today() + timedelta(days=1)).isoformat()

    def tearDown(self):
        os.unlink(self.ruta_bd)

    def crear(self, hora="10:00", duracion=1, personas=2, carne="EST0000001", sala="S01"):
        return reservaciones.crear_reservacion(
            carne, sala, self.manana, hora, duracion, personas
        )

    def test_rechaza_estudiante_inactivo(self):
        self.assertFalse(self.crear(carne="EST0000002").exito)

    def test_rechaza_sala_fuera_de_servicio(self):
        self.assertFalse(self.crear(sala="S02").exito)

    def test_rechaza_cantidad_mayor_que_capacidad(self):
        self.assertFalse(self.crear(personas=5).exito)

    def test_rechaza_superposicion_parcial(self):
        self.assertTrue(self.crear(hora="10:00", duracion=2).exito)
        self.assertFalse(self.crear(hora="11:00", duracion=1).exito)

    def test_permite_reservas_consecutivas(self):
        self.assertTrue(self.crear(hora="10:00", duracion=1).exito)
        self.assertTrue(self.crear(hora="11:00", duracion=1).exito)

    def test_rechaza_cuarta_reserva_activa(self):
        for hora in ("08:00", "10:00", "12:00"):
            self.assertTrue(self.crear(hora=hora).exito)
        self.assertFalse(self.crear(hora="14:00").exito)

    def test_cancelar_libera_horario_y_conserva_historial(self):
        creada = self.crear()
        self.assertTrue(creada.exito)
        self.assertTrue(reservaciones.cancelar_reservacion(creada.datos.id).exito)
        self.assertTrue(self.crear().exito)

        historial = reservacion_repo.listar_reservaciones()
        self.assertEqual(len(historial), 2)
        self.assertEqual(historial[0].estado, "cancelada")

    def test_identificador_no_se_reutiliza_despues_de_cancelar(self):
        primera = self.crear()
        self.assertEqual(primera.datos.id, "R0001")
        self.assertTrue(reservaciones.cancelar_reservacion("R0001").exito)
        segunda = self.crear(hora="12:00")
        self.assertEqual(segunda.datos.id, "R0002")

    def test_disponibilidad_no_crea_reservacion(self):
        resultado = reservaciones.consultar_disponibilidad(
            "S01", self.manana, "10:00", 1
        )
        self.assertTrue(resultado.exito)
        self.assertTrue(resultado.datos)
        self.assertEqual(reservacion_repo.listar_reservaciones(), [])

    def test_reserva_cancelada_no_bloquea_el_horario(self):
        reservacion_repo.insertar_reservacion(
            Reservacion(
                "R0001",
                "EST0000001",
                "S01",
                self.manana,
                "10:00",
                1,
                2,
                estado="cancelada",
            )
        )
        self.assertTrue(self.crear().exito)


if __name__ == "__main__":
    unittest.main()
