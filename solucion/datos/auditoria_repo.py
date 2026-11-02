"""Registro de auditoría; no incluye funciones de edición ni eliminación."""
from solucion.datos.conexion import abrir_conexion


def registrar(tipo_accion, entidad, identificador, detalle=None):
    with abrir_conexion() as con:
        con.execute("INSERT INTO auditoria(fecha_hora,tipo_accion,entidad,identificador,detalle) "
                    "VALUES(strftime('%Y-%m-%d %H:%M:%S','now','localtime'),?,?,?,?)",
                    (tipo_accion,entidad,identificador,detalle))



class RegistroAuditoria(dict):
    """Registro accesible mediante claves o atributos."""

    def __getattr__(self, nombre):
        try:
            return self[nombre]
        except KeyError as error:
            raise AttributeError(nombre) from error


def listar(entidad=None, identificador=None):
    """Consulta la auditoría y permite filtrar sus registros."""
    consulta = "SELECT * FROM auditoria WHERE 1 = 1"
    parametros = []
    if entidad is not None:
        consulta += " AND entidad = ?"
        parametros.append(entidad)
    if identificador is not None:
        consulta += " AND identificador = ?"
        parametros.append(identificador)
    if entidad is not None or identificador is not None:
        consulta += " ORDER BY id ASC"
    else:
        consulta += " ORDER BY id DESC"
    with abrir_conexion() as con:
        return [
            RegistroAuditoria(dict(fila))
            for fila in con.execute(consulta, parametros)
        ]

