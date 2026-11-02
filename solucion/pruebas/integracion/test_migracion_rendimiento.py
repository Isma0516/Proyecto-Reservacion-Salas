"""Migración de la BD F2 y rendimiento RNF-09 con volumen exigido."""
import sqlite3
import tempfile
import time
import unittest
from datetime import date, timedelta
from pathlib import Path
from solucion.datos import conexion
from solucion.datos import reservacion_repo


class TestMigracionRendimiento(unittest.TestCase):
    def tearDown(self):
        conexion.configurar_ruta_bd(None)

    def test_migracion_base_f2_conserva_reserva_y_fks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"legacy.db"
            db=sqlite3.connect(p)
            db.executescript("""
              CREATE TABLE estudiantes(carne TEXT PRIMARY KEY,nombre TEXT,correo TEXT,activo INTEGER);
              CREATE TABLE salas(codigo TEXT PRIMARY KEY,nombre TEXT,capacidad INTEGER,
                estado TEXT CHECK(estado IN ('disponible','fuera_servicio')));
              CREATE TABLE reservaciones(id TEXT PRIMARY KEY,carne_estudiante TEXT REFERENCES estudiantes(carne),
                codigo_sala TEXT REFERENCES salas(codigo),fecha TEXT,hora_inicio TEXT,
                duracion INTEGER,cantidad_personas INTEGER,estado TEXT);
              INSERT INTO estudiantes VALUES('A001234567','Andrea','a@b.co',1);
              INSERT INTO salas VALUES('S04','Sala multimedia',8,'fuera_servicio');
              INSERT INTO reservaciones VALUES('R0099','A001234567','S04','2027-01-05','10:00',1,1,'cancelada');
            """)
            db.close()
            conexion.configurar_ruta_bd(p)
            conexion.preparar_bd()
            con=conexion.obtener_conexion()
            try:
                fila=con.execute("SELECT estado FROM salas WHERE codigo='S04'").fetchone()
                self.assertEqual(fila["estado"],"fuera_de_servicio")
                self.assertIsNotNone(con.execute("SELECT id FROM reservaciones WHERE id='R0099'").fetchone())
                self.assertFalse(con.execute("PRAGMA foreign_key_check").fetchall())
            finally:con.close()

    def test_rnf09_consultas_con_mil_estudiantes_cinco_mil_reservas(self):
        with tempfile.TemporaryDirectory() as d:
            conexion.configurar_ruta_bd(Path(d)/"carga.db")
            conexion.preparar_bd()
            fecha=(date.today()+timedelta(days=180)).isoformat()
            con=conexion.obtener_conexion()
            try:
                with con:
                    con.executemany("INSERT INTO estudiantes VALUES(?,?,?,1)",[
                        (f"T{i:09d}",f"Estudiante {i}",f"est{i}@universidad.ac.cr") for i in range(1000)])
                    con.executemany("""INSERT INTO reservaciones
                      (id,carne_estudiante,codigo_sala,fecha,hora_inicio,duracion,cantidad_personas,estado)
                      VALUES(?,?,?,?,?,?,?,?)""",[(f"R{i+1000:04d}",f"T{i%1000:09d}","S01",fecha,
                          f"{8+(i%12):02d}:00",1,1,"cancelada") for i in range(5000)])
            finally:con.close()
            inicio=time.perf_counter()
            resultados=reservacion_repo.filtrar(fecha_desde=fecha,fecha_hasta=fecha)
            tiempo=time.perf_counter()-inicio
            self.assertEqual(len(resultados),5000)
            self.assertLess(tiempo,2.0,f"Consulta de 5000 reservaciones: {tiempo:.3f} s")


if __name__=="__main__":unittest.main()
