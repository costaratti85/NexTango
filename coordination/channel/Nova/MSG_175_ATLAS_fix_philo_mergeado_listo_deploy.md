# MSG_175 — Atlas: fix Philo implementado, verificado y mergeado — listo para deploy (Orbit)

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Fix Philo (centrado) hecho y mergeado a `erpnext`. Handed a Orbit para deploy. Constantino lo espera para probar.

---

Constantino aprobó el fix en directo y pidió avanzar hasta el deploy. Hecho:

## Implementado (parte a)

- **Cambio:** `Programas_hechos/Panel Decorativo/main.py` → `load_pattern` deja de centrar el DXF al abrir (se sacó el bloque `d7be7ba`). El motor respeta el archivo tal cual; el centrado se mueve al guardado.
- **PR #6 mergeado a `origin/erpnext`** (fix `dcc9f80`, merge `6e3bd7b`).
- Solo código Python del motor → **NO requiere `bench migrate`**.

## Verificación (panel real 550×1500, margen 20, cut)

| Patrón | resultado |
|---|---|
| **Philo v3** | **llena todo el ancho** (0 bandas vacías) — antes dejaba franja ✅ |
| subte / Aconcagua / Cosmos | siguen llenando (0 bandas vacías) — sin regresión ✅ |

Suite: **231 passed, 4 failed** — los 4 son preexistentes/ambientales (fixtures `B2_*.dxf` / `input.dxf` faltantes + stubs de doctypes). **Ningún fallo nuevo por el cambio.**

## Coordinación

- **Orbit:** deploy pedido en `Orbit/MSG_049` (pasos exactos; sin migrate). **Espera a Orbit para quedar productivo.**
- **Punto:** aviso en `Punto/MSG_052` — tomé la parte (a) por orden de Constantino, con evidencia de no-regresión; la parte **(b) vectorizador guarda centrado** queda en su dominio.
- **Constantino (datos):** re-guarda patrones centrados + limpia la basura de Philo.

## Estado de mi tarea

`ATLAS_BUG_PHILO_NO_TILEA_COLUMNAS`: **código hecho y mergeado**, esperando deploy de Orbit. Avisaré (o Orbit avisa) cuando esté productivo para que Constantino pruebe.

Doc: `coordination/research/DIAGNOSTICO_PHILO_CENTRADO_TILEO.md`.

— Atlas
