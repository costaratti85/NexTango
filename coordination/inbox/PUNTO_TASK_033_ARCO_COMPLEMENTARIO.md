# PUNTO_TASK_033 — Arco complementario aislado en panel Philo completo

**Para:** Punto  
**De:** Nova  
**Fecha:** 2026-06-18  
**Prioridad:** Alta

---

## Síntoma

Constantino generó un panel Philo completo. Todo salió bien excepto **un solo arco** que dibujó el arco complementario en lugar del arco correcto. El resto del panel está bien.

## Contexto

El bug de arcos complementarios fue corregido en TASK_019 y TASK_021. Este arco escapó a ambos fixes. Es un caso edge que no fue cubierto.

## Datos disponibles

El DXF generado debería estar guardado en el servidor (last_generate o similar). Punto tiene que localizarlo, encontrar el arco específico que dibujó el complementario, y entender por qué escapó a los fixes anteriores.

## Pedido

1. Localizar el DXF del panel Philo generado por Constantino
2. Identificar el arco que dibujó el complementario
3. Entender por qué TASK_019/021 no lo cubrieron
4. Corregirlo

## Reporte

`coordination/reports/PUNTO_TASK_033_REPORT.md` y mensaje en `coordination/channel/Nova/`.
