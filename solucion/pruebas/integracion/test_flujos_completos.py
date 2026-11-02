"""Pruebas integradas sobre una BD aislada de SQLite."""
import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from solucion.datos import conexion, auditoria_repo, reservacion_repo, sala_repo, estudiante_repo
from solucion.modelos.reservacion import Reservacion
from solucion.negocio import estudiantes, salas, reservaciones, reportes, panel


class TestFlujosIntegracion(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.ruta=Path(self.temp.name)/"base.db"
        conexion.configurar_ruta_bd(str(self.ruta))
        conexion.preparar_bd()
        self.f=(date.today()+timedelta(days=10)).isoformat()

    def tearDown(self):
        conexion.configurar_ruta_bd(None)
        self.temp.cleanup()

    def reservar(self,carne="A001234567",sala="S01",fecha=None,hora="10:00",duracion=1,personas=2):
        return reservaciones.crear_reservacion(carne,sala,fecha or self.f,hora,duracion,personas)

    def test_inicializacion_idempotente_sin_duplicados(self):
        conexion.preparar_bd();conexion.preparar_bd()
        self.assertEqual(len(estudiante_repo.listar_estudiantes()),3)
        self.assertEqual(len(sala_repo.listar_salas()),5)

    def test_registro_estudiante_y_estados(self):
        x=estudiantes.registrar_estudiante("D000000001","Ángela Pérez","angela@tec.ac.cr")
        self.assertTrue(x.exito,x.mensaje)
        self.assertFalse(estudiantes.registrar_estudiante("d000000001","Otro Nombre","otro@tec.ac.cr").exito)
        self.assertTrue(estudiantes.modificar_estudiante("d000000001","Ángela Úbeda","angela@tec.ac.cr",False).exito)
        self.assertFalse(self.reservar(carne="D000000001").exito)
        self.assertFalse(estudiantes.intentar_cambiar_carne("D000000001","Z000000001").exito)

    def test_rechazar_nombre_blanco_y_correo(self):
        self.assertFalse(estudiantes.registrar_estudiante("D000000002","   ","a@b.co").exito)
        self.assertFalse(estudiantes.registrar_estudiante("D000000002","Carlos Bueno","invalido").exito)

    def test_sala_codigo_protegido_capacidad_futura(self):
        self.assertTrue(salas.registrar_sala("S06","Sala Pequeña Güímar",5).exito)
        self.assertTrue(self.reservar(sala="S06",personas=5).exito)
        self.assertFalse(salas.modificar_sala("S06","Sala Pequeña",4,"disponible").exito)
        self.assertTrue(salas.modificar_sala("S06","Sala Pequeña",5,"fuera_de_servicio").exito)
        self.assertFalse(self.reservar(sala="S06").exito)
        self.assertFalse(salas.intentar_cambiar_codigo("S06","S07").exito)

    def test_sala_capacidad_invalida(self):
        self.assertFalse(salas.registrar_sala("S09","Sala",0).exito)
        self.assertFalse(salas.registrar_sala("S09","Sala",2.5).exito)

    def test_colision_parcial_consecutiva_y_cancelacion(self):
        primera=self.reservar(duracion=2)
        self.assertTrue(primera.exito)
        self.assertFalse(self.reservar(carne="B009876543",hora="11:00").exito)
        self.assertTrue(self.reservar(carne="B009876543",hora="12:00").exito)
        self.assertTrue(reservaciones.cancelar_reservacion(primera.datos.id).exito)
        self.assertTrue(self.reservar(hora="10:00").exito)
        self.assertFalse(reservaciones.cancelar_reservacion(primera.datos.id).exito)

    def test_modificar_conserva_id_y_previene_conflictos(self):
        a=self.reservar()
        b=self.reservar(carne="B009876543",hora="12:00")
        self.assertFalse(reservaciones.modificar_reservacion(b.datos.id,"S01",self.f,"10:00",1,2).exito)
        self.assertEqual(reservacion_repo.obtener_reservacion(b.datos.id).hora_inicio,"12:00")
        cambio=reservaciones.modificar_reservacion(b.datos.id,"S01",self.f,"13:00",1,2)
        self.assertTrue(cambio.exito,cambio.mensaje)
        self.assertEqual(cambio.datos.id,b.datos.id)
        self.assertTrue(any(a["tipo_accion"]=="modificacion" for a in auditoria_repo.listar()))
        self.assertTrue(reservaciones.cancelar_reservacion(b.datos.id).exito)
        self.assertFalse(reservaciones.modificar_reservacion(b.datos.id,"S01",self.f,"14:00",1,2).exito)

    def test_limite_reservas_y_no_reutilizar_id(self):
        ids=[]
        for i in range(3):
            r=self.reservar(fecha=(date.today()+timedelta(days=10+i)).isoformat());self.assertTrue(r.exito);ids.append(r.datos.id)
        self.assertFalse(self.reservar(fecha=(date.today()+timedelta(days=14)).isoformat()).exito)
        self.assertTrue(reservaciones.cancelar_reservacion(ids[0]).exito)
        nuevo=self.reservar(fecha=(date.today()+timedelta(days=14)).isoformat())
        self.assertTrue(nuevo.exito)
        self.assertEqual(nuevo.datos.id,"R0004")

    def test_recorrencia_dos_ocurrencias_y_cancelacion_futuras(self):
        r=reservaciones.crear_serie_semanal("A001234567","S01",self.f,"10:00",1,2,2)
        self.assertTrue(r.exito,r.mensaje)
        self.assertEqual(len(r.datos),2)
        self.assertEqual(len(reservacion_repo.listar_por_serie(r.datos[0].serie_id)),2)
        self.assertTrue(reservaciones.cancelar_ocurrencias_futuras(r.datos[0].id).exito)
        self.assertTrue(all(x.estado=="cancelada" for x in reservacion_repo.listar_por_serie(r.datos[0].serie_id)))

    def test_recurrencia_rechaza_conflicto_sin_escritura_parcial(self):
        self.assertTrue(self.reservar(carne="B009876543",fecha=(date.today()+timedelta(days=17)).isoformat()).exito)
        cantidad=len(reservacion_repo.listar_reservaciones())
        r=reservaciones.crear_serie_semanal("A001234567","S01",self.f,"10:00",1,1,2)
        self.assertFalse(r.exito)
        self.assertEqual(len(reservacion_repo.listar_reservaciones()),cantidad)

    def test_recurrencia_serie_8_conflicto_regla_11(self):
        r=reservaciones.crear_serie_semanal("A001234567","S01",self.f,"10:00",1,1,8)
        self.assertFalse(r.exito)
        self.assertIn("máximo de tres",r.mensaje)

    def test_busqueda_estudiante_inexistente_y_sin_reservas(self):
        self.assertFalse(reservaciones.buscar_reservaciones_estudiante("Z999999999").exito)
        r=reservaciones.buscar_reservaciones_estudiante("A001234567")
        self.assertTrue(r.exito);self.assertEqual(r.datos,[])
        self.reservar()
        self.assertEqual(len(reservaciones.buscar_reservaciones_estudiante("a001234567").datos),1)

    def test_disponibilidad_no_crea_archivos_ni_reservas(self):
        total=len(reservacion_repo.listar_reservaciones())
        r=reservaciones.consultar_disponibilidad("S01",self.f,"10:00",1)
        self.assertTrue(r.exito);self.assertTrue(r.datos)
        self.assertEqual(len(reservacion_repo.listar_reservaciones()),total)

    def test_export_csv_utf8_y_cancela_sin_archivos(self):
        self.assertTrue(estudiantes.registrar_estudiante("D000000001","Ángela Iñíguez","angela@tec.ac.cr").exito)
        self.assertTrue(salas.registrar_sala("S06","Sala Güímar Übeda",4).exito)
        self.assertTrue(self.reservar("D000000001","S06").exito)
        salida=Path(self.temp.name)/"reporte.csv"
        self.assertTrue(reportes.exportar_csv(self.f,self.f,salida).exito)
        with salida.open(encoding="utf-8",newline="") as f:
            filas=list(csv.reader(f))
        self.assertIn("Ángela Iñíguez",str(filas))
        self.assertIn("Güímar",str(filas))
        self.assertFalse(reportes.exportar_csv(self.f,self.f,"").exito)
        self.assertEqual(len(list(Path(self.temp.name).glob("*.tmp"))),0)

    def test_export_rango_erroneo(self):
        self.assertFalse(reportes.generar_reporte("2027-02-30",self.f).exito)
        self.assertFalse(reportes.generar_reporte("2029-01-01","2028-01-01").exito)

    def test_panel_filtros(self):
        self.assertTrue(self.reservar().exito)
        self.assertEqual(len(panel.filtrar(sala="S01",estado="activa").datos),1)
        self.assertEqual(len(panel.filtrar(sala="S02",estado="activa").datos),0)
        self.assertIn("ocupacion",panel.resumen().datos)

    def test_rollback_serie_id_duplicado(self):
        base=reservacion_repo.listar_reservaciones()
        a=Reservacion("R0100","A001234567","S01",self.f,"10:00",1,1)
        b=Reservacion("R0100","A001234567","S01",self.f,"11:00",1,1)
        from solucion.datos.excepciones import ErrorIntegridadDatos
        with self.assertRaises(ErrorIntegridadDatos):
            reservacion_repo.insertar_serie([a,b])
        self.assertEqual(base,reservacion_repo.listar_reservaciones())
        self.assertEqual(auditoria_repo.listar(),[])

    def test_reabrir_bd_y_continuidad_id(self):
        a=self.reservar()
        conexion.preparar_bd()
        b=self.reservar(hora="12:00")
        self.assertEqual(a.datos.id,"R0001")
        self.assertEqual(b.datos.id,"R0002")


if __name__=="__main__": unittest.main()
