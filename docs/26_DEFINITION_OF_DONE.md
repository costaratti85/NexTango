# Definition of Done

Una tarea se considera terminada solo si:

1. Cumple el alcance escrito.
2. No rompe tests existentes.
3. Agrega test si modifica logica.
4. Mantiene separado dominio neutral de adaptadores.
5. No toca core ERPNext.
6. No toca Tango real sin sandbox y aprobacion.
7. No reemplaza Excel Pricing.
8. No implementa nesting ni CAM propio.
9. Deja trazabilidad clara de estados por pieza si afecta produccion.
10. Tiene reporte de agente.

Para MVP, el DoD minimo es:
`PYTHONPATH=apps/sistema_industrial pytest -q` pasa.
