# DECISION_018 — Contrato de PedidoExcel (puente pedido ↔ Excel)

**Fecha:** 2026-07-21 · **Definido por:** Constantino · **Registrado por:** Nova
**Estado:** Vigente — incorporación formal al equipo
**Antes:** agente satélite ("Cargar pedido Tango vía Excel"), sin canal ni cola propia.

---

## 1. Incorporación

**PedidoExcel** deja de ser satélite y se incorpora formalmente al equipo:
- **Canal:** `coordination/channel/PedidoExcel/`
- **Cola:** propia, en `coordination/dispatch/queue.json` (agente `PedidoExcel`)
- **Contacto:** reporta a **Nova**, como todos.

## 2. Dominio

**El puente entre "nuestro programa" y los documentos de presupuesto / orden de trabajo.** Tiene dos tramos, uno en cada carril (ver `PROPUESTA_DOS_CARRILES_Y_DEPRECAR_PYTHON`):

| Tramo | Carril | Qué es |
|---|---|---|
| **Puente ↔ Excel** | 🟢 **YA** | Tomar el cálculo/cotización del sistema y volcarlo al formato de los **Excel de presupuesto / orden de trabajo** que Constantino usa hoy. Es el empalme "lo nuevo con lo viejo". |
| **Carga de pedidos en Tango** | 🔵 **LARGO PLAZO** | Empujar pedidos a Tango (zona fiscal). Depende de licencia (ver §5) y del modelo de clientes del carril largo plazo. |

**Fronteras (Source of Truth Matrix):**
- Precios → **Excel** (no los inventa; los consume). `DECISION_011`.
- Zona fiscal / facturación / pedidos en Tango → 🔴 requiere aprobación de Constantino. El tramo largo plazo cae acá.
- No duplica el cálculo de recursos (es de Punto / futuro rol de Cálculo) — PedidoExcel **transporta**, no calcula.

## 3. Lectura obligatoria (antes de su primera tarea de fondo)

- `docs/00_BRUJULA_DOCUMENT_FUNDACIONAL.md`
- `coordination/reference/SOURCE_OF_TRUTH_MATRIX.md` (incluida la regla de conflicto y el corolario)
- `DECISION_017` (modelo de patrones + aprendizaje de proceso)
- `PROPUESTA_DOS_CARRILES_Y_DEPRECAR_PYTHON` (el marco YA vs LARGO PLAZO — es central para él, porque su rol vive en los dos)

## 4. ⏳ PENDIENTE DE CONSTANTINO — cómo se retoma su trabajo viejo (migración)

Los archivos de trabajo de este agente **no se copiaron** a la máquina Linux. Vivían en una ruta **Windows/OneDrive**:
- `TangoAPI_VBA.bas` (VBA)
- `.xlam` (add-in de Excel)
- plantilla

**Decisión pendiente — a aprobar por Constantino:**

| Opción | Qué implica |
|---|---|
| **(a) Recuperar el VBA** | Constantino trae los archivos desde Windows/OneDrive; se retoma sobre esa base. |
| **(b) Reencarar como módulo Python** en el repo (`tango_sync/pedido_push.py`) | Más **testeable y versionable**, vive en git. **Es lo que el propio agente recomienda.** |

**No hace falta resolver esto para arrancar el análisis del Excel ejemplo** (esa tarea empieza ya, en paralelo). Es la decisión de **con qué base se construye el push**, no del análisis.

## 5. ⛔ BLOQUEO del tramo largo plazo — licencia Tango

El **push de pedidos a Tango** requiere la licencia **"Transacciones Tango Ventas"**, que hoy no está.

- **Bloquea SOLO** el tramo largo plazo (carga de pedidos en Tango).
- **NO bloquea** el análisis del Excel ni el puente ↔ Excel del carril YA.

Queda anotado como bloqueo a levantar cuando Constantino gestione la licencia.

## 6. Estado inicial

- **Activo en el carril YA:** análisis del archivo ejemplo `Full Tecnica 2026.xls` (tarea inmediata, la manda Constantino en paralelo).
- **Diferido / pendiente:** el push a Tango (bloqueado por §4 sin resolver + §5 licencia).
