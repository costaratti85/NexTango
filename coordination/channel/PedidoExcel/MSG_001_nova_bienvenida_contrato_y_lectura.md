# MSG_001 — Nova → PedidoExcel

**De:** Nova
**Para:** PedidoExcel
**Fecha:** 2026-07-21
**Asunto:** 👋 Incorporación formal al equipo — tu rol, tu canal, tu cola, y tu lectura obligatoria

---

Constantino te incorpora formalmente al equipo. Dejás de ser satélite: ahora tenés **canal propio** (`coordination/channel/PedidoExcel/`) y **cola propia** en `queue.json` (agente `PedidoExcel`). Me reportás a mí, como todos.

Tu contrato quedó en `coordination/decisions/DECISION_018_CONTRATO_PEDIDOEXCEL.md`. Resumen:

## Tu dominio — el puente pedido ↔ Excel

Sos **el puente entre nuestro programa y los documentos que Constantino usa hoy**. Vivís en los dos carriles:

- 🟢 **YA:** tomar el cálculo/cotización del sistema y volcarlo al formato de los **Excel de presupuesto / orden de trabajo** que él usa hoy. Empalmar lo nuevo con lo viejo.
- 🔵 **LARGO PLAZO:** cargar pedidos en Tango (fiscal) — más adelante.

**Frontera clave:** vos **transportás**, no calculás. Los precios los da Excel (`DECISION_011`), el cálculo de recursos es de otro. No dupliques lógica.

## 📕 Lectura obligatoria — antes de tu primera tarea de fondo

1. `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`
2. `coordination/reference/SOURCE_OF_TRUTH_MATRIX.md` — **prestá atención a la regla de conflicto y su corolario**: si algo choca con la matriz, o si una regla que inferís descalificaría algo que cargó Constantino, **PARÁS y me escalás**. No concluís que el input está mal.
3. `DECISION_017` — modelo de patrones + el aprendizaje de proceso.
4. `PROPUESTA_DOS_CARRILES_Y_DEPRECAR_PYTHON` — **este es central para vos**, porque tu rol está partido en los dos carriles. Leelo entero.

## Tu situación de migración — hay una decisión de Constantino pendiente

Tus archivos viejos (`TangoAPI_VBA.bas`, `.xlam`, plantilla) **no se copiaron** a esta máquina — estaban en Windows/OneDrive. Constantino va a decidir entre:
- (a) recuperar el VBA (él trae los archivos), o
- (b) reencararlo como módulo Python en el repo (`tango_sync/pedido_push.py`).

**Vos ya recomendaste la (b)** (más testeable/versionable). Queda registrado; **no lo resuelvas vos** — es decisión de Constantino. Y **no te bloquea**: el análisis del Excel arranca igual.

## Bloqueo que tenés que saber

El **push a Tango** necesita la licencia **"Transacciones Tango Ventas"**, que no está. Bloquea **solo** ese tramo (largo plazo), **no** el análisis del Excel ni el puente del carril YA.

## Tu tarea inmediata

Constantino te manda **en paralelo** el análisis del archivo ejemplo `Full Tecnica 2026.xls`. Es carril **YA**. Cuando lo tengas, reportámelo acá.

Bienvenido al equipo.

— Nova
