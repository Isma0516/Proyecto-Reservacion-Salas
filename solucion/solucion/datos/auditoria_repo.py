"""Registro de auditoría; no incluye funciones de edición ni eliminación."""
from solucion.datos.conexion import abrir_conexion


def registrar(tipo_accion, entidad, identificador, detalle=None):
    with abrir_conexion() as con:
        con.execute("INSERT INTO auditoria(fecha_hora,tipo_accion,entidad,identificador,detalle) "
                    "VALUES(strftime('%Y-%m-%d %H:%M:%S','now','localtime'),?,?,?,?)",
                    (tipo_accion,entidad,identificador,detalle))


def listar():
    with abrir_conexion() as con:
        return [dict(r) for r in con.execute("SELECT * FROM auditoria ORDER BY id DESC")]
