"""
Pruebas unitarias sobre la capa de persistencia agregada en esta entrega:
datos iniciales (RF-01), actualización de estudiantes/salas (RF-11/RF-12),
historial y búsqueda de reservaciones (RF-06/RF-07), series recurrentes
(RF-14) y auditoría (RF-17). Ejecutar desde la raíz del proyecto con:
    python -m unittest discover -s pruebas/unitarias -t .
"""
import os
import tempfile
import unittest

from solucion.datos import auditoria_repo, conexion, datos_iniciales, estudiante_repo, reservacion_repo, sala_repo
from solucion.modelos.reservacion import Reservacion


class PruebasPersistencia(unittest.TestCase):
    def setUp(self):
        self.archivo_temporal = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.archivo_temporal.close()
        conexion.configurar_ruta_bd(self.archivo_temporal.name)
        conexion.inicializar_bd()

    def tearDown(self):
        os.unlink(self.archivo_temporal.name)

    # --- RF-01: datos iniciales ---

    def test_siembra_datos_iniciales(self):
        datos_iniciales.sembrar_datos_iniciales()
        salas = sala_repo.listar_salas()
        estudiantes = estudiante_repo.listar_estudiantes()
        self.assertEqual(len(salas), 5)
        self.assertEqual(len(estudiantes), 3)
        sala_s04 = sala_repo.obtener_sala("S04")
        self.assertEqual(sala_s04.estado, "fuera_servicio")
        estudiante_inactivo = estudiante_repo.obtener_estudiante("C004567890")
        self.assertFalse(estudiante_inactivo.activo)

    def test_siembra_es_idempotente(self):
        # CP-RF01-02: reabrir/re-sembrar no debe duplicar registros
        datos_iniciales.sembrar_datos_iniciales()
        datos_iniciales.sembrar_datos_iniciales()
        self.assertEqual(len(sala_repo.listar_salas()), 5)
        self.assertEqual(len(estudiante_repo.listar_estudiantes()), 3)

    # --- RF-11 / RF-12: actualización sin tocar la llave ---

    def test_actualizar_estudiante_no_cambia_carne(self):
        datos_iniciales.sembrar_datos_iniciales()
        estudiante = estudiante_repo.obtener_estudiante("A001234567")
        estudiante.nombre = "Andrea Solano Ramírez"
        estudiante.activo = False
        estudiante_repo.actualizar_estudiante(estudiante)
        actualizado = estudiante_repo.obtener_estudiante("A001234567")
        self.assertEqual(actualizado.nombre, "Andrea Solano Ramírez")
        self.assertFalse(actualizado.activo)

    def test_actualizar_sala_no_cambia_codigo(self):
        datos_iniciales.sembrar_datos_iniciales()
        sala = sala_repo.obtener_sala("S01")
        sala.capacidad = 5
        sala.estado = "fuera_servicio"
        sala_repo.actualizar_sala(sala)
        actualizada = sala_repo.obtener_sala("S01")
        self.assertEqual(actualizada.capacidad, 5)
        self.assertEqual(actualizada.estado, "fuera_servicio")

    # --- RF-06 / RF-07: historial y búsqueda ---

    def test_listar_reservaciones_orden_fecha_hora(self):
        datos_iniciales.sembrar_datos_iniciales()
        reservacion_repo.insertar_reservacion(
            Reservacion(id="R0001", carne_estudiante="A001234567", codigo_sala="S01",
                        fecha="2026-10-02", hora_inicio="09:00", duracion=1, cantidad_personas=2)
        )
        reservacion_repo.insertar_reservacion(
            Reservacion(id="R0002", carne_estudiante="A001234567", codigo_sala="S01",
                        fecha="2026-10-01", hora_inicio="14:00", duracion=1, cantidad_personas=2)
        )
        historial = reservacion_repo.listar_reservaciones()
        self.assertEqual([r.id for r in historial], ["R0002", "R0001"])

    def test_buscar_por_carne_sin_distinguir_mayusculas(self):
        datos_iniciales.sembrar_datos_iniciales()
        reservacion_repo.insertar_reservacion(
            Reservacion(id="R0001", carne_estudiante="A001234567", codigo_sala="S01",
                        fecha="2026-10-02", hora_inicio="09:00", duracion=1, cantidad_personas=2)
        )
        encontradas = reservacion_repo.buscar_por_carne("a001234567")
        self.assertEqual(len(encontradas), 1)

    # --- RF-14: series recurrentes ---

    def test_serie_recurrente_cancelar_futuras(self):
        datos_iniciales.sembrar_datos_iniciales()
        serie = "SER0001"
        ocurrencias = [
            Reservacion(id=f"R000{n}", carne_estudiante="A001234567", codigo_sala="S01",
                        fecha=f"2026-10-0{n}", hora_inicio="09:00", duracion=1, cantidad_personas=2,
                        serie_id=serie, numero_ocurrencia=n)
            for n in range(1, 4)
        ]
        reservacion_repo.insertar_serie(ocurrencias)
        self.assertEqual(len(reservacion_repo.listar_por_serie(serie)), 3)

        canceladas = reservacion_repo.cancelar_ocurrencias_futuras_serie(serie, "2026-10-02")
        self.assertEqual(canceladas, 2)
        estados = {r.numero_ocurrencia: r.estado for r in reservacion_repo.listar_por_serie(serie)}
        self.assertEqual(estados[1], "activa")
        self.assertEqual(estados[2], "cancelada")
        self.assertEqual(estados[3], "cancelada")

    # --- RF-17: auditoría ---

    def test_auditoria_registra_y_lista(self):
        auditoria_repo.registrar("creacion", "reservacion", "R0001", "Sala S01, 2026-10-02 09:00")
        auditoria_repo.registrar("cancelacion", "reservacion", "R0001")
        registros = auditoria_repo.listar(entidad="reservacion", identificador="R0001")
        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[0].tipo_accion, "creacion")
        self.assertEqual(registros[1].tipo_accion, "cancelacion")


if __name__ == "__main__":
    unittest.main()
