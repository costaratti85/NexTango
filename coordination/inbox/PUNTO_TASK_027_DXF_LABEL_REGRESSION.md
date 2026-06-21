# PUNTO_TASK_027 — Regresión TASK_025: etiqueta DXF sin cambios en producción

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta

---

## Síntoma

TASK_025 se reportó como completada, pero Constantino verifica que en los DXF generados hoy:

1. **La justificación sigue siendo izquierda** — el texto se monta sobre la figura. Tenía que ser derecha.
2. **El nombre del material sigue siendo el largo** — aparece `"chapa doble decapada 0.9mm"` en lugar del formato abreviado (`N°20`).

## Pedido

Investigar por qué los cambios de TASK_025 no están llegando al DXF que genera la app en producción. Puede ser que el código modificado no sea el que ejecuta el flujo real, o que haya un problema de importación, caché, o ruta incorrecta.

Corregirlo y verificar con un DXF generado desde la app (no solo tests).

## Reporte

`coordination/reports/PUNTO_TASK_027_REPORT.md` y mensaje en `coordination/channel/Nova/`.
