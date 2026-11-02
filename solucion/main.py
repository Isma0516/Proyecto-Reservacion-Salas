
"""Punto de entrada del sistema de reservación de salas.

Permite iniciar la interfaz gráfica y preparar la base de datos SQLite.
"""

from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(
        0, str(Path(__file__).resolve().parent.parent)
    )

from solucion.datos.conexion import preparar_bd
from solucion.ui.aplicacion import Aplicacion


def main():
    """Inicializa la base de datos y abre la interfaz gráfica."""
    preparar_bd()

    aplicacion = Aplicacion()
    aplicacion.mainloop()


if __name__ == "__main__":
    main()

