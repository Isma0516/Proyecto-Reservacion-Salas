"""
Punto de entrada de demostración de la capa de lógica + persistencia
(todavía sin interfaz gráfica).

Ejecutar desde la raíz del proyecto con:
    python -m solucion.main
"""
from datetime import date, timedelta

from solucion.datos import conexion, datos_iniciales
from solucion.negocio import estudiantes, salas, reservaciones


def mostrar(resultado, titulo):
    print(f"\n--- {titulo} ---")
    print(f"Éxito: {resultado.exito} | Mensaje: {resultado.mensaje}")
    if resultado.datos is not None:
        print(f"Datos: {resultado.datos}")


def main():
    conexion.inicializar_bd()  # RF-01
    datos_iniciales.sembrar_datos_iniciales()  # RF-01: salas y estudiantes de ejemplo (secciones 5.2 y 10)

    mostrar(
        estudiantes.registrar_estudiante("EST0000001", "Juan Diego Quirós", "juan@estudiantec.cr"),
        "RF-02 Registrar estudiante",
    )
    mostrar(salas.consultar_salas(), "RF-04 Consultar salas")

    manana = (date.today() + timedelta(days=1)).isoformat()

    mostrar(
        reservaciones.consultar_disponibilidad("S01", manana, "10:00", 1),
        "RF-08 Consultar disponibilidad",
    )

    resultado_creacion = reservaciones.crear_reservacion("EST0000001", "S01", manana, "10:00", 1, 2)
    mostrar(resultado_creacion, "RF-05 Crear reservación")

    if resultado_creacion.exito:
        id_creada = resultado_creacion.datos.id
        mostrar(
            reservaciones.cancelar_reservacion(id_creada),
            "RF-09 Cancelar reservación",
        )


if __name__ == "__main__":
    main()
