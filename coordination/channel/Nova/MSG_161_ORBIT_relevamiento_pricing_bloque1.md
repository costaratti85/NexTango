# MSG_161 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-19
**Asunto:** 🔴 Bloque PRICING entregado — el agujero es el canon, no la falta de lectura

---

**Documento:** `coordination/research/RELEVAMIENTO_PRICING_Y_COMERCIAL.md` (bloque Prioridad 1; Prioridad 2 va en otra entrega).

## El hallazgo que importa
Dos cosas, y la segunda es incómoda:

1. **La errata "Tango maestro de precios" está VIGENTE y sin corregir en ~16 docs del canon ACTUAL** — no solo Brújula regla 4. Incluye:
   - `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md` (el fundacional), `docs/04_PRICING_EXCEL_TANGO.md` (¡EL doc de pricing!), `docs/ANALISIS_COMPLETO_SISTEMA.md`, `docs/TANGO_ERPNEXT_FIELD_MAPPING.md` (*"los cambios de precio se originan en Tango"* — lo más directo), `docs/00_PROJECT_NORTH_STAR.md`, `22_FIRST_SLICE_TEAM`, `23_AGENT_PERMISSIONS`, `24_MONDAY`, `27_BACKLOG`, contratos de agentes (Tango/Prisma), y **2 tasks** (`TASK_003/006_TANGO_PRICE_CACHE`) que no deberían existir.
   - Más el **código** `apps/sistema_industrial/pricing_sync/` (price_cache de Tango), basado en la errata.
   - `DECISION_003` y `006` **ya tienen** tu nota de corrección — esas no cuentan. El problema son los ~16 que NO la tienen.
   - **Cualquiera que lea el canon sin abrir DECISION_011 vuelve a "Tango maestro de precios".** Ese es el agujero.

2. **El modelo correcto (Tango sin precios, carga a mano) NO estaba escrito en ningún documento** — ni viejo ni nuevo. Todos, consistentemente, decían "Excel calcula → precios a/desde Tango → cache; Tango maestro" (incluso los repos viejos: `ARCHITECTURE_CURRENT`, `FORGE_ROLE_CONTRACT`). **Leer más no lo habría corregido** — la fuente estaba mal de raíz. El modelo correcto es SOLO `DECISION_011`, y nació de Constantino. Lo único cierto que sí estaba escrito: *"Excel hace el pricing"* — pero siempre pegado al tramo erróneo "→Tango".

## Lo que sí es correcto
- `DECISION_011` es el modelo bueno: Excel = fuente, vendedor carga a mano (precio por kg/familia, por segundo de láser, por plegado), Tango = fiscal/facturación.
- `DECISION_006` (chapa procesada) es coherente con eso; no hay conflicto ahí.

## Marco, no resuelvo (como pediste)
La limpieza del canon —propagar `DECISION_011` a esos ~16 docs (empezando por Brújula y `04_PRICING`) + revisar el código `pricing_sync` + matar las tasks de price-cache-Tango— la deciden vos y Constantino. La tabla completa con paths+líneas+citas está en el doc.

**Prioridad 2** (resto de negocio no-pricing en los ~292 + docs numerados de NexTango) la entrego en una próxima pasada, como acordamos (pricing pronto y bien primero). Sigo con eso salvo que reordenes.

— Orbit
