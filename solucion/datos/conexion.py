"""
Manejo de la conexión SQLite y creación del esquema (RF-01), incluyendo las
tablas necesarias para RF-14 (recurrencia, vía columnas de serie en
reservaciones) y RF-17 (auditoría).

La base de datos se ubica junto al paquete `solucion`, usando una ruta
relativa al propio archivo, para que la aplicación pueda ejecutarse en
otra computadora sin depender de rutas personales (RNF-03).
"""
import os
import sqlite3
from contextlib import contextmanager

from solucion.datos.excepciones import ErrorIntegridadDatos, ErrorPersistencia

_RUTA_BD_POR_DEFECTO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "reservaciones.db",
)

# Ruta activa; puede cambiarse (por ejemplo, en las pruebas automatizadas)
# mediante configurar_ruta_bd() para no afectar la base de datos real.
_ruta_bd_actual = _RUTA_BD_POR_DEFECTO


def configurar_ruta_bd(ruta: str) -> None:
    """Permite apuntar a otra base de datos (usado en pruebas con archivos temporales)."""
    global _ruta_bd_actual
    _ruta_bd_actual = ruta


def obtener_conexion() -> sqlite3.Connection:
    conexion = sqlite3.connect(_ruta_bd_actual)
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.row_factory = sqlite3.Row
    return conexion


@contextmanager
def abrir_conexion():
    """Open a database connection and translate SQLite errors.

    Repositories use this context manager so SQLite-specific exceptions do not
    escape the ``datos`` package. The business layer therefore depends on the
    persistence abstraction, not directly on ``sqlite3``.
    """
    conexion = None
    try:
        conexion = obtener_conexion()
        yield conexion
    except sqlite3.IntegrityError as exc:
        raise ErrorIntegridadDatos(str(exc)) from exc
    except sqlite3.Error as exc:
        raise ErrorPersistencia(str(exc)) from exc
    finally:
        if conexion is not None:
            conexion.close()


def _columnas_de(conexion: sqlite3.Connection, tabla: str) -> set:
    filas = conexion.execute(f"PRAGMA table_info({tabla})").fetchall()
    return {fila["name"] for fila in filas}


def _migrar_columnas_faltantes(conexion: sqlite3.Connection) -> None:
    """
    Agrega columnas nuevas a bases de datos creadas con una versión anterior
    del esquema, sin tocar los datos existentes (RNF-06: integridad).
    SQLite no soporta "ADD COLUMN IF NOT EXISTS", así que se revisa primero
    con PRAGMA table_info.
    """
    columnas_reservaciones = _columnas_de(conexion, "reservaciones")
    if "serie_id" not in columnas_reservaciones:
        conexion.execute("ALTER TABLE reservaciones ADD COLUMN serie_id TEXT")
    if "numero_ocurrencia" not in columnas_reservaciones:
        conexion.execute("ALTER TABLE reservaciones ADD COLUMN numero_ocurrencia INTEGER")


def inicializar_bd() -> None:
    """
    RF-01: inicializa el esquema de la base de datos SQLite.
    Es segura de ejecutar varias veces (usa CREATE TABLE IF NOT EXISTS y
    migra columnas faltantes), de forma que reabrir la aplicación no
    duplique ni pierda información.
    """
    conexion = obtener_conexion()
    try:
        with conexion:
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS estudiantes (
                    carne TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    correo TEXT NOT NULL,
                    activo INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS salas (
                    codigo TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    capacidad INTEGER NOT NULL,
                    estado TEXT NOT NULL CHECK (estado IN ('disponible', 'fuera_servicio'))
                )
                """
            )
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS reservaciones (
                    id TEXT PRIMARY KEY,
                    carne_estudiante TEXT NOT NULL,
                    codigo_sala TEXT NOT NULL,
                    fecha TEXT NOT NULL,
                    hora_inicio TEXT NOT NULL,
                    duracion INTEGER NOT NULL,
                    cantidad_personas INTEGER NOT NULL,
                    estado TEXT NOT NULL CHECK (estado IN ('activa', 'cancelada')),
                    serie_id TEXT,
                    numero_ocurrencia INTEGER,
                    FOREIGN KEY (carne_estudiante) REFERENCES estudiantes (carne),
                    FOREIGN KEY (codigo_sala) REFERENCES salas (codigo)
                )
                """
            )
            # RF-17: historial de auditoría. Es de solo-inserción (append-only)
            # desde la interfaz; no se expone ninguna operación de edición o
            # borrado sobre esta tabla a propósito.
            conexion.execute(
                """
                CREATE TABLE IF NOT EXISTS auditoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_hora TEXT NOT NULL,
                    tipo_accion TEXT NOT NULL,
                    entidad TEXT NOT NULL,
                    identificador TEXT NOT NULL,
                    detalle TEXT
                )
                """
            )
            # Las columnas deben existir (migradas si es una BD antigua) antes
            # de indexarlas.
            _migrar_columnas_faltantes(conexion)
            conexion.execute(
                "CREATE INDEX IF NOT EXISTS idx_reservaciones_sala_fecha "
                "ON reservaciones (codigo_sala, fecha)"
            )
            conexion.execute(
                "CREATE INDEX IF NOT EXISTS idx_reservaciones_carne "
                "ON reservaciones (carne_estudiante)"
            )
            conexion.execute(
                "CREATE INDEX IF NOT EXISTS idx_reservaciones_serie "
                "ON reservaciones (serie_id)"
            )
    finally:
        conexion.close()
        
