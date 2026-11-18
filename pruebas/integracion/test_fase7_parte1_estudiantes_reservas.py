"""Fase 7 - Parte 1: pruebas cruzadas de integración estudiantes/reservaciones.

No modifica el código de producción. Cada prueba utiliza una base SQLite
independiente en una carpeta temporal, sin tocar solucion/reservaciones.db.

Caso INT: escenario de integración nuevo de fase 7.
Caso REG: regresión a partir de hallazgos corregidos en fase 6.
"""
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from solucion.datos import conexion, estudiante_repo, reservacion_repo
from solucion.negocio import estudiantes, reservaciones


class Fase7Parte1EstudiantesYReservaciones(unittest.TestCase):
    def setUp(self):
        self.directorio_temporal = tempfile.TemporaryDirectory(prefix="fase7_p1_")
        self.ruta_bd = Path(self.directorio_temporal.name) / "pruebas.db"
        conexion.configurar_ruta_bd(self.ruta_bd)
        conexion.preparar_bd()
        self.fecha = (date.today() + timedelta(days=20)).isoformat()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.directorio_temporal.cleanup()

    def crear_reserva(self, carne, hora="10:00", sala="S01"):
        return reservaciones.crear_reservacion(
            carne, sala, self.fecha, hora, 1, 1
        )

    def reservas(self):
        return reservacion_repo.listar_reservaciones()

    # INT-01: RF-02, RF-05, RF-07, RN-01.
    def test_INT01_registro_y_reserva_y_busqueda(self):
        registrado = estudiantes.registrar_estudiante(
            "D000000001", "María López", "maria@tec.ac.cr"
        )
        self.assertTrue(registrado.exito, registrado.mensaje)
        reserva = self.crear_reserva("D000000001")
        self.assertTrue(reserva.exito, reserva.mensaje)
        encontrados = reservaciones.buscar_reservaciones_estudiante("d000000001")
        self.assertTrue(encontrados.exito, encontrados.mensaje)
        self.assertEqual(len(encontrados.datos), 1)
        self.assertEqual(encontrados.datos[0].id, reserva.datos.id)
        self.assertEqual(encontrados.datos[0].carne_estudiante, "D000000001")

    # INT-02: RF-05, RF-11, RN-01. El historial se conserva al inactivar.
    def test_INT02_inactivar_con_reserva_previa_y_rechazar_nueva(self):
        anterior = self.crear_reserva("A001234567")
        self.assertTrue(anterior.exito, anterior.mensaje)
        cambio = estudiantes.modificar_estudiante(
            "A001234567", "Andrea Solano", "andrea@universidad.ac.cr", False
        )
        self.assertTrue(cambio.exito, cambio.mensaje)
        nueva = self.crear_reserva("A001234567", hora="12:00")
        self.assertFalse(nueva.exito)
        encontrados = reservaciones.buscar_reservaciones_estudiante("A001234567")
        self.assertTrue(encontrados.exito, encontrados.mensaje)
        self.assertEqual([r.id for r in encontrados.datos], [anterior.datos.id])
        self.assertEqual(len(self.reservas()), 1)
        self.assertFalse(estudiante_repo.obtener_estudiante("A001234567").activo)

    # INT-03: RF-07, RF-11: editar contacto sin romper reserva/identificador.
    def test_INT03_actualizar_nombre_correo_conserva_reserva(self):
        anterior = self.crear_reserva("A001234567")
        self.assertTrue(anterior.exito, anterior.mensaje)
        cambio = estudiantes.modificar_estudiante(
            "a001234567", "Andrea Gómez", "nuevo.correo@tec.ac.cr", True
        )
        self.assertTrue(cambio.exito, cambio.mensaje)
        e = estudiante_repo.obtener_estudiante("A001234567")
        self.assertEqual(e.nombre, "Andrea Gómez")
        self.assertEqual(e.correo, "nuevo.correo@tec.ac.cr")
        encontrados = reservaciones.buscar_reservaciones_estudiante("a001234567")
        self.assertTrue(encontrados.exito, encontrados.mensaje)
        self.assertEqual(len(encontrados.datos), 1)
        self.assertEqual(encontrados.datos[0].id, anterior.datos.id)
        self.assertEqual(encontrados.datos[0].carne_estudiante, "A001234567")

    # INT-04: RN-01/RF-11: reactivar vuelve a permitir reservas.
    def test_INT04_reactivar_y_conservar_reservas_anteriores(self):
        anterior = self.crear_reserva("A001234567")
        self.assertTrue(anterior.exito, anterior.mensaje)
        self.assertTrue(estudiantes.modificar_estudiante(
            "A001234567", "Andrea Solano", "andrea@universidad.ac.cr", False
        ).exito)
        self.assertFalse(self.crear_reserva("A001234567", "12:00").exito)
        self.assertTrue(estudiantes.modificar_estudiante(
            "A001234567", "Andrea Solano", "andrea@universidad.ac.cr", True
        ).exito)
        segunda = self.crear_reserva("A001234567", "12:00")
        self.assertTrue(segunda.exito, segunda.mensaje)
        encontrados = reservaciones.buscar_reservaciones_estudiante("A001234567")
        self.assertTrue(encontrados.exito, encontrados.mensaje)
        self.assertEqual({r.id for r in encontrados.datos}, {anterior.datos.id, segunda.datos.id})

    # INT-05: RF-02/RF-05: duplicado case-insensitive no altera el original.
    def test_INT05_duplicado_por_mayusculas_no_altera_datos(self):
        anterior = self.crear_reserva("A001234567")
        self.assertTrue(anterior.exito, anterior.mensaje)
        original = estudiante_repo.obtener_estudiante("A001234567")
        duplicado = estudiantes.registrar_estudiante(
            "a001234567", "Nombre Duplicado", "duplicado@tec.ac.cr"
        )
        self.assertFalse(duplicado.exito)
        otra = estudiante_repo.obtener_estudiante("a001234567")
        self.assertEqual((otra.carne, otra.nombre, otra.correo),
                         (original.carne, original.nombre, original.correo))
        self.assertEqual(len(estudiante_repo.listar_estudiantes()), 3)
        self.assertEqual(len(self.reservas()), 1)

    # INT-06: RF-05/RF-07/RN-01: inexistente no deja escrituras.
    def test_INT06_carnet_inexistente_no_crea_reserva(self):
        cantidad_antes = len(self.reservas())
        denegada = self.crear_reserva("Z999999999")
        self.assertFalse(denegada.exito)
        busqueda = reservaciones.buscar_reservaciones_estudiante("Z999999999")
        self.assertFalse(busqueda.exito)
        self.assertEqual(len(self.reservas()), cantidad_antes)

    # REG-01: BUG-RN-04, CP-RN01-04.
    def test_REG01_carne_minusculas_reserva_con_identificador_canonico(self):
        r = self.crear_reserva("a001234567")
        self.assertTrue(r.exito, r.mensaje)
        self.assertEqual(r.datos.carne_estudiante, "A001234567")
        guardada = reservacion_repo.obtener_reservacion(r.datos.id)
        self.assertEqual(guardada.carne_estudiante, "A001234567")

    # REG-02: BUG-RF02-01, CP-RF02-06.
    def test_REG02_nombre_corto_rechazado_sin_escritura(self):
        antes = len(estudiante_repo.listar_estudiantes())
        r = estudiantes.registrar_estudiante(
            "D000000002", "A  ", "ana@tec.ac.cr"
        )
        self.assertFalse(r.exito)
        self.assertIsNone(estudiante_repo.obtener_estudiante("D000000002"))
        self.assertEqual(len(estudiante_repo.listar_estudiantes()), antes)

    # REG-03: RF-11 y regresión cercana al BUG-RF02-01.
    def test_REG03_edicion_nombre_invalido_conserva_estudiante_y_reserva(self):
        anterior = self.crear_reserva("A001234567")
        self.assertTrue(anterior.exito, anterior.mensaje)
        original = estudiante_repo.obtener_estudiante("A001234567")
        resultado = estudiantes.modificar_estudiante(
            "A001234567", "A ", "cambio@tec.ac.cr", True
        )
        self.assertFalse(resultado.exito)
        e = estudiante_repo.obtener_estudiante("A001234567")
        self.assertEqual((e.nombre, e.correo, e.activo),
                         (original.nombre, original.correo, original.activo))
        self.assertEqual([r.id for r in self.reservas()], [anterior.datos.id])


if __name__ == "__main__":
    unittest.main(verbosity=2)
