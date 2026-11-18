"""Pruebas de integración y regresión de Fase 7
Integración de recurrencia, límites y cancelaciones de series.
"""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from solucion.datos import conexion, reservacion_repo
from solucion.negocio import reservaciones


class TestFase7Parte4Recurrencia(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self.temp.name) / "base.db"

        conexion.configurar_ruta_bd(str(self.ruta))
        conexion.preparar_bd()

        self.fecha_base = date.today() + timedelta(days=10)
        self.fecha = self.fecha_base.isoformat()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.temp.cleanup()

    # ---------------------------------------------------------
    # CASOS DE INTEGRACIÓN
    # ---------------------------------------------------------

    def test_INT_P4_01_serie_tres_ocurrencias_valida(self):
        """Crear una serie semanal válida de tres ocurrencias."""

        resultado = reservaciones.crear_serie_semanal(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            4,
            3
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(len(resultado.datos), 3)

        serie_id = resultado.datos[0].serie_id
        guardadas = reservacion_repo.listar_por_serie(serie_id)

        self.assertEqual(len(guardadas), 3)
        self.assertTrue(all(r.estado == "activa" for r in guardadas))

        fechas_esperadas = {
            (self.fecha_base + timedelta(days=0)).isoformat(),
            (self.fecha_base + timedelta(days=7)).isoformat(),
            (self.fecha_base + timedelta(days=14)).isoformat(),
        }

        self.assertEqual({r.fecha for r in guardadas}, fechas_esperadas)

    def test_INT_P4_02_limite_tres_rechaza_cuatro_sin_escritura(self):
        """Una serie de cuatro ocurrencias debe ser rechazada por RN-11."""

        cantidad_antes = len(reservacion_repo.listar_reservaciones())

        resultado = reservaciones.crear_serie_semanal(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            2,
            4
        )

        self.assertFalse(resultado.exito)
        self.assertIn("máximo de tres", resultado.mensaje)

        cantidad_despues = len(reservacion_repo.listar_reservaciones())
        self.assertEqual(cantidad_antes, cantidad_despues)

    def test_INT_P4_03_conflicto_en_serie_no_deja_registros_parciales(self):
        """Un conflicto en una ocurrencia debe rechazar toda la serie."""

        fecha_conflicto = (
            self.fecha_base + timedelta(days=7)
        ).isoformat()

        previa = reservaciones.crear_reservacion(
            "B009876543",
            "S01",
            fecha_conflicto,
            "10:00",
            1,
            2
        )

        self.assertTrue(previa.exito, previa.mensaje)

        cantidad_antes = len(reservacion_repo.listar_reservaciones())

        resultado = reservaciones.crear_serie_semanal(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            2,
            3
        )

        self.assertFalse(resultado.exito)

        cantidad_despues = len(reservacion_repo.listar_reservaciones())
        self.assertEqual(cantidad_antes, cantidad_despues)

    def test_INT_P4_04_cancelar_una_ocurrencia_conserva_las_demas(self):
        """Cancelar una ocurrencia no debe cancelar toda la serie."""

        serie = reservaciones.crear_serie_semanal(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            2,
            3
        )

        self.assertTrue(serie.exito, serie.mensaje)

        primera = serie.datos[0]
        segunda = serie.datos[1]
        tercera = serie.datos[2]

        cancelacion = reservaciones.cancelar_reservacion(segunda.id)
        self.assertTrue(cancelacion.exito, cancelacion.mensaje)

        guardadas = reservacion_repo.listar_por_serie(primera.serie_id)
        estados = {r.id: r.estado for r in guardadas}

        self.assertEqual(estados[primera.id], "activa")
        self.assertEqual(estados[segunda.id], "cancelada")
        self.assertEqual(estados[tercera.id], "activa")

        nueva = reservaciones.crear_reservacion(
            "B009876543",
            "S01",
            segunda.fecha,
            "10:00",
            1,
            2
        )

        self.assertTrue(nueva.exito, nueva.mensaje)

    def test_INT_P4_05_cancelar_ocurrencias_futuras_desde_segunda(self):
        """Cancelar desde la segunda ocurrencia conserva la primera."""

        serie = reservaciones.crear_serie_semanal(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            2,
            3
        )

        self.assertTrue(serie.exito, serie.mensaje)

        primera = serie.datos[0]
        segunda = serie.datos[1]
        tercera = serie.datos[2]

        resultado = reservaciones.cancelar_ocurrencias_futuras(
            segunda.id
        )

        self.assertTrue(resultado.exito, resultado.mensaje)

        guardadas = reservacion_repo.listar_por_serie(primera.serie_id)
        estados = {r.id: r.estado for r in guardadas}

        self.assertEqual(estados[primera.id], "activa")
        self.assertEqual(estados[segunda.id], "cancelada")
        self.assertEqual(estados[tercera.id], "cancelada")

    # ---------------------------------------------------------
    # CASOS DE REGRESIÓN
    # ---------------------------------------------------------

    def test_REG_P4_01_ocho_ocurrencias_siguen_rechazadas_por_RN11(self):
        """Regresión del comportamiento CP-RF14-02 de Fase 6."""

        cantidad_antes = len(reservacion_repo.listar_reservaciones())

        resultado = reservaciones.crear_serie_semanal(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            1,
            8
        )

        self.assertFalse(resultado.exito)
        self.assertIn("máximo de tres", resultado.mensaje)

        self.assertEqual(
            len(reservacion_repo.listar_reservaciones()),
            cantidad_antes
        )

    def test_REG_P4_02_cancelacion_futuras_serie(self):
        """Regresión de la cancelación de ocurrencias futuras."""

        serie = reservaciones.crear_serie_semanal(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            2,
            2
        )

        self.assertTrue(serie.exito, serie.mensaje)

        resultado = reservaciones.cancelar_ocurrencias_futuras(
            serie.datos[0].id
        )

        self.assertTrue(resultado.exito, resultado.mensaje)

        guardadas = reservacion_repo.listar_por_serie(
            serie.datos[0].serie_id
        )

        self.assertEqual(len(guardadas), 2)
        self.assertTrue(
            all(r.estado == "cancelada" for r in guardadas)
        )


if __name__ == "__main__":
    unittest.main()