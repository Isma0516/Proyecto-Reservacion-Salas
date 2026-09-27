"""Reglas de negocio para estudiantes (RF-02 registro, RF-03 consulta)."""
from solucion.datos import estudiante_repo
from solucion.datos.excepciones import ErrorIntegridadDatos, ErrorPersistencia
from solucion.modelos.estudiante import Estudiante
from solucion.modelos.resultado import Resultado
from solucion.negocio import validaciones


def registrar_estudiante(carne: str, nombre: str, correo: str) -> Resultado:
    """RF-02: registra un estudiante únicamente si los datos son correctos."""
    if not validaciones.carne_valido(carne):
        return Resultado(False, "El carné debe tener exactamente diez caracteres alfanuméricos.")

    if not validaciones.texto_no_vacio(nombre):
        return Resultado(False, "El nombre completo es obligatorio.")

    if not validaciones.correo_valido(correo):
        return Resultado(False, "El correo ingresado no tiene un formato válido.")

    carne = carne.strip()
    nombre = nombre.strip()
    correo = correo.strip()

    try:
        if estudiante_repo.existe_carne(carne):
            return Resultado(False, f"Ya existe un estudiante registrado con el carné {carne}.")

        nuevo_estudiante = Estudiante(
            carne=carne,
            nombre=nombre,
            correo=correo,
            activo=True,
        )
        estudiante_repo.insertar_estudiante(nuevo_estudiante)
    except ErrorIntegridadDatos:
        return Resultado(False, f"Ya existe un estudiante registrado con el carné {carne}.")
    except ErrorPersistencia:
        return Resultado(False, "Ocurrió un error al guardar el estudiante. No se realizaron cambios.")

    return Resultado(True, f"Estudiante {carne} registrado exitosamente.", nuevo_estudiante)


def consultar_estudiantes() -> Resultado:
    """RF-03: lista todos los estudiantes, activos e inactivos."""
    try:
        estudiantes = estudiante_repo.listar_estudiantes()
    except ErrorPersistencia:
        return Resultado(False, "No fue posible consultar los estudiantes en este momento.")

    return Resultado(True, f"Se encontraron {len(estudiantes)} estudiante(s).", estudiantes)
