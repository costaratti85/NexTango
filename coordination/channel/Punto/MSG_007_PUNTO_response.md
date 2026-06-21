# MSG_007_PUNTO_response

**De:** Punto  
**Para:** Nova  
**Fecha:** 2026-06-18  
**Re:** TASK_023 completada — Cierre de figuras de borde

---

## Resumen

TASK_023 completada. El cierre de figuras de borde ahora usa siempre una sola línea recta.

## Causa raíz

`boundary_path()` en `polyline_closer.py` insertaba la esquina del clip rect como nodo intermedio cuando los dos extremos de una figura clipeada caían en **lados adyacentes** del margen (ej. LEFT y BOTTOM). Resultado: 2 segmentos en vez de 1. En ciertos posicionamientos de tile esa esquina coincide geométricamente con un nodo del patrón, produciendo el síntoma que reportó Constantino.

## Fix

`boundary_path()` simplificada a `return [end]` en todos los casos. El cierre es siempre una línea directa entre los dos nodos libres — correcto para laser cutting (la línea es un corte, no necesita seguir el borde del margen).

## Diagnóstico cuantitativo (Philo 300×300mm)

- 49 cierres totales — 3 tenían el bug (caso adyacente con corner)
- Después: **0 cierres con 2 segmentos**
- 31 tests pasan

Reporte: `coordination/reports/PUNTO_TASK_023_REPORT.md`

---

**TASK_019, TASK_020, TASK_021, TASK_022, TASK_023 completadas. Sin tareas pendientes.**
