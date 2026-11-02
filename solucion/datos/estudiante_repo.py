"""Acceso a datos de estudiantes."""
from solucion.datos.conexion import abrir_conexion
from solucion.modelos.estudiante import Estudiante


def _crear(f):
    return Estudiante(f["carne"], f["nombre"], f["correo"], bool(f["activo"])) if f else None


def obtener_estudiante(carne):
    with abrir_conexion() as con:
        return _crear(con.execute("SELECT * FROM estudiantes WHERE carne=? COLLATE NOCASE", (carne.strip(),)).fetchone())


def listar_estudiantes():
    with abrir_conexion() as con:
        return [_crear(f) for f in con.execute("SELECT * FROM estudiantes ORDER BY nombre COLLATE NOCASE")]


def insertar_estudiante(estudiante):
    with abrir_conexion() as con:
        con.execute("INSERT INTO estudiantes(carne,nombre,correo,activo) VALUES(?,?,?,?)", (estudiante.carne, estudiante.nombre, estudiante.correo, int(estudiante.activo)))



def actualizar_estudiante(carne, nombre=None, correo=None, activo=None):
    """Actualiza un estudiante conservando su carné.
    Admite un objeto Estudiante o los cuatro parámetros separados.
    """
    if isinstance(carne, Estudiante):
        estudiante = carne
        carne = estudiante.carne
        nombre = estudiante.nombre
        correo = estudiante.correo
        activo = estudiante.activo
    with abrir_conexion() as con:
        con.execute(
            """
            UPDATE estudiantes
            SET nombre = ?, correo = ?, activo = ?
            WHERE carne = ? COLLATE NOCASE
            """,
            (nombre, correo, int(activo), carne),
        )
  
def existe_carne(carne):
    """Comprueba si existe un carné, sin distinguir mayúsculas."""
    if not isinstance(carne, str):
        return False

    with abrir_conexion() as con:
        fila = con.execute(
            """
            SELECT 1
            FROM estudiantes
            WHERE carne = ? COLLATE NOCASE
            LIMIT 1
            """,
            (carne.strip(),),
        ).fetchone()

    return fila is not None

