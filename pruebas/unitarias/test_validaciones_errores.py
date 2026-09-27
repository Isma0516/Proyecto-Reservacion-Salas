"""Pruebas de robustez para RNF-05 y validaciones de entrada de la Persona 3."""
import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from solucion.datos import conexion, estudiante_repo, sala_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.sala import Sala
from solucion.negocio import estudiantes, reservaciones, salas


class PruebasValidacionesYManejoErrores(unittest.TestCase):
    def setUp(self):
        self.archivo_temporal = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.archivo_temporal.close()
        conexion.configurar_ruta_bd(self.archivo_temporal.name)
        conexion.inicializar_bd()
        estudiantes.registrar_estudiante("EST0000001", "Ana Pérez", "ana@correo.com")
        sala_repo.insertar_sala(
            Sala(codigo="S01", nombre="Sala Alpha", capacidad=4, estado="disponible")
        )
        self.manana = (date.today() + timedelta(days=1)).isoformat()

    def tearDown(self):
        os.unlink(self.archivo_temporal.name)

    def test_carne_no_texto_no_cierra_aplicacion(self):
        resultado = estudiantes.registrar_estudiante(1234567890, "Nombre", "correo@ejemplo.com")
        self.assertFalse(resultado.exito)

    def test_nombre_no_texto_no_cierra_aplicacion(self):
        resultado = estudiantes.registrar_estudiante("ABC1234567", 123, "correo@ejemplo.com")
        self.assertFalse(resultado.exito)

    def test_rechaza_booleano_como_cantidad_personas(self):
        resultado = reservaciones.crear_reservacion(
            "EST0000001", "S01", self.manana, "10:00", 1, True
        )
        self.assertFalse(resultado.exito)

    def test_hora_fuera_de_rango_no_lanza_excepcion(self):
        resultado = reservaciones.crear_reservacion(
            "EST0000001", "S01", self.manana, "23:00", 2, 2
        )
        self.assertFalse(resultado.exito)
        self.assertIn("20:00", resultado.mensaje)

    def test_disponibilidad_rechaza_fecha_pasada(self):
        ayer = (date.today() - timedelta(days=1)).isoformat()
        resultado = reservaciones.consultar_disponibilidad("S01", ayer, "10:00", 1)
        self.assertFalse(resultado.exito)

    def test_cancelacion_rechaza_id_invalido(self):
        resultado = reservaciones.cancelar_reservacion("123")
        self.assertFalse(resultado.exito)

    def test_capa_datos_traduce_error_sqlite(self):
        with patch(
            "solucion.datos.conexion.obtener_conexion",
            side_effect=sqlite3.OperationalError("fallo simulado"),
        ):
            with self.assertRaises(ErrorPersistencia):
                estudiante_repo.existe_carne("EST0000001")

    def test_error_bd_en_registro_se_convierte_en_resultado(self):
        with patch(
            "solucion.negocio.estudiantes.estudiante_repo.existe_carne",
            side_effect=ErrorPersistencia("fallo simulado"),
        ):
            resultado = estudiantes.registrar_estudiante(
                "ABC1234567", "Nombre", "correo@ejemplo.com"
            )
        self.assertFalse(resultado.exito)

    def test_error_bd_en_consulta_estudiantes_se_convierte_en_resultado(self):
        with patch(
            "solucion.negocio.estudiantes.estudiante_repo.listar_estudiantes",
            side_effect=ErrorPersistencia("fallo simulado"),
        ):
            resultado = estudiantes.consultar_estudiantes()
        self.assertFalse(resultado.exito)

    def test_error_bd_en_consulta_salas_se_convierte_en_resultado(self):
        with patch(
            "solucion.negocio.salas.sala_repo.listar_salas",
            side_effect=ErrorPersistencia("fallo simulado"),
        ):
            resultado = salas.consultar_salas()
        self.assertFalse(resultado.exito)

    def test_error_bd_en_disponibilidad_se_convierte_en_resultado(self):
        with patch(
            "solucion.negocio.reservaciones.sala_repo.obtener_sala",
            side_effect=ErrorPersistencia("fallo simulado"),
        ):
            resultado = reservaciones.consultar_disponibilidad(
                "S01", self.manana, "10:00", 1
            )
        self.assertFalse(resultado.exito)


if __name__ == "__main__":
    unittest.main()
