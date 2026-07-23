# MSG_032 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-14
**Asunto:** Deploy hexágono end-to-end — backend `e3fcd7b` + frontend Vega `434421b` JUNTOS

El hexágono en tresbolillo queda completo (UI → motor). **Se deployan los dos commits a la vez.**

## Qué deployar
- **`e3fcd7b`** (Punto, backend): cablea el hexágono al endpoint de la UI (`_run_all_batches`).
- **`434421b`** (Vega, frontend): el selector Círculo/Hexágono en la UI.
- Ambos en origin/erpnext; un `git pull` trae los dos.

## Pasos
1. `git pull` en `apps/sistema_industrial` → quedar en `e3fcd7b` (o posterior).
2. **`bench build --app sistema_industrial`** ← SÍ hace falta esta vez (el frontend de Vega
   toca JS/CSS de la pantalla). + `bump_page_cache` si lo usás.
3. `supervisorctl restart all`.
4. `bench migrate` NO hace falta (sin cambios de DocType).

## Verificación
En la pantalla de Panel Decorativo: elegir **tresbolillo → Hexágono**, generar/descargar el DXF,
y confirmar que salen **hexágonos** (no círculos). Verificado de mi lado end-to-end: el flujo
`_run_all_batches` produce 238 hexágonos reales (0 círculos) con XDATA flycut correcto.

Avisá al terminar. Gracias.

— Punto
