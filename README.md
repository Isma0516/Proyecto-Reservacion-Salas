# Proyecto de reservación de salas — Fase 6, Grupo 2

Aplicación de escritorio Python con interfaz Tkinter, persistencia SQLite y pruebas automatizadas. Se conserva la separación entre **UI**, **negocio**, **datos** y **modelos** de la Fase 2.

## Requisitos

- Python **3.10 o superior** con Tkinter disponible. SQLite y unittest forman parte de Python.
- Windows: instalar Python desde python.org con Tk/Tcl (instalación estándar). En Linux, instalar el paquete de Tkinter del sistema si no está incluido.
- No se requieren dependencias de `pip`.

## Ejecutar

Desde la **raíz del proyecto**:

```sh
python -m solucion.main
```

El primer inicio crea `solucion/reservaciones.db`, sus tablas, índices y datos iniciales, y abre la interfaz gráfica. Si la BD ya existe, conserva los datos y aplica migraciones compatibles con el esquema de Fase 2. No se debe subir el archivo `.db` a GitHub; está en `.gitignore`.

## Pantallas

1. **Panel:** próximas reservas, ocupación por sala y filtros combinables.
2. **Estudiantes:** registro, listado, edición y activación/inactivación. Seleccionar una fila y luego guardar cambios.
3. **Salas:** alta, listado, edición, estado y restricciones de capacidad.
4. **Reservaciones:** crear, consultar disponibilidad, editar, cancelar, buscar por carné e historial.
5. **Recurrencias:** crear serie semanal (2–8 ocurrencias), cancelar una ocurrencia o desde cierta ocurrencia de la serie.
6. **Reportes:** previsualización por fechas y exportación CSV UTF-8.
7. **Auditoría:** historial de solo lectura, actualizado automáticamente al crear/modificar/cancelar reservas.

**Regla RN-11 (interpretación conservadora):** cada ocurrencia recurrente cuenta como una reserva activa; el máximo de tres presentes o futuras se aplica también a series. Por tanto, series de 4–8 ocurrencias no podrán quedar todas activas a la vez para un estudiante; este conflicto entre RF-14 y RN-11 debe aclararse con el profesor antes de cambiar la regla.

## Probar

```sh
python -m unittest discover -s pruebas -p "test_*.py" -v
```

Las pruebas crean bases SQLite temporales independientes; no afectan datos reales. La suite incluye los casos fallidos de la Fase 5 y escenarios de integración.

## Base de datos y restauración de datos iniciales

Las tablas son `estudiantes`, `salas`, `reservaciones` y `auditoria`. Para comenzar **desde cero**, cerrar la aplicación, copiar o respaldar el archivo `solucion/reservaciones.db` y luego eliminarlo; al iniciar se regeneran las tablas y datos semilla. **No elimine la BD si requiere conservar reservaciones reales.**

La columna `activo INTEGER` de Fase 2 se mantiene como `0/1` con mapeo `inactivo/activo` en UI y negocio. El valor de sala `fuera_servicio` se migra a `fuera_de_servicio`. Los triggers de auditoría registran sólo operaciones de base confirmadas y no registran validaciones rechazadas.

## Git: convención de Fase 1

- Rama de integración `develop`, rama estable `main`.
- Defectos: `fix/BUG-RN-02-formato-fecha`, commit `fix(BUG-RN-02): exigir fecha AAAA-MM-DD`.
- Funcionalidades: `feature/RF-16-reportes-csv`, commit `feat(RF-16): generar y exportar reportes CSV`.
- Pruebas: `test/CP-RN02-04-formato-fecha`, commit `test(CP-RN02-04): verificar rechazo de fecha sin ceros`.
- Documentación: `docs(F6): actualizar registro y matriz de trazabilidad`.
- Revisar, ejecutar pruebas, crear commits descriptivos y subir la rama; integrar a `develop` mediante PR.

Los commits y pushes **no se han ejecutado remotamente desde esta entrega**; la ruta `documentacion/fase_6/` contiene la propuesta de registro que debe actualizarse con los hashes reales de Git.
