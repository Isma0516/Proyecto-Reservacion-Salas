"""Fase 7 - Parte 5: integración del panel, reportes y rendimiento."""

import csv
import tempfile
import time
import unittest
from datetime import date, timedelta
from pathlib import Path

from solucion.datos import conexion, reservacion_repo
from solucion.negocio import estudiantes, salas, reservaciones, panel, reportes


class TestFase7Parte5PanelReportes(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ruta = Path(self.temp.name) / "fase7_parte5.db"
        conexion.configurar_ruta_bd(str(self.ruta))
        conexion.preparar_bd()

        self.fecha = (date.today() + timedelta(days=20)).isoformat()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.temp.cleanup()

    # ---------------------------------------------------------
    # CASOS DE INTEGRACIÓN
    # ---------------------------------------------------------

    def test_INT_P5_01_panel_refleja_creacion_modificacion_y_cancelacion(self):
        """El panel debe reflejar los cambios realizados sobre una reservación."""

        creada = reservaciones.crear_reservacion(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            2
        )

        self.assertTrue(creada.exito, creada.mensaje)

        resultado = panel.filtrar(
            fecha_desde=self.fecha,
            fecha_hasta=self.fecha,
            sala="S01",
            estado="activa"
        )

        self.assertTrue(resultado.exito)
        self.assertEqual(len(resultado.datos), 1)
        self.assertEqual(resultado.datos[0].id, creada.datos.id)

        modificada = reservaciones.modificar_reservacion(
            creada.datos.id,
            "S02",
            self.fecha,
            "12:00",
            1,
            2
        )

        self.assertTrue(modificada.exito, modificada.mensaje)

        resultado_s01 = panel.filtrar(
            fecha_desde=self.fecha,
            fecha_hasta=self.fecha,
            sala="S01",
            estado="activa"
        )

        resultado_s02 = panel.filtrar(
            fecha_desde=self.fecha,
            fecha_hasta=self.fecha,
            sala="S02",
            estado="activa"
        )

        self.assertEqual(len(resultado_s01.datos), 0)
        self.assertEqual(len(resultado_s02.datos), 1)

        cancelada = reservaciones.cancelar_reservacion(creada.datos.id)
        self.assertTrue(cancelada.exito, cancelada.mensaje)

        activas = panel.filtrar(
            fecha_desde=self.fecha,
            fecha_hasta=self.fecha,
            sala="S02",
            estado="activa"
        )

        canceladas = panel.filtrar(
            fecha_desde=self.fecha,
            fecha_hasta=self.fecha,
            sala="S02",
            estado="cancelada"
        )

        self.assertEqual(len(activas.datos), 0)
        self.assertEqual(len(canceladas.datos), 1)
        self.assertEqual(canceladas.datos[0].id, creada.datos.id)

    def test_INT_P5_02_filtros_combinados_panel(self):
        """Los filtros combinados deben devolver únicamente las reservas coincidentes."""

        r1 = reservaciones.crear_reservacion(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            1,
            2
        )

        r2 = reservaciones.crear_reservacion(
            "B009876543",
            "S02",
            self.fecha,
            "12:00",
            1,
            2
        )

        self.assertTrue(r1.exito, r1.mensaje)
        self.assertTrue(r2.exito, r2.mensaje)

        resultado = panel.filtrar(
            fecha_desde=self.fecha,
            fecha_hasta=self.fecha,
            sala="S01",
            estado="activa",
            carne="A001234567"
        )

        self.assertTrue(resultado.exito)
        self.assertEqual(len(resultado.datos), 1)
        self.assertEqual(resultado.datos[0].id, r1.datos.id)
        self.assertEqual(resultado.datos[0].codigo_sala, "S01")
        self.assertEqual(resultado.datos[0].carne_estudiante, "A001234567")

    def test_INT_P5_03_reporte_refleja_datos_almacenados(self):
        """El reporte debe reflejar los datos actuales de la reservación."""

        creada = reservaciones.crear_reservacion(
            "A001234567",
            "S01",
            self.fecha,
            "10:00",
            2,
            3
        )

        self.assertTrue(creada.exito, creada.mensaje)

        resultado = reportes.generar_reporte(
            self.fecha,
            self.fecha
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(len(resultado.datos), 1)

        fila = resultado.datos[0]

        self.assertEqual(fila[0], creada.datos.id)
        self.assertEqual(fila[1], "A001234567")
        self.assertEqual(fila[4], self.fecha)
        self.assertEqual(fila[5], "10:00")
        self.assertEqual(fila[6], "12:00")
        self.assertEqual(fila[7], 3)
        self.assertEqual(fila[8], "activa")

    def test_INT_P5_04_rendimiento_panel_con_5000_reservaciones(self):
        """El filtrado del panel debe responder en menos de dos segundos."""

        fecha_carga = (date.today() + timedelta(days=180)).isoformat()

        con = conexion.obtener_conexion()

        try:
            with con:
                con.executemany(
                    """
                    INSERT INTO estudiantes
                    VALUES (?, ?, ?, 1)
                    """,
                    [
                        (
                            f"T{i:09d}",
                            f"Estudiante {i}",
                            f"est{i}@universidad.ac.cr"
                        )
                        for i in range(1000)
                    ]
                )

                con.executemany(
                    """
                    INSERT INTO reservaciones
                    (
                        id,
                        carne_estudiante,
                        codigo_sala,
                        fecha,
                        hora_inicio,
                        duracion,
                        cantidad_personas,
                        estado
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            f"R{i + 1000:04d}",
                            f"T{i % 1000:09d}",
                            "S01",
                            fecha_carga,
                            f"{8 + (i % 12):02d}:00",
                            1,
                            1,
                            "cancelada"
                        )
                        for i in range(5000)
                    ]
                )
        finally:
            con.close()

        inicio = time.perf_counter()

        resultado = panel.filtrar(
            fecha_desde=fecha_carga,
            fecha_hasta=fecha_carga
        )

        tiempo = time.perf_counter() - inicio

        self.assertTrue(resultado.exito)
        self.assertEqual(len(resultado.datos), 5000)
        self.assertLess(
            tiempo,
            2.0,
            f"Filtrado del panel con 5000 reservaciones: {tiempo:.3f} s"
        )

    # ---------------------------------------------------------
    # CASOS DE REGRESIÓN
    # ---------------------------------------------------------

    def test_REG_P5_01_csv_utf8_encabezados_y_caracteres_especiales(self):
        """Regresión de exportación CSV UTF-8 con nombres que contienen tildes."""

        estudiante = estudiantes.registrar_estudiante(
            "D000000001",
            "Ángela Iñíguez",
            "angela@tec.ac.cr"
        )

        sala = salas.registrar_sala(
            "S06",
            "Sala Güímar Úbeda",
            4
        )

        self.assertTrue(estudiante.exito, estudiante.mensaje)
        self.assertTrue(sala.exito, sala.mensaje)

        reserva = reservaciones.crear_reservacion(
            "D000000001",
            "S06",
            self.fecha,
            "10:00",
            1,
            2
        )

        self.assertTrue(reserva.exito, reserva.mensaje)

        salida = Path(self.temp.name) / "reporte_fase7.csv"

        resultado = reportes.exportar_csv(
            self.fecha,
            self.fecha,
            salida
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertTrue(salida.exists())

        with salida.open(
            encoding="utf-8",
            newline=""
        ) as archivo:
            filas = list(csv.reader(archivo))

        self.assertEqual(
            filas[0],
            [
                "ID",
                "Carné",
                "Estudiante",
                "Sala",
                "Fecha",
                "Hora inicio",
                "Hora fin",
                "Personas",
                "Estado"
            ]
        )

        contenido = str(filas)

        self.assertIn("Ángela Iñíguez", contenido)
        self.assertIn("Güímar Úbeda", contenido)

    def test_REG_P5_02_rango_fechas_invalido_no_genera_reporte(self):
        """Regresión de validación de rangos inválidos en reportes."""

        resultado_fecha = reportes.generar_reporte(
            "2027-02-30",
            self.fecha
        )

        resultado_rango = reportes.generar_reporte(
            "2029-01-01",
            "2028-01-01"
        )

        self.assertFalse(resultado_fecha.exito)
        self.assertFalse(resultado_rango.exito)


if __name__ == "__main__":
    unittest.main()