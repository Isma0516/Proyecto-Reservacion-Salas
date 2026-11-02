"""Punto de entrada: inicializa SQLite y abre la interfaz de escritorio."""
from solucion.datos.conexion import preparar_bd


def iniciar():
    preparar_bd()
    from solucion.ui.aplicacion import Aplicacion
    app=Aplicacion()
    app.mainloop()


if __name__=="__main__":
    iniciar()
