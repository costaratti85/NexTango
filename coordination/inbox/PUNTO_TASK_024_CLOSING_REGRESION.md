# PUNTO_TASK_024 — Cierre de figuras de borde: bug persiste post TASK_023

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta  
**Re:** Seguimiento de TASK_023

---

## Síntoma

Constantino reporta que el problema de cierre con 2 líneas **sigue ocurriendo** después del fix de TASK_023.

Captura de pantalla: figuras en el margen izquierdo del panel muestran nodos azules marcando puntos de quiebre — en vez de cerrarse con una línea recta entre los dos nodos libres, se cierran con dos vectores que se unen en un nodo ya existente de la figura.

El comportamiento es idéntico al reportado originalmente: 2 segmentos en lugar de 1, con un nodo intermedio que coincide con un nodo ya existente de la pieza.

## Contexto

TASK_023 simplificó `boundary_path()` a `return [end]`. El bug persiste, lo que sugiere que hay otro lugar en el pipeline que produce el mismo síntoma, o que `boundary_path()` no es el único punto de entrada para este tipo de cierre.

## Pedido

1. Investigar por qué el síntoma persiste después del fix de TASK_023
2. Identificar el código path real que genera los cierres con 2 segmentos
3. Corregirlo
4. Verificar con el panel que muestra el problema (Constantino puede proveer el DXF si hace falta)

## Reporte

Dejar reporte en `coordination/reports/PUNTO_TASK_024_REPORT.md` y mensaje en `coordination/channel/Nova/`.
