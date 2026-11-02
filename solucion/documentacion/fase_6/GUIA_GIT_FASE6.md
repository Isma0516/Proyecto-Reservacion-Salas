# Guía de Git y publicación de Fase 6 — Grupo 2

Este proyecto respeta las convenciones de la Fase 1. **No se realizaron cambios ni pushes al repositorio remoto del Grupo 2 desde esta entrega.**

## Política de ramas

- `main`: rama estable; no subir correcciones directas sin revisión.
- `develop`: rama de integración; aquí se integran los pull requests validados.
- `fix/BUG-XX-descripcion`: correcciones de defectos concretos.
- `feature/RF-XX-descripcion`: implementación de requisito funcional.
- `test/CP-XX-descripcion`: automatización y regresión.

## Antes de copiar archivos

1. Clonar el repositorio y cambiar a `develop`.
2. Guardar una copia y comprobar que no hay cambios pendientes (`git status`).
3. Comparar cada archivo del ZIP con la versión del repositorio. Esta entrega es una **reconstrucción autónoma** que preserva la organización y las APIs principales; NO es un commit incremental aplicado al historial remoto original.
4. Incorporar los archivos por módulos y revisar cuidadosamente las diferencias para no borrar trabajo posterior de otros integrantes.
5. Ejecutar `python -m unittest discover -s pruebas -p "test_*.py" -v` desde la raíz.
6. Abrir `python -m solucion.main`, verificar la navegación, registrar capturas reales.

## Comandos orientativos

```sh
git clone https://github.com/Isma0516/Proyecto-Reservacion-Salas.git
cd Proyecto-Reservacion-Salas
git checkout develop
git pull origin develop
git checkout -b fix/BUG-RN-02-formato-fecha
# Incorporar únicamente el cambio correspondiente.
python -m unittest discover -s pruebas -p "test_*.py" -v
git add solucion/negocio/validaciones.py pruebas/regresion/test_f6_defectos.py
git commit -m "fix(BUG-RN-02): rechazar fechas que incumplen AAAA-MM-DD"
git push -u origin fix/BUG-RN-02-formato-fecha
```

Luego crear un pull request hacia `develop`. Repetir la secuencia por cambios relacionados o por requisito. No efectuar `git push --force` ni añadir archivos `.db`.

## Mensajes sugeridos de commit

- `fix(BUG-RN-02): validar formato exacto de fecha`
- `fix(BUG-RN-01): prevenir doble reservación con fechas equivalentes`
- `fix(BUG-RN-03): validar horas HH:MM`
- `fix(BUG-RN-04): consultar carnés sin distinguir mayúsculas`
- `fix(BUG-RN-05): excluir reservas finalizadas del límite`
- `fix(BUG-RF02-01): exigir tres caracteres no espaciales en nombres`
- `fix(BUG-RF17-01): registrar creación y cancelación en auditoría`
- `feat(RF-11): habilitar edición y cambio de estado de estudiantes`
- `feat(RF-12): implementar gestión y validaciones de salas`
- `feat(RF-13): validar modificaciones de reservaciones`
- `feat(RF-14): crear y cancelar reservaciones recurrentes`
- `feat(RF-15): incorporar panel de ocupación y filtros`
- `feat(RF-16): exportar reportes CSV UTF-8`
- `feat(RF-17): integrar consulta de auditoría en la GUI`
- `feat(RNF-04): crear interfaz gráfica Tkinter`
- `test(CP-RN09-04): verificar conflicto con formatos de fecha`
- `test(CP-RF17): comprobar registro de auditoría`
- `docs(F6): consolidar resolución y matriz de trazabilidad`

## Modelo de descripción extensa de cada push / pull request

**Resumen:** cambio realizado, problema del requisito afectado y componente modificado.

**Requisitos / casos:** IDs oficiales `RF-XX`, `RN-XX`, `RNF-XX`, `CP-XX`, `BUG-XX`.

**Archivos:** rutas exactas modificadas y motivo.

**Validación:** comando ejecutado, versión de Python, total aprobado/fallido/bloqueado, evidencia asociada.

**Consideraciones:** diferencias con Fase 2, migración de datos, funcionalidades pendientes y riesgos.

**Commit:** hash real generado por Git; registrarlo en el documento F6 después de subir los cambios.
