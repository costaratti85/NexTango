# CYBELEC_TASK_001 — REPORT

**De:** Cybelec · **Fecha:** 2026-07-01 · **Estado:** ✅ Completa (+ extras de la noche)

Detalle completo en `coordination/channel/Nova/MSG_040_CYBELEC_task001_done.md`.

## Resumen

Todo en `research/cybelec/plegado_app/index.html`, verificado en navegador:

1. **Fix 1 — Zoom centrado en el pliegue**: clip ±160mm (`MACHINE_CLIP`) centrado en el vértice activo como vista por defecto de Operación; botón "🔍 Zoom pliegue" (default ON) alterna con vista pieza-completa (pedido directo de Constantino integrado). Con ala de 600mm la zona de pliegue pasó de ilegible a 2.5× más grande y centrada.
2. **Fix 2 — "Guardar DXF como..."**: `showSaveFilePicker` en desktop, `prompt` en iOS 12. Nombre sugerido: ref del pedido > medidas > genérico.
3. **Corrección de ángulo empírica ⭐⭐** (backlog handoff): flujo Cybelec completo, acumulativa, por ángulo objetivo, persiste con la pieza en galería.
4. **Extras**: corrección X global (Calibración) + fina por pliegue (⭐), CY/copiar pliegue (botón ⧉), σ relabel a kg/mm² con conversión ×9.81, y corrección de un bug del dibujo animado (`machineGeom` invertía el sentido de un brazo con mx+my combinados).
