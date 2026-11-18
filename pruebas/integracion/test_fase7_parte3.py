"""Fase 7 - Parte 3: integración de reservaciones, cancelaciones y SQLite."""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from solucion.datos import conexion, reservacion_repo, auditoria_repo
from solucion.negocio import reservaciones


class TestFase7Parte3Integracion(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self.temp.name) / "fase7_parte3.db"
        conexion.configurar_ruta_bd(str(self.ruta))
        conexion.preparar_bd()
        self.fecha = (date.today() + timedelta(days=10)).isoformat()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.temp.cleanup()

    def crear(self, carne="A001234567", sala="S01", hora="10:00", duracion=1, personas=2):
        return reservaciones.crear_reservacion(
            carne, sala, self.fecha, hora, duracion, personas
        )

    def test_INT_P3_01_creacion_se_persiste_en_sqlite(self):
        resultado = self.crear()
        self.assertTrue(resultado.exito, resultado.mensaje)

        guardada = reservacion_repo.obtener_reservacion(resultado.datos.id)
        self.assertIsNotNone(guardada)
        self.assertEqual(guardada.id, resultado.datos.id)
        self.assertEqual(guardada.carne_estudiante, "A001234567")
        self.assertEqual(guardada.codigo_sala, "S01")
        self.assertEqual(guardada.fecha, self.fecha)
        self.assertEqual(guardada.hora_inicio, "10:00")
        self.assertEqual(guardada.estado, "activa")

    def test_INT_P3_02_modificacion_se_persiste_y_conserva_id(self):
        creada = self.crear()
        self.assertTrue(creada.exito, creada.mensaje)
        identificador = creada.datos.id

        cambio = reservaciones.modificar_reservacion(
            identificador, "S02", self.fecha, "12:00", 1, 3
        )
        self.assertTrue(cambio.exito, cambio.mensaje)

        guardada = reservacion_repo.obtener_reservacion(identificador)
        self.assertEqual(guardada.id, identificador)
        self.assertEqual(guardada.codigo_sala, "S02")
        self.assertEqual(guardada.hora_inicio, "12:00")
        self.assertEqual(guardada.cantidad_personas, 3)

    def test_INT_P3_03_cancelacion_conserva_historial_y_libera_horario(self):
        creada = self.crear()
        self.assertTrue(creada.exito, creada.mensaje)
        identificador = creada.datos.id

        cancelada = reservaciones.cancelar_reservacion(identificador)
        self.assertTrue(cancelada.exito, cancelada.mensaje)

        historica = reservacion_repo.obtener_reservacion(identificador)
        self.assertIsNotNone(historica)
        self.assertEqual(historica.estado, "cancelada")

        disponible = reservaciones.consultar_disponibilidad("S01", self.fecha, "10:00", 1)
        self.assertTrue(disponible.exito, disponible.mensaje)
        self.assertTrue(disponible.datos)

        nueva = self.crear(carne="B009876543")
        self.assertTrue(nueva.exito, nueva.mensaje)
        self.assertNotEqual(nueva.datos.id, identificador)

    def test_INT_P3_04_modificacion_rechazada_no_altera_sqlite(self):
        primera = self.crear(hora="10:00")
        segunda = self.crear(carne="B009876543", hora="12:00")
        self.assertTrue(primera.exito)
        self.assertTrue(segunda.exito)

        identificador = segunda.datos.id
        antes = reservacion_repo.obtener_reservacion(identificador)
        auditoria_antes = list(auditoria_repo.listar("reservacion", identificador))

        rechazo = reservaciones.modificar_reservacion(
            identificador, "S01", self.fecha, "10:00", 1, 2
        )
        self.assertFalse(rechazo.exito)

        despues = reservacion_repo.obtener_reservacion(identificador)
        auditoria_despues = list(auditoria_repo.listar("reservacion", identificador))

        self.assertEqual(despues, antes)
        self.assertEqual(auditoria_despues, auditoria_antes)


class TestFase7Parte3Regresion(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self.temp.name) / "fase7_parte3_reg.db"
        conexion.configurar_ruta_bd(str(self.ruta))
        conexion.preparar_bd()
        self.fecha = (date.today() + timedelta(days=15)).isoformat()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.temp.cleanup()

    def crear(self, hora="10:00"):
        return reservaciones.crear_reservacion(
            "A001234567", "S01", self.fecha, hora, 1, 2
        )

    def test_REG_P3_01_id_no_se_reutiliza_despues_de_cancelar(self):
        primera = self.crear("10:00")
        self.assertTrue(primera.exito)
        self.assertEqual(primera.datos.id, "R0001")

        self.assertTrue(reservaciones.cancelar_reservacion("R0001").exito)
        segunda = self.crear("12:00")
        self.assertTrue(segunda.exito)
        self.assertEqual(segunda.datos.id, "R0002")

    def test_REG_P3_02_reabrir_bd_mantiene_continuidad_de_ids(self):
        primera = self.crear("10:00")
        self.assertTrue(primera.exito)
        self.assertEqual(primera.datos.id, "R0001")

        # Simula cerrar y volver a abrir el almacenamiento usando el mismo archivo SQLite.
        conexion.configurar_ruta_bd(None)
        conexion.configurar_ruta_bd(str(self.ruta))
        conexion.preparar_bd()

        segunda = self.crear("12:00")
        self.assertTrue(segunda.exito)
        self.assertEqual(segunda.datos.id, "R0002")
        self.assertEqual(len(reservacion_repo.listar_reservaciones()), 2)


if __name__ == "__main__":
    unittest.main()
