# Sistema de reservación de salas de estudio

Aplicación académica en Python para administrar estudiantes, salas y reservaciones de salas de estudio. La versión integrada incluye la capa de negocio, persistencia SQLite, datos iniciales, validaciones, manejo uniforme de errores y pruebas automatizadas. La interfaz gráfica y los requisitos avanzados que dependen de ella quedan fuera de esta versión candidata.

## Requisitos

- Python 3.10 o superior.
- No se requieren paquetes externos; la aplicación utiliza únicamente la biblioteca estándar de Python.

## Ejecución

Desde la raíz del repositorio:

```powershell
python -m solucion.main
```

La primera ejecución crea `solucion/reservaciones.db`, inicializa el esquema y carga los datos de ejemplo. Las ejecuciones posteriores reutilizan la misma base sin duplicar los datos iniciales.

## Pruebas

Para ejecutar toda la suite automatizada desde la raíz:

```powershell
python -m unittest discover -s pruebas -p "test_*.py" -v
```

Las pruebas usan bases SQLite temporales y no modifican `solucion/reservaciones.db`.

## Funcionalidad integrada

- Inicialización y migración segura del esquema SQLite.
- Carga idempotente de estudiantes y salas de ejemplo.
- Registro y consulta de estudiantes.
- Consulta de salas, incluidas las que están fuera de servicio.
- Creación, consulta, búsqueda, disponibilidad y cancelación de reservaciones.
- Validación de las reglas RN-01 a RN-13 para crear reservaciones.
- Operaciones de persistencia para actualizar estudiantes, salas y reservaciones.
- Soporte de persistencia para series recurrentes y auditoría.
- Traducción de errores SQLite a errores controlados de la aplicación.

## Estructura del proyecto

```text
documentacion/
  fase_1/          Especificación y planificación originales
  trazabilidad/    Artefactos de trazabilidad
evidencias/        Capturas, resultados y defectos
pruebas/
  unitarias/       Pruebas automatizadas
  integracion/     Pruebas de integración
  regresion/       Pruebas de regresión
  datos/           Datos de prueba
solucion/
  main.py          Punto de entrada de demostración
  datos/           Conexión SQLite y repositorios
  modelos/         Entidades y resultados de operación
  negocio/         Reglas, validaciones y casos de uso
  ui/              Interfaz gráfica pendiente
  recursos/        Recursos de la aplicación
```

## Datos iniciales

La carga inicial agrega cinco salas y tres estudiantes. Incluye una sala fuera de servicio y un estudiante inactivo para permitir la verificación de las reglas de negocio. La operación puede repetirse sin duplicar registros.

## Notas de alcance

Esta versión es una candidata de integración de la Fase 2. Aún no incluye la interfaz de escritorio, panel y filtros, exportación CSV ni los flujos completos de modificación y recurrencia en la capa de negocio. Los repositorios ya contienen parte del soporte de persistencia para continuar esas funciones en fases posteriores.
