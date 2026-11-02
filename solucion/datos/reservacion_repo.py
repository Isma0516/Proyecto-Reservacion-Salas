"""Consultas y persistencia de reservaciones, incluyendo recurrencia."""
from datetime import date, datetime
from solucion.datos.conexion import abrir_conexion
from solucion.modelos.reservacion import Reservacion, ESTADO_ACTIVA, ESTADO_CANCELADA


def _fila_a_reservacion(f):
    if f is None:
        return None
    return Reservacion(f["id"],f["carne_estudiante"],f["codigo_sala"],f["fecha"],
        f["hora_inicio"],f["duracion"],f["cantidad_personas"],f["estado"],
        f["serie_id"] if "serie_id" in f.keys() else None,
        f["numero_ocurrencia"] if "numero_ocurrencia" in f.keys() else None)


def _registro(r):
    return (r.id,r.carne_estudiante,r.codigo_sala,r.fecha,r.hora_inicio,r.duracion,
            r.cantidad_personas,r.estado,r.serie_id,r.numero_ocurrencia)


def _insertar(con, reservacion):
    con.execute("""INSERT INTO reservaciones
      (id,carne_estudiante,codigo_sala,fecha,hora_inicio,duracion,cantidad_personas,estado,serie_id,numero_ocurrencia)
      VALUES(?,?,?,?,?,?,?,?,?,?)""", _registro(reservacion))


def insertar_reservacion(reservacion):
    with abrir_conexion() as con:
        _insertar(con,reservacion)


def insertar_serie(reservaciones):
    with abrir_conexion() as con:
        for r in reservaciones:
            _insertar(con,r)


def obtener_reservacion(identificador):
    with abrir_conexion() as con:
        return _fila_a_reservacion(con.execute("SELECT * FROM reservaciones WHERE id=?",(identificador,)).fetchone())


def listar_reservaciones():
    with abrir_conexion() as con:
        return [_fila_a_reservacion(f) for f in con.execute("SELECT * FROM reservaciones ORDER BY fecha,hora_inicio,id")]


def buscar_por_carne(carne):
    with abrir_conexion() as con:
        return [_fila_a_reservacion(f) for f in con.execute("SELECT * FROM reservaciones WHERE carne_estudiante=? COLLATE NOCASE ORDER BY fecha,hora_inicio,id",(carne,))]


def listar_activas_por_sala_fecha(codigo_sala, fecha):
    with abrir_conexion() as con:
        return [_fila_a_reservacion(f) for f in con.execute("SELECT * FROM reservaciones WHERE codigo_sala=? AND fecha=? AND estado='activa'",(codigo_sala,fecha))]


def contar_activas_estudiante_desde(carne, fecha_desde, hora_actual=None):
    """RN-11: fecha = hoy exige comprobar hora de fin, no solo fecha."""
    with abrir_conexion() as con:
        if hora_actual is None:
            fila=con.execute("""SELECT COUNT(*) AS n FROM reservaciones WHERE
                 carne_estudiante=? COLLATE NOCASE AND estado='activa' AND fecha>=?""",
                 (carne,fecha_desde)).fetchone()
        else:
            fila=con.execute("""SELECT COUNT(*) AS n FROM reservaciones WHERE
                 carne_estudiante=? COLLATE NOCASE AND estado='activa'
                 AND (fecha>? OR (fecha=? AND time(hora_inicio,printf('+%d hours',duracion))>time(?)))""",
                 (carne,fecha_desde,fecha_desde,hora_actual)).fetchone()
        return fila["n"]


def _siguiente_id(con):
    fila=con.execute("SELECT MAX(CAST(SUBSTR(id,2) AS INTEGER)) AS mayor FROM reservaciones").fetchone()
    return f"R{(fila['mayor'] or 0)+1:04d}"


def generar_siguiente_id():
    with abrir_conexion() as con:
        return _siguiente_id(con)


def crear_atomica(reservacion):
    """ID asignado con reserva de escritura, sin colisiones entre clientes."""
    with abrir_conexion() as con:
        con.execute("BEGIN IMMEDIATE")
        reservacion.id=_siguiente_id(con)
        _insertar(con,reservacion)
        return reservacion


def crear_serie_atomica(reservaciones):
    with abrir_conexion() as con:
        con.execute("BEGIN IMMEDIATE")
        primero=int(_siguiente_id(con)[1:])
        for i,r in enumerate(reservaciones):
            r.id=f"R{primero+i:04d}"
            r.serie_id=f"SER-{primero:04d}"
            r.numero_ocurrencia=i+1
            _insertar(con,r)
        return reservaciones


def actualizar_reservacion(reservacion):
    with abrir_conexion() as con:
        con.execute("""UPDATE reservaciones SET codigo_sala=?,fecha=?,hora_inicio=?,duracion=?,cantidad_personas=?
               WHERE id=?""",(reservacion.codigo_sala,reservacion.fecha,reservacion.hora_inicio,
                                  reservacion.duracion,reservacion.cantidad_personas,reservacion.id))


def cancelar_reservacion_bd(identificador):
    with abrir_conexion() as con:
        con.execute("UPDATE reservaciones SET estado='cancelada' WHERE id=? AND estado='activa'",(identificador,))


def listar_por_serie(serie):
    with abrir_conexion() as con:
        return [_fila_a_reservacion(f) for f in con.execute("SELECT * FROM reservaciones WHERE serie_id=? ORDER BY numero_ocurrencia",(serie,))]


def cancelar_ocurrencias_futuras_serie(serie, desde_fecha):
    with abrir_conexion() as con:
        cur=con.execute("""UPDATE reservaciones SET estado='cancelada' WHERE serie_id=? AND estado='activa'
                    AND fecha>=?""",(serie,desde_fecha))
        return cur.rowcount


def filtrar(fecha_desde=None, fecha_hasta=None, sala=None, estado=None, carne=None):
    criterios=[]; args=[]
    for campo,valor in (("fecha >=", fecha_desde),("fecha <=", fecha_hasta),
                        ("codigo_sala =",sala),("estado =",estado)):
        if valor:
            criterios.append(campo+" ?");args.append(valor)
    if carne:
        criterios.append("carne_estudiante = ? COLLATE NOCASE");args.append(carne)
    where=" WHERE "+" AND ".join(criterios) if criterios else ""
    with abrir_conexion() as con:
        return [_fila_a_reservacion(f) for f in con.execute(
            "SELECT * FROM reservaciones"+where+" ORDER BY fecha,hora_inicio,id",args)]


def resumen_panel():
    hoy=date.today().isoformat(); actual=datetime.now().strftime("%H:%M:%S")
    with abrir_conexion() as con:
        total=con.execute("SELECT COUNT(*) AS n FROM reservaciones WHERE fecha=? AND estado='activa'",(hoy,)).fetchone()["n"]
        proximas=[_fila_a_reservacion(f) for f in con.execute("""SELECT * FROM reservaciones
          WHERE estado='activa' AND (fecha>? OR (fecha=? AND time(hora_inicio,printf('+%d hours',duracion))>time(?)))
          ORDER BY fecha,hora_inicio LIMIT 15""",(hoy,hoy,actual))]
        ocupacion=[dict(f) for f in con.execute("""SELECT s.codigo,s.nombre,s.capacidad,
          COUNT(r.id) AS reservas_hoy FROM salas s LEFT JOIN reservaciones r
          ON r.codigo_sala=s.codigo AND r.fecha=? AND r.estado='activa'
          GROUP BY s.codigo ORDER BY s.codigo""",(hoy,))]
        return {"reservas_hoy":total,"proximas":proximas,"ocupacion":ocupacion}
