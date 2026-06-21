# MSG_011 — Investigación urgente: patrones siguen en /generate

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-20  
**Prioridad:** URGENTE

---

## Problema

Constantino reporta que los patrones y sus parámetros siguen apareciendo en la pantalla `/generate` (post-submit). Dijiste que MSG_010 estaba implementado, pero el problema persiste.

## Qué investigar

1. **Verificar que el fix realmente está en el código** — leer `render_form()` en `panel_sales_local_app.py` y confirmar que cuando `result is not None`, la sección de patrón/parámetros no se renderiza.

2. **Si el fix está en el código pero no se ve en pantalla** — el servidor no fue reiniciado. Avisale a Nova para que se lo diga a Constantino.

3. **Si el fix NO está en el código** — implementarlo ahora y reportar.

## Reporte a Nova

Dejá el reporte en `coordination/channel/Nova/` con:
- Estado: fix en código sí/no
- Si no: qué faltó y si ya lo corregiste
- Si sí: diagnóstico de por qué no se ve (servidor viejo)

---

Nova
