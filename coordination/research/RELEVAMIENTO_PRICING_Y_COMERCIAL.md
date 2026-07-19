# Relevamiento PRICING y comercial (2ª pasada enfocada)

**Autor:** Orbit · **Fecha:** 2026-07-19 · **Tipo:** SOLO LECTURA · **Entrega:** POR PARTES — **este es el bloque PRICING (Prioridad 1)**; el resto de negocio (Prioridad 2) va en una entrega posterior.
**Regla de esta pasada:** NO asumir que el canon está bien. Cotejar cada definición contra `DECISION_001..016` + Brújula y **marcar toda discrepancia**, incluso en el canon actual.

---

## 0. Titular (lo urgente)

El modelo de pricing **correcto** es `DECISION_011`: **el pricing se hace en EXCEL, Excel es la fuente, el vendedor los carga a mano en el sistema, y Tango NO maneja precios** (Tango = fiscal/facturación).

**Pero la errata "Tango es maestro de precios" sigue VIGENTE, sin corregir, en ~16 documentos del canon ACTUAL** (incluido el fundacional Brújula y el propio `04_PRICING_EXCEL_TANGO.md`). `DECISION_011` corrigió la *decisión* pero **no propagó la corrección a los docs**. Cualquiera que lea el canon hoy —sin abrir DECISION_011— vuelve a concluir "Tango maestro de precios". **Ahí está el agujero.**

Y un hallazgo incómodo pero honesto (§4): **el modelo correcto NO estaba escrito en ningún doc, viejo ni nuevo.** Todos traían la misma errata consistente. Leer *más* documentos no habría dado el modelo correcto — lo habría reforzado. El modelo correcto vino de Constantino.

---

## 1. El modelo de pricing SEGÚN LOS DOCUMENTOS (con citas)

Todos coinciden en un flujo con **Tango en el medio como maestro** (la errata):

- `docs/04_PRICING_EXCEL_TANGO.md`:6-8 → *"Factura proveedor → costos Excel → **pricing Excel → precios Tango → cache ERPNext**. **Tango es maestro de precios publicados**."*
- `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`:24 (regla 4) → *"**Tango es maestro de precios finales** — ERPNext sincroniza copia."* · :38 → *"…cálculo automático de recursos → **precios desde Tango** → cotización ERPNext."* · :68 (OCR) → *"…pricing en Excel → **precios a Tango**."*
- `docs/ANALISIS_COMPLETO_SISTEMA.md`:33 → *"Pricing: lo sigue calculando un humano en Excel; **Tango es maestro de precios publicados**."* · :50 → *"Price cache | **Cache local de precios Tango** | `pricing_sync/price_cache.py`."*
- `docs/TANGO_ERPNEXT_FIELD_MAPPING.md`:78-79 → *"La lista de precios de Tango es **solo lectura** en ERPNext. **Los cambios de precio se originan en Tango** y se sincronizan hacia ERPNext."* ← el más frontalmente contrario a DECISION_011.
- `docs/00_PROJECT_NORTH_STAR.md`:8 → *"Tango Gestión: …**precios publicados** — integrado via API."*
- `docs/23_AGENT_PERMISSIONS_MATRIX.md`:8 → *"Tango | …**cache precios**."* · `docs/agents/TANGO_EXECUTION_CONTRACT.md`:7 → *"…**precios maestros**."*
- **Repos viejos:** `Sistema-Industrial/docs/ARCHITECTURE_CURRENT.md`:9-10 → *"Tango… **master prices**"* + *"Excel for pricing formulas"* · `Sistema-Industrial/docs/agents/FORGE_ROLE_CONTRACT.md`:114-115 → *"→ Excel pricing → **Tango price list update**."*

**Lo que sí quedó claro y es correcto en los docs:** *"Excel hace el pricing / las fórmulas"* (DECISION_003, 04_PRICING, ARCHITECTURE_CURRENT:10). El error no es "Excel"; el error es el tramo **"→ Tango → cache"** y **"Tango maestro"**.

## 2. El modelo CORRECTO (DECISION_011, 2026-07-19)

> *"El PRICING se hace en EXCEL. Los precios vienen de ahí. **Tango NO maneja precios. Tango es fiscal/facturación.**"* · *"El vendedor **carga a mano** los precios diarios en nuestro sistema (ERPNext) a la mañana."* · *"Excel → sistema: automatización a desarrollar más adelante; hoy carga manual (mecanismo oficial, no parche)."* · *"La página de precios es **EDITABLE y escribible**; nada de solo-lectura ni sync con Tango."*

---

## 3. 🔴 CONTRADICCIONES contra las DECISIONs (lo más importante)

**No es "viejo vs nuevo": el canon actual se auto-contradice.** `DECISION_011` dice X; ~16 docs del canon actual dicen lo opuesto (errata sin corregir).

| # | Documento (canon ACTUAL) | Dice (errata) | Contradice | Estado |
|---|---|---|---|---|
| 1 | `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md` §regla 4, :38, :68 | "Tango maestro de precios" / "precios desde/a Tango" | DECISION_011 | ❌ **sin corregir** (el fundacional) |
| 2 | `docs/00_BRUJU_MESSAGE_TO_TEAM.md`:23 | "frontera… precios maestros" | DECISION_011 | ❌ sin corregir |
| 3 | `docs/04_PRICING_EXCEL_TANGO.md`:6,8 | "pricing Excel → precios Tango → cache", "Tango maestro" | DECISION_011 | ❌ sin corregir (¡es EL doc de pricing!) |
| 4 | `docs/ANALISIS_COMPLETO_SISTEMA.md`:17,25,33,50,245 | "precios de Tango", "sync precios Tango", "cache precios Tango" | DECISION_011 | ❌ sin corregir |
| 5 | `docs/TANGO_ERPNEXT_FIELD_MAPPING.md`:3,78,79 | "los cambios de precio se originan en Tango" | DECISION_011 | ❌ sin corregir (el más directo) |
| 6 | `docs/00_PROJECT_NORTH_STAR.md`:8 | "Tango: precios publicados" | DECISION_011 | ❌ sin corregir |
| 7 | `docs/22_FIRST_SLICE_TEAM.md`:10 | "Tango: precios maestros" | DECISION_011 | ❌ sin corregir |
| 8 | `docs/23_AGENT_PERMISSIONS_MATRIX.md`:8 | "Tango: cache precios" | DECISION_011 | ❌ sin corregir |
| 9 | `docs/24_MONDAY_CODEX_SINGLE_ORDER.md`:21 / `docs/CODEX_ONE_SHOT_REPO_MOUNT_ORDER.md`:21 | "Tango frontera… precios maestros" | DECISION_011 | ❌ sin corregir |
| 10 | `docs/27_FIRST_SLICE_BACKLOG.md`:27 | "Sincronización precios Tango" (backlog) | DECISION_011 / DECISION_002-style | ❌ sin corregir |
| 11 | `docs/agents/TANGO_EXECUTION_CONTRACT.md`:7 / `docs/agents/PRISMA_ROLE_CONTRACT.md` | "precios maestros" en el contrato de Tango | DECISION_011 | ❌ sin corregir |
| 12 | `docs/tasks/TASK_003_TANGO_PRICE_CACHE.md` / `TASK_006_TANGO_PRICE_CACHE_ADAPTER.md` | "sincronizar precios publicados de Tango → cache" (tareas) | DECISION_011 | ❌ tareas que **no deberían existir** |
| 13 | `docs/11_WEEKEND_ADVANCE_PLAN.md`, `docs/12_FRAPPE_DOCTYPES_BLUEPRINT.md` | mencionan precios-Tango | DECISION_011 | ❌ sin corregir |
| 14 | `DECISION_016_ROL_OCR_PROVEEDORES.md` | flujo OCR "precio a Tango" (heredado de Brújula:68) | DECISION_011 | ⚠️ revisar |
| — | `DECISION_003`, `DECISION_006` | tenían la errata | DECISION_011 | ✅ **ya tienen nota de corrección** (no cuentan) |
| — | **Código:** `apps/sistema_industrial/pricing_sync/` (price_cache de Tango) | implementa el sync Tango→precios | DECISION_011 | ⚠️ **código basado en la errata** — revisar con Atlas/Tango |

**Contradicción secundaria (menor):** `DECISION_006` dice que "chapa procesada" es el único artículo que se factura y que los insumos (hierro cortado/plegado) nunca se facturan — **coherente** con DECISION_011; no hay conflicto ahí, solo comparten la nota de corrección de la errata Tango-precios.

## 4. Hallazgo clave (honesto)

**El modelo correcto (Tango sin precios) no estaba escrito en NINGÚN documento** — ni viejo ni nuevo. Todos, de forma consistente, decían "Excel calcula → precios a/desde Tango → cache; Tango maestro". Incluso los repos viejos (`ARCHITECTURE_CURRENT`, `FORGE_ROLE_CONTRACT`) traían el mismo flujo Excel→Tango. Por eso **"leer más" no habría evitado el error**: la fuente estaba equivocada de raíz. El único documento con el modelo correcto es `DECISION_011`, que nació de la corrección de Constantino, no de los docs. Lo que sí estaba escrito y es rescatable: *"Excel es donde se hace el pricing"* — cierto, pero siempre venía pegado al tramo erróneo "→Tango".

## 5. Definiciones de negocio de pricing (para el canon)
- **Precio por kg por familia**, **precio por segundo de láser**, **precio por plegado** = los 3 precios que el vendedor carga a mano (DECISION_011 §2). Son el corazón de la página de precios.
- Flujo comercial (Brújula §3): *cotización → ítems → cálculo de recursos → precios (de Excel, corregido) → cotización ERPNext*. La cotización vive en ERPNext (Source of Truth Matrix: "Quotation → ERPNext"). Coherente.

---

## 6. Cobertura
- **Leído a fondo (Prioridad 1 pricing):** `04_PRICING_EXCEL_TANGO`, Brújula + Bruju + North Star, `ANALISIS_COMPLETO_SISTEMA`, `TANGO_ERPNEXT_FIELD_MAPPING`, DECISION_003/006/011, contratos Tango (actual + viejo), `ARCHITECTURE_CURRENT`/`FORGE_ROLE_CONTRACT` (viejos), tasks de price cache, barrido ES+EN de precio/price/pricing/Excel/cotización/margen/factura en los 3 repos.
- **PENDIENTE (Prioridad 2, próxima entrega):** el resto de definiciones de negocio no-pricing en los ~292 docs viejos (contratos DTO, README por módulo, gobernanza) + docs numerados de NexTango (`docs/0X_*`, `docs/2X_*`) que no tocan pricing. Entrego este bloque ahora, como pediste.
- **Sin secretos transcritos.** Solo lectura, sin tocar repos.

## Resumen ejecutivo
Modelo correcto = `DECISION_011` (Excel es la fuente, vendedor carga a mano, **Tango NO precios**). La errata "Tango maestro de precios" sigue **viva y sin corregir en ~16 docs del canon actual** (incl. Brújula y `04_PRICING`), más código `pricing_sync` y 2 tasks de "price cache Tango" que no deberían existir. El modelo correcto **no estaba escrito en ningún doc** — todos tenían la misma errata; leer más no la corregía. **Marco, no resuelvo:** la limpieza del canon (propagar DECISION_011 a esos 16 docs + revisar el código pricing_sync) la deciden Constantino y Nova.
