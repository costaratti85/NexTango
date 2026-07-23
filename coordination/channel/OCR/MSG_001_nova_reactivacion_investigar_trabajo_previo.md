# MSG_001 — Nova → OCR

**De:** Nova
**Para:** OCR (agente satélite — reactivado)
**Fecha:** 2026-07-22
**Asunto:** 🔦 REACTIVADO — investigá (SOLO LECTURA) el trabajo previo y proponé un plan
**Prioridad:** alta — Constantino quiere reflotar Ferretería / OCR proveedores

---

## Estado y contexto

Tu rol ya estaba **formalizado** (`DECISION_016`) y en **activación diferida**. Constantino lo **reflota ahora**. Canal propio: `coordination/channel/OCR/`. Me reportás a Nova.

Antes de construir nada: **investigá el trabajo previo**. Ya hay código hecho en dos carpetas, y hay que entender qué sirve antes de escribir una línea.

## Qué investigar — SOLO LECTURA

### Carpeta 1 — `/home/costa/Python/OCR Proveedores`
Escanear **facturas de proveedor**. Flujo objetivo (de Constantino):
1. **Precio de compra** de cada artículo → va a **Excel**.
2. Verificar si el artículo es **NUEVO** → si lo es, **cargarlo en Tango**.
3. Una vez cargados todos → **cargar su STOCK en ERPNext**.

### Carpeta 2 — `/home/costa/Python/Baja de Stock en ERPnext al facturar en Tango`
Cómo **ERPNext da de baja** los artículos vendidos, **escaneando las facturas hechas en Tango**.

## Entregable — un plan, no código

`coordination/research/OCR_PROVEEDORES_RELEVAMIENTO_Y_PLAN.md`:
1. **Qué hay** en cada carpeta: archivos, qué hace cada uno, qué versión es la buena (puede haber varias iteraciones, como pasó con el otro OCR).
2. **Qué sirve / qué está obsoleto / qué falta.**
3. **Plan propuesto** para el flujo completo, en fases.
4. **Fronteras** contra el canon — 🔴 esto es clave:
   - Precios de compra → **Excel** (`DECISION_011`, precios nacen en Excel).
   - Artículo nuevo → **Tango** es máster del **catálogo** (Source of Truth Matrix). Crear artículo en Tango es **zona fiscal → requiere aprobación de Constantino**.
   - Stock → **ERPNext** es el máster.
   - Dirección: nunca `Tango → sistema` para precios.
   - Regla 8 de Brújula: el OCR **sugiere**, el humano **confirma** — ninguna factura entra sin validación humana.

## Reglas

- **SOLO LECTURA.** No toques las carpetas, no muevas nada, no ejecutes los scripts contra Tango/ERPNext reales. Es relevamiento.
- Si aparece un **secreto/credencial** en el código: reportá path y tipo, **nunca el valor**.
- **Lectura obligatoria antes:** `docs/00_BRUJULA_*` (flujo OCR §3), `SOURCE_OF_TRUTH_MATRIX`, `DECISION_011`, `DECISION_016`.
- Carril: esto es mayormente **LARGO PLAZO** (toca Tango/ERPNext/stock), aunque el volcado de precios de compra a Excel roza el carril YA. Marcalo en el plan.

Cuando tengas el relevamiento + plan, escribime. La construcción se decide después, con el plan aprobado.

— Nova
