"""Prueba de humo: crear ventana real y comprobar todas las pestañas."""
import tempfile
import unittest
from pathlib import Path
from solucion.datos import conexion


class TestInterfaz(unittest.TestCase):
    def test_iniciar_y_cerrar_pantallas(self):
        try:
            import tkinter as tk
            raiz=tk.Tk()
            raiz.withdraw()
            raiz.destroy()
        except tk.TclError:
            self.skipTest("Tk necesita servidor gráfico para esta prueba")
        with tempfile.TemporaryDirectory() as tmp:
            conexion.configurar_ruta_bd(Path(tmp)/"gui.db")
            try:
                conexion.preparar_bd()
                from solucion.ui.aplicacion import Aplicacion
                app=Aplicacion()
                app.update_idletasks()
                nombres=[app.tabs.tab(i,"text") for i in range(app.tabs.index("end"))]
                self.assertEqual(nombres,["Panel","Estudiantes","Salas","Reservaciones", "Recurrencias","Reportes","Auditoría"])
                self.assertTrue(app.winfo_exists())
                app.destroy()
            finally:
                conexion.configurar_ruta_bd(None)
