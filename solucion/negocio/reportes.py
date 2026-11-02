"""RF-16: reportes de reservaciones en CSV UTF-8."""
import csv
from pathlib import Path
from solucion.datos import reservacion_repo, estudiante_repo, sala_repo
from solucion.datos.excepciones import ErrorPersistencia
from solucion.modelos.resultado import Resultado
from solucion.negocio.validaciones import convertir_fecha

ENCABEZADOS=("ID","Carné","Estudiante","Sala","Fecha","Hora inicio","Hora fin","Personas","Estado")


def generar_reporte(desde,hasta):
    i=convertir_fecha(desde); f=convertir_fecha(hasta)
    if i is None or f is None:return Resultado(False,"Debe indicar un rango válido de fechas AAAA-MM-DD.")
    if i>f:return Resultado(False,"La fecha final no puede ser anterior a la inicial.")
    try:
        registros=reservacion_repo.filtrar(fecha_desde=desde,fecha_hasta=hasta)
        filas=[]
        from solucion.negocio.validaciones import calcular_hora_fin
        for r in registros:
            estudiante=estudiante_repo.obtener_estudiante(r.carne_estudiante)
            sala=sala_repo.obtener_sala(r.codigo_sala)
            fin=calcular_hora_fin(r.hora_inicio,r.duracion)
            filas.append((r.id,r.carne_estudiante,estudiante.nombre if estudiante else "",
                sala.nombre if sala else r.codigo_sala,r.fecha,r.hora_inicio,fin.strftime("%H:%M") if fin else "",
                r.cantidad_personas,r.estado))
        return Resultado(True,f"Reporte generado con {len(filas)} registros.",filas)
    except ErrorPersistencia:return Resultado(False,"No fue posible generar el reporte.")


def exportar_csv(desde,hasta,ruta):
    """El archivo no se crea si el usuario cancela el selector de destino."""
    if not ruta:return Resultado(False,"Exportación cancelada; no se creó ningún archivo.")
    resultado=generar_reporte(desde,hasta)
    if not resultado.exito:return resultado
    destino=Path(ruta)
    temporal=destino.with_suffix(destino.suffix+".tmp")
    try:
        with temporal.open("w",encoding="utf-8",newline="") as f:
            salida=csv.writer(f)
            salida.writerow(ENCABEZADOS)
            salida.writerows(resultado.datos)
        temporal.replace(destino)
        return Resultado(True,f"Reporte exportado: {destino}",str(destino))
    except (OSError,UnicodeError):
        temporal.unlink(missing_ok=True)
        return Resultado(False,"No fue posible exportar el reporte.")
