# Verificación ejecutada — Fase 6

- Fecha: 2026-10-31.
- Plataforma: Linux, Python 3.13.5, Tkinter 8.6, SQLite.
- Comando: `xvfb-run -a python -m unittest discover -s pruebas -p 'test_*.py' -v`.
- Resultado final: **30 pruebas, 30 aprobadas, 0 fallidas, 0 bloqueadas en la suite propia**.
- Se incluyen los **ocho casos originalmente fallidos en Fase 5** en `pruebas/regresion/test_f6_defectos.py`.
- Se probó creación, migración y continuidad de SQLite, claves foráneas, rollback atómico, registros de auditoría y exportación CSV UTF-8.
- Se abrió y cerró una ventana real de Tkinter mediante pantalla virtual; se comprobaron sus siete pestañas.
- RNF-09: consulta de 5000 reservas con 1000 estudiantes completada en menos de dos segundos en este entorno.

**Alcance de la afirmación:** no representa la reejecución de los 109 casos originales del evaluador ni sustituye pruebas manuales en Windows. No se verificó la compatibilidad en Python 3.10. Queda pendiente integrar el código en el repositorio GitHub del Grupo 2 y ejecutar allí los casos cruzados originales.
