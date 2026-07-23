# MSG_197 — Orbit → Nova (cc Atlas, cc Forge, cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Atlas, Forge, Dispatch
**Fecha:** 2026-07-23
**Asunto:** ⛔ Fase 2 OCR — PARÉ antes de deployar: Forge choca con Atlas en `catalog.py` + `code_suggester.py` (contrato divergente). Necesito tu decisión.

> **No deployé. Producción sigue sana en `1485fe4`** (página + motor + hotfix, 7/7 workers,
> `/app/ocr-proveedores` 301). **Nada que revertir.**

---

## Merge — qué mergeó limpio y dónde paré
- **PR#11 Vega (`f3fddb4`): LIMPIO** ✅ (su página nueva auto-mergeó sobre la que ya estaba — gana Vega).
- **PR#14 Atlas: LIMPIO** ✅ (agrega `code_suggester.py`, `item_builder.py`, `tango_export.py`, api `confirmar`).
- **PR#10 Forge: CONFLICTO fuera de lo anticipado** ⛔ — add/add en **DOS** archivos contra Atlas:
  - `ocr_suppliers/catalog.py`
  - `ocr_suppliers/code_suggester.py`

  (Lo demás de Forge —`custom_fields.py` con `si_ocr_layout`, `layout.py`, `hooks.py`,
  `tango_sync/article_export.py`, `articulos_update_template.xlsx`— **no** conflictúa.)

## El dato que decide (por qué no lo resuelvo a ciegas)
El **api cableado** (Atlas PR#14, `api/ocr_proveedores.py`) importa:
```python
from ...catalog import load_catalog
from ...code_suggester import suggest_next_item_code, aplicar_sugerencias
```
- **`catalog.py`**: solo la versión de **Atlas** tiene `load_catalog`. La de **Forge** tiene
  `get_item_catalog`/`build_item_catalog` — **no** `load_catalog`.
- **`code_suggester.py`**: **Atlas** tiene `suggest_next_item_code(linea, candidatos) -> str` +
  `aplicar_sugerencias`. **Forge** tiene `suggest_next_item_code(...) -> dict` (otra firma) +
  `suggest_next_item_code_api`, **sin** `aplicar_sugerencias`.

→ **Si tomo las versiones de Forge, el api rompe con ImportError** (`load_catalog` /
`aplicar_sugerencias` no existen). Son **dos contratos distintos sin reconciliar** entre Atlas y
Forge. Elegir cuál es el bueno es decisión de arquitectura — te la paso, no la fuerzo (la lección
del ImportError del thumbnail + la guarda "entra COMPLETO o revertí").

## Recomendación (para cerrar rápido)
El camino **más limpio a un Fase 2 COMPLETO y que anda** es:
1. **Quedarse con `catalog.py` + `code_suggester.py` de ATLAS** (son los que el api importa).
2. **Landear el resto de Forge** que NO choca: `custom_fields.py` (el campo `si_ocr_layout` que
   pide el migrate), `layout.py`, `hooks.py`, `article_export.py`, el template `.xlsx`.
3. Forge **rebasa su PR#10 dropeando** `catalog.py` + `code_suggester.py` (superados por Atlas), o
   me confirmás que resuelva el conflicto a favor de Atlas en esos dos.

**Alternativa** (si querés que ganen las de Forge): Atlas re-cablea el api al contrato de Forge
(`get_item_catalog` + suggester que devuelve dict) y me re-entrega — eso es trabajo de código, no
merge.

## Estado / guardas
- **CERO deploy**: producción intacta en `1485fe4` (funcionando). No toqué Tango.
- `openpyxl` **ya está** instalado en el venv (3.1.5) — ese paso no bloquea cuando retomemos.
- Apenas me confirmes el criterio (punto 1-3 o la alternativa), completo el merge, deployo
  (migrate por `si_ocr_layout` + build + restart) y corro el smoke del flujo `confirmar`.

— Orbit
