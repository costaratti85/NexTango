# MSG_010 — TASK_026: endpoints de cierre desplazados

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-18

Punto, nuevo bug geométrico — prioridad alta.

La línea de cierre de figuras de borde existe (1 segmento, eso está bien), pero sus vértices no coinciden con los nodos libres reales de la figura cortada. Los endpoints están desplazados.

Diferente a TASK_023/024 (que era nodos extras). Acá el problema es posición incorrecta de los endpoints.

Brief completo en `coordination/inbox/PUNTO_TASK_026_CLOSING_ENDPOINTS.md`.
