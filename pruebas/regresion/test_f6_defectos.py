"""Regresión F6: los ocho fallos de la Fase 5 (siete defectos únicos)."""
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from solucion.datos import conexion, estudiante_repo, reservacion_repo, auditoria_repo
from solucion.modelos.reservacion import Reservacion
from solucion.negocio import estudiantes, reservaciones


class TestDefectosFase6(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        conexion.configurar_ruta_bd(str(Path(self.temp.name)/"test.db"))
        conexion.preparar_bd()
        self.futuro=(date.today()+timedelta(days=20)).isoformat()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.temp.cleanup()

    def test_CP_RN02_04_fecha_sin_ceros(self):
        resultado=reservaciones.crear_reservacion("A001234567","S01","2027-1-5","10:00",1,2)
        self.assertFalse(resultado.exito)
        self.assertEqual(len(reservacion_repo.listar_reservaciones()),0)

    def test_CP_RN09_04_misma_fecha_otro_formato(self):
        self.assertTrue(reservaciones.crear_reservacion("B009876543","S03","2027-01-05","10:00",1,2).exito)
        resultado=reservaciones.crear_reservacion("A001234567","S03","2027-1-5","10:00",1,2)
        self.assertFalse(resultado.exito)
        self.assertEqual(len(reservacion_repo.listar_reservaciones()),1)

    def test_CP_RN04_02_hora_sin_cero(self):
        r=reservaciones.crear_reservacion("A001234567","S01",self.futuro,"9:00",1,2)
        self.assertFalse(r.exito)
        self.assertEqual(len(reservacion_repo.listar_reservaciones()),0)

    def test_CP_RN01_04_carne_minusc(self):
        r=reservaciones.crear_reservacion("a001234567","S01",self.futuro,"10:00",1,2)
        self.assertTrue(r.exito,r.mensaje)
        self.assertEqual(r.datos.carne_estudiante,"A001234567")

    def test_CP_RN11_04_reserva_hoy_finalizada(self):
        ahora=datetime.now()
        hoy=ahora.date().isoformat()
        reservas=[Reservacion("R0001","A001234567","S01",hoy,"08:00",1,1),
                  Reservacion("R0002","A001234567","S01",(ahora.date()+timedelta(days=1)).isoformat(),"10:00",1,1),
                  Reservacion("R0003","A001234567","S01",(ahora.date()+timedelta(days=2)).isoformat(),"10:00",1,1)]
        for r in reservas:reservacion_repo.insertar_reservacion(r)
        class Reloj:
            @staticmethod
            def now():return datetime.combine(ahora.date(),datetime.strptime("14:30","%H:%M").time())
        with patch.object(reservaciones,"datetime",Reloj):
            r=reservaciones.crear_reservacion("A001234567","S01",(ahora.date()+timedelta(days=3)).isoformat(),"10:00",1,1)
        self.assertTrue(r.exito,r.mensaje)
        self.assertEqual(len(reservacion_repo.listar_reservaciones()),4)

    def test_CP_RF02_06_nombre_menor_tres_caracteres(self):
        r=estudiantes.registrar_estudiante("D001112222","A","laura@universidad.ac.cr")
        self.assertFalse(r.exito)
        self.assertIsNone(estudiante_repo.obtener_estudiante("D001112222"))

    def test_CP_RF17_01_auditoria_creacion(self):
        r=reservaciones.crear_reservacion("A001234567","S01",self.futuro,"10:00",1,1)
        self.assertTrue(r.exito,r.mensaje)
        logs=auditoria_repo.listar()
        self.assertTrue(any(x["tipo_accion"]=="creacion" and x["identificador"]==r.datos.id for x in logs))

    def test_CP_RF17_03_auditoria_cancelacion(self):
        r=reservaciones.crear_reservacion("A001234567","S01",self.futuro,"10:00",1,1)
        self.assertTrue(reservaciones.cancelar_reservacion(r.datos.id).exito)
        acciones=[x["tipo_accion"] for x in auditoria_repo.listar()]
        self.assertIn("creacion",acciones)
        self.assertIn("cancelacion",acciones)

    def test_RNF06_auditoria_sin_cambios_por_rechazo(self):
        r=reservaciones.crear_reservacion("A001234567","S04",self.futuro,"10:00",1,1)
        self.assertFalse(r.exito)
        self.assertEqual(auditoria_repo.listar(),[])


if __name__=="__main__":unittest.main()
