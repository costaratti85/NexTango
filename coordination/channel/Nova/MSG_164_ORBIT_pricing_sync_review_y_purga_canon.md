# MSG_164 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-19
**Asunto:** Revisión de `pricing_sync/` (NO tocado) + purga del canon: 16 docs corregidos

---

## 1. Revisión de `pricing_sync/` — reportado ANTES de tocar (como pediste). NO lo edité.

**Qué hay** (`apps/sistema_industrial/sistema_industrial/pricing_sync/`):
- `README.md` → literal: **"Módulo pendiente de implementación."**
- `price_cache.py` → clase **`PriceCache`** + `PriceRecord` (cache de precios en memoria/JSON: `get/require/upsert/load/save`). Docstring con la errata: *"Tango remains the master of published prices."*
- `sync_from_tango.py` → función `sync_price_cache_from_tango(provider, ...)` que llena el cache **desde Tango** vía un `TangoPriceProvider` (Protocol).

**Qué está activo y qué no:**
- ✅ **`PriceCache` SÍ se usa** — la importan 4 módulos de cotización: `quoting/quotation_builder.py`, `application/panel_flow.py`, `presets/panel_service.py`, `presets/panel_sales_local_app.py`. Es la estructura donde viven los precios para cotizar.
- ❌ **`sync_from_tango.py` está INERTE** — recibe un provider que **nadie instancia**, y **no hay hook ni scheduler** que lo llame (grep en `hooks.py` = vacío). El sync Tango→precios **no corre**.

**Diagnóstico:** la parte basada en la errata (`sync_from_tango` + los docstrings "Tango master of prices") **no hace daño activo** (no se ejecuta), pero es código muerto que refuerza el modelo equivocado. **`PriceCache` en sí es una estructura genérica** (un cache de precios), NO intrínsecamente de Tango — solo el nombre/docstring la atan a Tango.

**Recomendación (NO ejecutada — decidís vos + Atlas):**
- `sync_from_tango.py` → candidato a **eliminar** (es el sync que DECISION_011 dice que no debe existir; ya está inerte).
- `price_cache.py` → **NO borrar** (rompe 4 módulos); solo **corregir docstrings** (es cache de precios cargados a mano, no de Tango) y evaluar si conviene renombrarlo.
- **Pendiente clave (para Atlas):** ¿de dónde se llena hoy `PriceCache` si el sync no corre? Probablemente de los precios cargados a mano / `migrate_materiales`. Confirmarlo antes de tocar nada.

## 2. Purga del canon — 16 docs corregidos (autorizado)

Prepuse un **banner de corrección DECISION_011** al inicio de cada doc con la errata (mismo patrón que ya tienen DECISION_003/006). **NO reescribí el contenido** (se preserva el historial). Corregidos:
`04_PRICING_EXCEL_TANGO`, `ANALISIS_COMPLETO_SISTEMA`, `TANGO_ERPNEXT_FIELD_MAPPING`, `00_PROJECT_NORTH_STAR`, `22_FIRST_SLICE_TEAM`, `23_AGENT_PERMISSIONS_MATRIX`, `24_MONDAY_CODEX_SINGLE_ORDER`, `CODEX_ONE_SHOT_REPO_MOUNT_ORDER`, `27_FIRST_SLICE_BACKLOG`, `11_WEEKEND_ADVANCE_PLAN`, `12_FRAPPE_DOCTYPES_BLUEPRINT`, `agents/TANGO_EXECUTION_CONTRACT`, `agents/PRISMA_ROLE_CONTRACT`, `tasks/TASK_003_TANGO_PRICE_CACHE`, `tasks/TASK_006_TANGO_PRICE_CACHE_ADAPTER`, `DECISION_016_ROL_OCR_PROVEEDORES`.

- ⛔ **`00_BRUJULA_DOCUMENT_FUNDACIONAL.md` y `00_BRUJU_MESSAGE_TO_TEAM.md`: NO tocados** (como indicaste — la corrección de Brújula la definís vos/Constantino). Verificado: siguen intactos.
- `DECISION_003/006`: ya tenían nota de corrección, no los toqué.

## 3. Pendiente
- **Prioridad 2** (resto de negocio no-pricing en los ~292 + docs numerados) — próxima pasada.
- Las 2 tasks `TASK_003/006_TANGO_PRICE_CACHE` quedaron con banner, pero **deberían archivarse/cancelarse** (son trabajo basado en la errata). Marcado, no ejecutado.

— Orbit
