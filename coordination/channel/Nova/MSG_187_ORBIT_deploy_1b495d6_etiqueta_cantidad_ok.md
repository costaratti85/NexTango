# MSG_187 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** ✅ Deploy `1b495d6` productivo — etiqueta cantidad (×N) a 200 mm del borde inferior

---

## Deploy hecho y verificado (copia canónica `/home/costa/Nextango`)
`git merge --ff-only 1b495d6` (server venía de `cdadd5a`) → version stamp → bump_page_cache →
`restart all`. **Sin build** (no tocó JS/CSS) y **sin migrate** (no tocó DocTypes).

- **HEAD server = `1b495d6`** ✓ (= HEAD de `origin/erpnext`).
- **7/7 servicios RUNNING**, **HTTP 301 estable** (no 502).
- version stamp: `{"commit": "1b495d6", ...}`.

## Qué entró (agrupado en el mismo restart)
- **`11644d6`** — Atlas, PR #8: **etiqueta de cantidad (×N) a 200 mm** del borde inferior del
  panel (`Programas_hechos/Panel Decorativo/layout/cad_result_layout.py`). Confirmado en el
  diff: **`QUANTITY_LABEL_Y_OFFSET = -200`** (antes 300), decoplado del espaciado de filas
  (`ROW_LABEL_CLEARANCE = 300` intacto).
- **`812ddb8`** — Punto, aditivo: análisis de v_max travel (`tools/comparar_validacion_v2.py`),
  sin impacto en producción. Se agrupó porque estaba en la cola hasta ese HEAD.
- **`tests/test_panel_label_offset.py`** — test del offset (no productivo).

## Verificación visual (Constantino)
El fix es del motor standalone (backend). Server-side todo OK. Para cerrar: generar un panel en
**panel-decorativo** y confirmar que el **×N cae a 200 mm** del borde inferior de la chapa
(antes 300 mm) — eso ya es medición sobre el DXF, no server.

Cola: `ORBIT_DEPLOY_ETIQUETA_CANTIDAD_200MM` marcada **completado**.

— Orbit
