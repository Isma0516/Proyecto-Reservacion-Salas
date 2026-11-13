"""Regresión BUG-INT-P2-01: capacidad de sala fuera del rango SQLite INTEGER."""
import tempfile
import unittest
from pathlib import Path

from solucion.datos import conexion, sala_repo
from solucion.modelos.sala import ESTADO_DISPONIBLE, ESTADO_FUERA_SERVICIO
from solucion.negocio import salas


class TestBugIntP201(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        conexion.configurar_ruta_bd(str(Path(self.temp.name) / "test.db"))
        conexion.preparar_bd()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.temp.cleanup()

    def test_INT_P2_06_registrar_capacidad_excesiva(self):
        resultado = salas.registrar_sala(
            "S06", "Sala grande", 10**30, ESTADO_DISPONIBLE
        )
        self.assertFalse(resultado.exito)
        self.assertIn("capacidad", resultado.mensaje.lower())
        self.assertIsNone(sala_repo.obtener_sala("S06"))

    def test_INT_P2_08_modificar_capacidad_excesiva(self):
        original = sala_repo.obtener_sala("S03")
        resultado = salas.modificar_sala(
            "S03", "Nombre alterado", 10**30, ESTADO_FUERA_SERVICIO
        )
        actual = sala_repo.obtener_sala("S03")
        self.assertFalse(resultado.exito)
        self.assertIn("capacidad", resultado.mensaje.lower())
        self.assertEqual(actual, original)

    def test_limite_superior_sqlite_rechazado(self):
        resultado = salas.registrar_sala(
            "S06", "Sala límite", 2**63, ESTADO_DISPONIBLE
        )
        self.assertFalse(resultado.exito)
        self.assertIsNone(sala_repo.obtener_sala("S06"))

    def test_capacidad_positiva_valida_no_cambia(self):
        resultado = salas.registrar_sala(
            "S06", "Sala válida", 12, ESTADO_DISPONIBLE
        )
        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(sala_repo.obtener_sala("S06").capacidad, 12)


if __name__ == "__main__":
    unittest.main()
