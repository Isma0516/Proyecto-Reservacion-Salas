"""SQLite: apertura, integridad, migración del esquema y auditoría atómica."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from solucion.datos.excepciones import ErrorIntegridadDatos, ErrorPersistencia

_RUTA_POR_DEFECTO = str(Path(__file__).resolve().parents[1] / "reservaciones.db")
_ruta_bd_actual = _RUTA_POR_DEFECTO


def configurar_ruta_bd(ruta):
    """Establece la ruta de SQLite; útil para pruebas con BD aisladas."""
    global _ruta_bd_actual
    _ruta_bd_actual = os.fspath(ruta) if ruta is not None else _RUTA_POR_DEFECTO


def obtener_conexion():
    ruta = Path(_ruta_bd_actual)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(ruta), timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout=15000")
    return con



@contextmanager
def abrir_conexion():
    """Gestiona conexiones y traduce errores de SQLite."""
    con = None
    try:
        con = obtener_conexion()
        with con:
            yield con
    except sqlite3.IntegrityError as error:
        raise ErrorIntegridadDatos(str(error)) from error
    except sqlite3.Error as error:
        raise ErrorPersistencia(str(error)) from error
    finally:
        if con is not None:
            con.close()



def _columnas(con, nombre):
    return {f["name"] for f in con.execute(f"PRAGMA table_info({nombre})")}


def _migrar_estados_salas(con):
    """Convierte esquema F2 con CHECK fuera_servicio a la denominación oficial.
    Se deshabilitan FK solo durante la migración y se valida la integridad
    referencial antes de confirmar. No se eliminan reservaciones relacionadas.
    """
    sql = con.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='salas'").fetchone()
    if sql is None:
        return
    if "fuera_de_servicio" in sql["sql"]:
        # Este CHECK ya reconoce el estado nuevo; normalizar datos anteriores.
        con.execute("UPDATE salas SET estado='fuera_de_servicio' WHERE estado='fuera_servicio'")
        return
    # SQLite no permite modificar un CHECK con ALTER TABLE.
    # Esta operación se ejecuta antes de activar de nuevo las FK.
    con.execute("PRAGMA foreign_keys=OFF")
    try:
        with con:
            con.execute("CREATE TABLE salas_migradas (codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL, "
                        "capacidad INTEGER NOT NULL CHECK(capacidad > 0), "
                        "estado TEXT NOT NULL CHECK(estado IN ('disponible','fuera_de_servicio')))")
            con.execute("INSERT INTO salas_migradas SELECT codigo, nombre, capacidad, "
                        "CASE WHEN estado='fuera_servicio' THEN 'fuera_de_servicio' ELSE estado END FROM salas")
            con.execute("DROP TABLE salas")
            con.execute("ALTER TABLE salas_migradas RENAME TO salas")
            if con.execute("PRAGMA foreign_key_check").fetchall():
                raise sqlite3.IntegrityError("La migración afectaría la integridad referencial")
    finally:
        con.execute("PRAGMA foreign_keys=ON")


def inicializar_bd():
    """Crea o migra esquema sin borrar reservaciones ni reiniciar identificadores."""
    con = obtener_conexion()
    try:
        with con:
            con.execute("""CREATE TABLE IF NOT EXISTS estudiantes (
                carne TEXT PRIMARY KEY COLLATE NOCASE,
                nombre TEXT NOT NULL,
                correo TEXT NOT NULL,
                activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)))""")
            con.execute("""CREATE TABLE IF NOT EXISTS salas (
                codigo TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                capacidad INTEGER NOT NULL CHECK(capacidad > 0),
                estado TEXT NOT NULL CHECK(estado IN ('disponible', 'fuera_de_servicio')))""")
            con.execute("""CREATE TABLE IF NOT EXISTS reservaciones (
                id TEXT PRIMARY KEY,
                carne_estudiante TEXT NOT NULL,
                codigo_sala TEXT NOT NULL,
                fecha TEXT NOT NULL,
                hora_inicio TEXT NOT NULL,
                duracion INTEGER NOT NULL,
                cantidad_personas INTEGER NOT NULL,
                estado TEXT NOT NULL CHECK(estado IN ('activa','cancelada')),
                serie_id TEXT,
                numero_ocurrencia INTEGER,
                FOREIGN KEY(carne_estudiante) REFERENCES estudiantes(carne),
                FOREIGN KEY(codigo_sala) REFERENCES salas(codigo))""")
            con.execute("""CREATE TABLE IF NOT EXISTS auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_hora TEXT NOT NULL,
                tipo_accion TEXT NOT NULL,
                entidad TEXT NOT NULL,
                identificador TEXT NOT NULL,
                detalle TEXT)""")
            cols = _columnas(con, "reservaciones")
            for campo in ("serie_id", "numero_ocurrencia"):
                if campo not in cols:
                    tipo = "TEXT" if campo == "serie_id" else "INTEGER"
                    con.execute(f"ALTER TABLE reservaciones ADD COLUMN {campo} {tipo}")
        _migrar_estados_salas(con)
        with con:
            con.execute("CREATE INDEX IF NOT EXISTS idx_reservaciones_sala_fecha ON reservaciones(codigo_sala, fecha)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_reservaciones_carne ON reservaciones(carne_estudiante)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_reservaciones_serie ON reservaciones(serie_id)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha_hora)")
            # Los triggers garantizan que la escritura y auditoría formen una sola transacción.
            con.execute("""CREATE TRIGGER IF NOT EXISTS trg_f6_reserva_insert
                AFTER INSERT ON reservaciones BEGIN
                  INSERT INTO auditoria(fecha_hora,tipo_accion,entidad,identificador,detalle)
                  VALUES(strftime('%Y-%m-%d %H:%M:%S','now','localtime'),'creacion','reservacion',NEW.id,NULL);
                END""")
            con.execute("""CREATE TRIGGER IF NOT EXISTS trg_f6_reserva_cancelar
                AFTER UPDATE OF estado ON reservaciones
                WHEN OLD.estado='activa' AND NEW.estado='cancelada' BEGIN
                  INSERT INTO auditoria(fecha_hora,tipo_accion,entidad,identificador,detalle)
                  VALUES(strftime('%Y-%m-%d %H:%M:%S','now','localtime'),'cancelacion','reservacion',NEW.id,NULL);
                END""")
            con.execute("""CREATE TRIGGER IF NOT EXISTS trg_f6_reserva_editar
                AFTER UPDATE OF codigo_sala,fecha,hora_inicio,duracion,cantidad_personas ON reservaciones
                WHEN OLD.codigo_sala<>NEW.codigo_sala OR OLD.fecha<>NEW.fecha
                  OR OLD.hora_inicio<>NEW.hora_inicio OR OLD.duracion<>NEW.duracion
                  OR OLD.cantidad_personas<>NEW.cantidad_personas BEGIN
                  INSERT INTO auditoria(fecha_hora,tipo_accion,entidad,identificador,detalle)
                  VALUES(strftime('%Y-%m-%d %H:%M:%S','now','localtime'),'modificacion','reservacion',NEW.id,NULL);
                END""")
    finally:
        con.close()


def sembrar_datos_iniciales():
    """Inserta los tres estudiantes y las cinco salas sin duplicados."""
    con = obtener_conexion()
    try:
        with con:
            con.executemany("INSERT OR IGNORE INTO estudiantes(carne,nombre,correo,activo) VALUES(?,?,?,?)", [
                ("A001234567", "Andrea Solano", "andrea@universidad.ac.cr", 1),
                ("B009876543", "Carlos Méndez", "carlos@universidad.ac.cr", 1),
                ("C004567890", "Daniela Rojas", "daniela@universidad.ac.cr", 0),
            ])
            con.executemany("INSERT OR IGNORE INTO salas(codigo,nombre,capacidad,estado) VALUES(?,?,?,?)", [
                ("S01", "Sala Biblioteca 1", 4, "disponible"),
                ("S02", "Sala Biblioteca 2", 6, "disponible"),
                ("S03", "Laboratorio de estudio", 10, "disponible"),
                ("S04", "Sala multimedia", 8, "fuera_de_servicio"),
                ("S05", "Cubículo individual", 1, "disponible"),
            ])
    finally:
        con.close()


def preparar_bd():
    inicializar_bd()
    sembrar_datos_iniciales()
