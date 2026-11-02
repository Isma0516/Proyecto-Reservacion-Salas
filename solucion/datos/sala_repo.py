"""Acceso a datos de salas."""
from solucion.datos.conexion import abrir_conexion
from solucion.modelos.sala import Sala


def _crear(f):
    return Sala(f["codigo"], f["nombre"], f["capacidad"], f["estado"]) if f else None


def obtener_sala(codigo):
    with abrir_conexion() as con:
        return _crear(con.execute("SELECT * FROM salas WHERE codigo=?",(codigo.strip().upper(),)).fetchone())


def listar_salas():
    with abrir_conexion() as con:
        return [_crear(f) for f in con.execute("SELECT * FROM salas ORDER BY codigo")]


def insertar_sala(sala):
    with abrir_conexion() as con:
        con.execute("INSERT INTO salas(codigo,nombre,capacidad,estado) VALUES(?,?,?,?)",(sala.codigo,sala.nombre,sala.capacidad,sala.estado))


def actualizar_sala(codigo,nombre,capacidad,estado):
    with abrir_conexion() as con:
        con.execute("UPDATE salas SET nombre=?,capacidad=?,estado=? WHERE codigo=?",(nombre,capacidad,estado,codigo))


def maximo_personas_futuras(codigo, fecha_desde, hora_actual):
    with abrir_conexion() as con:
        f=con.execute("""SELECT COALESCE(MAX(cantidad_personas),0) AS mayor
              FROM reservaciones WHERE codigo_sala=? AND estado='activa'
              AND (fecha>? OR (fecha=? AND time(hora_inicio,printf('+%d hours',duracion))>time(?)))""",
              (codigo,fecha_desde,fecha_desde,hora_actual)).fetchone()
        return f["mayor"]
