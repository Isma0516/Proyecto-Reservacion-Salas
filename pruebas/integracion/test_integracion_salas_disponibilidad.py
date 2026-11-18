"""
Pruebas de integración - Fase 7, Parte 2: salas, capacidad y disponibilidad.

Equipo evaluador. Cada prueba recorre varios módulos reales (negocio de salas,
negocio de reservaciones, repositorios y SQLite) y lleva el ID de su escenario
en el nombre (test_INT_P2_xx_...).

- No modifica el código productivo.
- Cada prueba usa una base SQLite temporal sembrada con los datos iniciales.
- La prueba de interfaz se omite si el equipo no tiene entorno gráfico.

Ejecución desde la raíz del repositorio:
    python -m unittest pruebas.integracion.test_integracion_salas_disponibilidad -v
"""
import hashlib
import os
import tempfile
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from solucion.datos import conexion, datos_iniciales, reservacion_repo, sala_repo
from solucion.modelos.reservacion import Reservacion
from solucion.negocio import reservaciones, salas

ANDREA = "A001234567"
CARLOS = "B009876543"


def dia(n):
    """Fecha AAAA-MM-DD relativa a hoy (D+n)."""
    return (date.today() + timedelta(days=n)).isoformat()


class BaseIntegracion(unittest.TestCase):
    """BD temporal con las 5 salas y los 3 estudiantes iniciales, sin reservaciones."""

    def setUp(self):
        archivo = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        archivo.close()
        self.ruta_bd = archivo.name
        conexion.configurar_ruta_bd(self.ruta_bd)
        conexion.inicializar_bd()
        datos_iniciales.sembrar_datos_iniciales()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        os.unlink(self.ruta_bd)

    def disponible(self, sala, fecha, hora, duracion=1):
        r = reservaciones.consultar_disponibilidad(sala, fecha, hora, duracion)
        self.assertTrue(r.exito, r.mensaje)
        return r.datos

    def huella(self):
        with open(self.ruta_bd, "rb") as archivo:
            return hashlib.md5(archivo.read()).hexdigest()

    def capacidad(self, sala):
        return sala_repo.obtener_sala(sala).capacidad


# ===========================================================================
class INTP2SalaNueva(BaseIntegracion):
    def test_INT_P2_01_sala_nueva_se_consulta_y_se_reserva(self):
        # RF-12, RF-04, RF-08 y RF-05: una sala registrada queda lista para todo el flujo.
        r = salas.registrar_sala(" s06 ", "Sala de grupos", 5)
        self.assertTrue(r.exito, r.mensaje)
        codigos = [s.codigo for s in salas.consultar_salas().datos]
        self.assertIn("S06", codigos)                                   # se normaliza el código

        self.assertTrue(self.disponible("S06", dia(1), "10:00"))
        creada = reservaciones.crear_reservacion(ANDREA, "s06", dia(1), "10:00", 1, 5)
        self.assertTrue(creada.exito, creada.mensaje)
        self.assertEqual(creada.datos.codigo_sala, "S06")
        self.assertFalse(self.disponible("S06", dia(1), "10:00"))       # ahora hay conflicto


class INTP2EstadoSala(BaseIntegracion):
    def test_INT_P2_02_fuera_de_servicio_bloquea_nuevas_y_conserva_existentes(self):
        # RF-12, RN-08 y RF-08: el estado de la sala gobierna creación, modificación y consulta.
        existente = reservaciones.crear_reservacion(ANDREA, "S03", dia(2), "10:00", 1, 3)
        self.assertTrue(existente.exito, existente.mensaje)

        self.assertTrue(salas.modificar_sala("S03", "Laboratorio de estudio", 10, "fuera_de_servicio").exito)
        nueva = reservaciones.crear_reservacion(CARLOS, "S03", dia(2), "14:00", 1, 2)
        self.assertFalse(nueva.exito)
        self.assertIn("fuera de servicio", nueva.mensaje)
        consulta = reservaciones.consultar_disponibilidad("S03", dia(2), "14:00", 1)
        self.assertFalse(consulta.datos)
        self.assertIn("fuera de servicio", consulta.mensaje)
        cambio = reservaciones.modificar_reservacion("R0001", "S03", dia(2), "11:00", 1, 3)
        self.assertFalse(cambio.exito)
        self.assertEqual(reservacion_repo.obtener_reservacion("R0001").hora_inicio, "10:00")
        self.assertEqual(reservacion_repo.obtener_reservacion("R0001").estado, "activa")
        self.assertEqual(len(reservacion_repo.listar_reservaciones()), 1)  # solo la existente

        self.assertTrue(salas.modificar_sala("S03", "Laboratorio de estudio", 10, "disponible").exito)
        self.assertTrue(self.disponible("S03", dia(2), "14:00"))
        self.assertTrue(reservaciones.crear_reservacion(CARLOS, "S03", dia(2), "14:00", 1, 2).exito)


class INTP2ReduccionCapacidad(BaseIntegracion):
    def test_INT_P2_03_reducir_capacidad_con_reservas_existentes(self):
        # RF-12 y RN-07: solo las reservas activas futuras impiden reducir la capacidad.
        reservaciones.crear_reservacion(ANDREA, "S02", dia(3), "10:00", 1, 5)
        reservacion_repo.insertar_reservacion(Reservacion("R0050", CARLOS, "S02", dia(-1), "10:00", 1, 6))
        cancelada = reservaciones.crear_reservacion(CARLOS, "S02", dia(4), "10:00", 1, 6)
        reservaciones.cancelar_reservacion(cancelada.datos.id)

        rechazo = salas.modificar_sala("S02", "Sala Biblioteca 2", 4, "disponible")
        self.assertFalse(rechazo.exito)
        self.assertIn("5", rechazo.mensaje)
        self.assertEqual(self.capacidad("S02"), 6)                      # sin cambios en SQLite

        self.assertTrue(salas.modificar_sala("S02", "Sala Biblioteca 2", 5, "disponible").exito)
        self.assertEqual(self.capacidad("S02"), 5)                      # igual a la mayor futura
        self.assertTrue(salas.modificar_sala("S01", "Sala Biblioteca 1", 1, "disponible").exito)  # otra sala


class INTP2CapacidadVigente(BaseIntegracion):
    def test_INT_P2_04_nuevas_reservas_usan_la_capacidad_actualizada(self):
        # RN-07, RF-05 y RF-13: crear y modificar validan contra la capacidad guardada.
        self.assertFalse(reservaciones.crear_reservacion(ANDREA, "S01", dia(1), "10:00", 1, 6).exito)
        self.assertTrue(salas.modificar_sala("S01", "Sala Biblioteca 1", 6, "disponible").exito)
        creada = reservaciones.crear_reservacion(ANDREA, "S01", dia(1), "10:00", 1, 6)
        self.assertTrue(creada.exito, creada.mensaje)

        cambio = reservaciones.modificar_reservacion(creada.datos.id, "S05", dia(1), "10:00", 1, 6)
        self.assertFalse(cambio.exito)
        self.assertIn("capacidad", cambio.mensaje)
        original = reservacion_repo.obtener_reservacion(creada.datos.id)
        self.assertEqual((original.codigo_sala, original.cantidad_personas), ("S01", 6))


class INTP2ConflictosYConsecutivas(BaseIntegracion):
    def test_INT_P2_05_disponibilidad_y_creacion_coinciden(self):
        # RN-09, RN-10 y RF-08: la consulta y la creación aplican la misma regla.
        self.assertTrue(reservaciones.crear_reservacion(ANDREA, "S03", dia(2), "10:00", 2, 3).exito)  # 10 a 12
        casos = [("08:00", 2, True), ("09:00", 1, True), ("12:00", 1, True),
                 ("09:00", 2, False), ("11:00", 1, False), ("11:00", 2, False)]
        for hora, duracion, esperado in casos:
            with self.subTest(hora=hora, duracion=duracion):
                self.assertEqual(self.disponible("S03", dia(2), hora, duracion), esperado)

        self.assertTrue(reservaciones.crear_reservacion(CARLOS, "S03", dia(2), "12:00", 2, 3).exito)  # consecutiva
        self.assertTrue(reservaciones.crear_reservacion(CARLOS, "S03", dia(2), "08:00", 2, 3).exito)  # consecutiva
        self.assertFalse(reservaciones.crear_reservacion(CARLOS, "S03", dia(2), "11:00", 1, 3).exito)
        self.assertTrue(self.disponible("S02", dia(2), "10:00", 2))     # otra sala no se ve afectada

        antes = self.huella()
        self.disponible("S03", dia(2), "15:00")
        self.assertEqual(self.huella(), antes)  # consulta sin cambios


class INTP2CapacidadExtrema(BaseIntegracion):
    def test_INT_P2_06_capacidad_muy_grande_se_rechaza_con_mensaje(self):
        # RF-12: una capacidad que SQLite no puede guardar debe rechazarse sin error técnico.
        for operacion in ("registrar", "modificar"):
            with self.subTest(operacion=operacion):
                try:
                    if operacion == "registrar":
                        r = salas.registrar_sala("S06", "Sala grande", 10 ** 30)
                    else:
                        r = salas.modificar_sala("S03", "Laboratorio de estudio", 10 ** 30, "disponible")
                except Exception as error:                              # noqa: BLE001
                    self.fail(f"Se lanzó {type(error).__name__} en lugar de un Resultado: {error}")
                self.assertFalse(r.exito)
        self.assertIsNone(sala_repo.obtener_sala("S06"))
        self.assertEqual(self.capacidad("S03"), 10)


class INTP2Interfaz(BaseIntegracion):
    def setUp(self):
        super().setUp()
        try:
            import tkinter as tk
            prueba = tk.Tk()
            prueba.destroy()
        except Exception:                                               # noqa: BLE001
            self.skipTest("No hay entorno gráfico para crear ventanas Tkinter")
        from solucion.ui import aplicacion
        self.ui = aplicacion
        self.mensajes = []
        for tipo in ("showinfo", "showwarning", "showerror"):
            p = patch.object(aplicacion.messagebox, tipo,
                             lambda titulo, texto, parent=None, _t=tipo: self.mensajes.append((_t, texto)))
            p.start()
            self.addCleanup(p.stop)
        self.app = aplicacion.Aplicacion()
        self.app.withdraw()
        self.addCleanup(self.app.destroy)

    def test_INT_P2_07_registrar_sala_y_consultar_disponibilidad_desde_la_pantalla(self):
        # RF-12 y RF-08 desde la interfaz: pantalla de salas, negocio y SQLite.
        self.app.s["codigo"].set("S06")
        self.app.s["nombre"].set("Sala de grupos")
        self.app.s["capacidad"].set("5")
        self.app.s["estado"].set("disponible")
        self.app._s_registrar()
        self.assertEqual(self.mensajes[-1][0], "showinfo")
        self.assertIn("S06", [self.app.ts.item(i, "values")[0] for i in self.app.ts.get_children()])

        self.app.r["codigo"].set("S06")
        self.app.r["fecha"].set(dia(1))
        self.app._r_disponibilidad()
        self.assertIn("disponible", self.mensajes[-1][1])

    def test_INT_P2_08_capacidad_muy_grande_desde_la_pantalla_muestra_mensaje(self):
        # RF-12 desde la interfaz: el error debe llegar como mensaje a la persona usuaria.
        self.app.s["codigo"].set("S06")
        self.app.s["nombre"].set("Sala grande")
        self.app.s["capacidad"].set("1" + "0" * 30)
        self.app.s["estado"].set("disponible")
        try:
            self.app._s_registrar()
        except Exception as error:                                      # noqa: BLE001
            self.fail(f"La pantalla dejó escapar {type(error).__name__}: {error}")
        self.assertTrue(self.mensajes, "No se mostró ningún mensaje a la persona usuaria")
        self.assertIsNone(sala_repo.obtener_sala("S06"))


if __name__ == "__main__":
    unittest.main()
