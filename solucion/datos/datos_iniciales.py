"""
Siembra los datos iniciales exigidos por el enunciado (secciones 5.2 y 10):
las 5 salas y los 3 estudiantes de ejemplo.

RF-01 exige que "las salas iniciales queden disponibles desde la primera
ejecución" y que, si la base de datos ya existe, "se utiliza sin duplicar
registros". Por eso cada inserción aquí se hace únicamente si el registro
todavía no existe: llamar a sembrar_datos_iniciales() en cada arranque de
la aplicación es seguro y nunca genera duplicados ni sobrescribe cambios
que la persona usuaria haya hecho después (por ejemplo, si ya inactivó a
un estudiante o puso una sala fuera de servicio).
"""
from solucion.datos import estudiante_repo, sala_repo
from solucion.modelos.estudiante import Estudiante
from solucion.modelos.sala import Sala, ESTADO_DISPONIBLE, ESTADO_FUERA_SERVICIO

# Sección 5.2 del enunciado
SALAS_INICIALES = [
    Sala(codigo="S01", nombre="Sala Biblioteca 1", capacidad=4, estado=ESTADO_DISPONIBLE),
    Sala(codigo="S02", nombre="Sala Biblioteca 2", capacidad=6, estado=ESTADO_DISPONIBLE),
    Sala(codigo="S03", nombre="Laboratorio de estudio", capacidad=10, estado=ESTADO_DISPONIBLE),
    Sala(codigo="S04", nombre="Sala multimedia", capacidad=8, estado=ESTADO_FUERA_SERVICIO),
    Sala(codigo="S05", nombre="Cubículo individual", capacidad=1, estado=ESTADO_DISPONIBLE),
]

# Sección 10 del enunciado
ESTUDIANTES_INICIALES = [
    Estudiante(carne="A001234567", nombre="Andrea Solano", correo="andrea@universidad.ac.cr", activo=True),
    Estudiante(carne="B009876543", nombre="Carlos Méndez", correo="carlos@universidad.ac.cr", activo=True),
    Estudiante(carne="C004567890", nombre="Daniela Rojas", correo="daniela@universidad.ac.cr", activo=False),
]


def sembrar_datos_iniciales() -> None:
    """
    Inserta las salas y estudiantes iniciales si todavía no existen.
    Debe llamarse después de conexion.inicializar_bd().
    """
    for sala in SALAS_INICIALES:
        if sala_repo.obtener_sala(sala.codigo) is None:
            sala_repo.insertar_sala(sala)

    for estudiante in ESTUDIANTES_INICIALES:
        if not estudiante_repo.existe_carne(estudiante.carne):
            estudiante_repo.insertar_estudiante(estudiante)
            
