"""Flujos RF-02, RF-03 y RF-11."""
from solucion.datos import estudiante_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.estudiante import Estudiante
from solucion.modelos.resultado import Resultado
from solucion.negocio import validaciones as v


def registrar_estudiante(carne,nombre,correo):
    if not v.carne_valido(carne):
        return Resultado(False,"El carné debe tener exactamente diez caracteres alfanuméricos.")
    if not v.texto_no_vacio(nombre):
        return Resultado(False,"El nombre completo es obligatorio.")
    if not v.nombre_valido(nombre):
        return Resultado(False,"El nombre debe contener al menos tres caracteres no espaciales.")
    if not v.correo_valido(correo):
        return Resultado(False,"El correo electrónico tiene un formato inválido.")
    carne,nombre,correo=carne.strip(),nombre.strip(),correo.strip()
    try:
        if estudiante_repo.existe_carne(carne):
            return Resultado(False,"Ya existe un estudiante registrado con ese carné.")
        nuevo=Estudiante(carne,nombre,correo)
        estudiante_repo.insertar_estudiante(nuevo)
        return Resultado(True,"Estudiante registrado correctamente.",nuevo)
    except ErrorPersistencia:
        return Resultado(False,"No fue posible guardar al estudiante. No se realizaron cambios.")


def consultar_estudiantes():
    try:
        datos=estudiante_repo.listar_estudiantes()
        return Resultado(True, f"Se encontraron {len(datos)} estudiantes.",datos)
    except ErrorPersistencia:
        return Resultado(False,"No fue posible consultar estudiantes.")


def modificar_estudiante(carne,nombre,correo,activo):
    if not v.carne_valido(carne):
        return Resultado(False,"El carné no tiene un formato válido.")
    if not v.nombre_valido(nombre):
        return Resultado(False,"El nombre debe contener al menos tres caracteres no espaciales.")
    if not v.correo_valido(correo):
        return Resultado(False,"El correo electrónico tiene un formato inválido.")
    if type(activo) is not bool:
        return Resultado(False,"El estado del estudiante debe ser válido.")
    try:
        original=estudiante_repo.obtener_estudiante(carne)
        if original is None:
            return Resultado(False,"No existe el estudiante indicado.")
        estudiante_repo.actualizar_estudiante(original.carne,nombre.strip(),correo.strip(),activo)
        return Resultado(True,"Estudiante actualizado; su carné permanece sin cambios.")
    except ErrorPersistencia:
        return Resultado(False,"No fue posible modificar el estudiante. No se realizaron cambios.")


def intentar_cambiar_carne(carne_actual,carne_nuevo):
    return Resultado(False,"El carné es un identificador y no puede modificarse.")
