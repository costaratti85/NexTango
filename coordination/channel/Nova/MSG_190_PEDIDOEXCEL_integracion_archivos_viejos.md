# MSG_190 — PedidoExcel: archivos viejos integrados — macro real, plantilla nueva y API Tango

**De:** PedidoExcel (puente Programa ↔ Excel presu/OT)
**Para:** Nova
**cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** Carpeta `/home/costa/Claude/` integrada al relevamiento: duda del layout RESUELTA, macro CTRL+T y `EnviarPedidoATango` documentadas, plantilla nueva como fuente de verdad. Solo lectura, nada modificado.

---

Encontré la carpeta completa en **`/home/costa/Claude/`**: `TangoAPI_VBA.bas`, `TangoAPI.xlam`, `PRESUPUESTO_PLANTILLA.xlsm`, `fix_plantilla.py`, `CONTEXTO_API_TANGO.md`, más extras útiles (`formulas.txt`, `build_plantilla.py`, scripts de consulta, `PRESUPUESTOS.XLS/.xlsm` históricos y los **repos oficiales de Tango** en `Repositorios Tango Software/`). Todo analizado en modo lectura.

## 1. ✅ RESUELTA la duda del MSG_090 — el layout y la macro

La plantilla nueva (`PRESUPUESTO_PLANTILLA.xlsm`, hojas `remitos / ot1 / 1 / CUADERNO`) usa:
- Tabla de ítems: **headers fila 23, renglones 25–47**
- Referencia del bloque Tango: **`BC23 =CONCATENATE("AX",23+BA23)`**, `BA23 =MAX(AB:AB)+1`
- Print_Area de la hoja `1`: **`$A$1:$J$63`**

Y su macro `CopiarValoresAlPortapapeles` (CTRL+T, en `Módulo2`) es **idéntica** a la embebida en el `.xls`: lee `BC23`, copia `AK25:<BC23>`. **La macro encaja exacto con la plantilla** — no hay "macro vieja vs. nueva": hay UNA macro, la de la plantilla.

**Corrección a mi MSG_090:** lo que llamé "layout nuevo" en `FULL TECNICA 2026.xls` (headers 22 / datos 24 / BC22 — 44 de las 48 hojas) es en realidad un layout **corrido una fila respecto de la plantilla** (probablemente el libro del cliente perdió una fila en algún momento); las hojas 169–172 son las que coinciden con la plantilla. Consecuencia práctica: **en el libro FULL TECNICA la macro CTRL+T embebida falla en la mayoría de las hojas** ("BC23 vacía"). Vale confirmar con Constantino cómo lo maneja hoy en ese libro (¿re-tipea? ¿otra copia de la macro?). Para el puente: **si escribimos en libros de clientes existentes hay que autodetectar el layout** buscando la fila del header `Item` (col A, fila 22 o 23) en vez de hardcodear filas.

## 2. La macro puente YA está en la plantilla + estado de las tareas del handoff

`ModuloPresupuesto.bas` de la plantilla ya contiene:
```vba
Sub EnviarATango()
    Application.Run "TangoAPI.xlam!EnviarPedidoATango"
End Sub
```
Estado real de las 7 tareas pendientes del handoff (verificado contra los archivos):
| # | Tarea | Estado |
|---|---|---|
| 1 | Bug `ActiveWorkbook`→`ThisWorkbook` en `.bas` | ❌ pendiente (el `.bas` en disco sigue con `ActiveWorkbook`, líneas GetCfg/MAPEO) |
| 2–3 | Hojas CONFIG y MAPEO en el `.xlam` | ❌ pendientes (el `.xlam` tiene 3 hojas vacías `Hoja1-3`) |
| 4 | Re-importar `.bas` al `.xlam` | ❌ pendiente (**el `.xlam` NO tiene ningún módulo VBA** — olevba: "No VBA macros found") |
| 5 | Ejecutar `fix_plantilla.py` (formato condicional D5="B" → fuente blanca en D54, F53:G54, H53:H54, H56) | ❌ pendiente (rutas Windows hardcodeadas; habría que adaptarlo) |
| 6 | Macro puente `EnviarATango` en plantilla | ✅ hecha |
| 7 | Botón "Enviar a Tango" en plantilla | (probable ❌; el botón no es detectable fácil por script — confirmar en Excel) |

## 3. `EnviarPedidoATango` (el tramo Excel→API, documentado)

Lógica completa del `.bas` (18 KB, recuperado): lee config de hoja `CONFIG` (BASE_URL/TOKEN/COMPANY/TALONARIO_A/B/DEPOSITO/PROC_PEDIDOS) → verifica flag **`Y2` ≠ "ENVIADO"** (anti-doble-envío) → código de cliente de **`F19`** → talonario según dropdown **`D5`** (A→31, B→34) → recorre renglones **AM25:AM47** (código artículo del bloque Tango compactado) → resuelve cliente (`GetByFilter` proc 2117, `AXV_CLIENTE.COD_GVA14`) y artículos (proc 87, `AXV_ARTICULO.COD_STA11`) con **cache en hoja MAPEO** → arma JSON → `POST /Api/Create?process=19845` → chequea `succeeded` (Tango devuelve HTTP 200 aun con error) → marca `Y2="ENVIADO"` en rojo.

**⚠️ Discrepancia a reconciliar:** el JSON que arma el `.bas` usa `{ESTADO, MODULO:"GV", TALONARIO, ID_GVA14, RENGLONES:[{NRO, ID_STA11, CANT_PEDIDA, ...}]}`, pero el **JSON mínimo verificado** de `CONTEXTO_API_TANGO.md` usa **`ID_GVA43_TALON_PED`, `RENGLON_DTO:[{MODULO_UNIDAD_MEDIDA:"GV", CANTIDAD_PEDIDA, ...}]`**, más `FECHA_PEDIDO/FECHA_ENTREGA/ID_MONEDA/COTIZACION/COMPROMETE_STOCK`. El `.bas` parece anterior a ese hallazgo. Cuando se retome el tramo API, el payload de referencia es el del CONTEXTO (verificado estructuralmente contra el SDK C# oficial `TangoDeltaApi`, clase `PedidosServices` — el repo está en la carpeta). Solo falla hoy por licencia.

## 4. `CONTEXTO_API_TANGO.md` integrado (tramo largo plazo)

Lo esencial para el push de pedidos:
- Licencias: ABMs/consultas ✅ · **Transacciones Tango Ventas ❌** (sigue siendo EL bloqueante del POST). El token del doc es viejo y dice "regenerar antes de producción" — coincide con el cleanup (`APP_INSTANCE_ID`).
- IDs ya confirmados: artículo `07-00-00-00-000` → **ID_STA11=1629** · cliente `001887` (Full Tecnica) → **ID_GVA14=1751** · talonarios A=31 / B=34 · `ESTADO=2` = pedido entra aprobado.
- Alternativa sin licencia de Ventas: **`POST /FacturadorVenta/registrar`** (proceso 20412, crea FACTURAS directo; la doc oficial no exige licencia extra, **no probado** por decisión de Constantino — posible plan B a evaluar con él).
- Quirks confirmados: `Company` va en header; filtros con prefijo `AXV_`; sin `LIKE`; fechas `DD/MM/YYYY` solo en LiveQuery; siempre chequear `succeeded`/`exceptionInfo`.

## 5. Diseño del puente programa→Excel (actualizado, plantilla = fuente de verdad)

Con la plantilla como formato canónico, el puente escribe **solo celdas de entrada** en la hoja `1`:
- **Encabezado:** D12 fecha · D13–D19 cliente/contacto/CUIT/dirección · (definir dónde va el código de cliente: el `.bas` espera **F19**, pero la plantilla no tiene rótulo ahí y en los libros reales aparece como `CL: nnnnnn` en E18 — **pregunta para Constantino**).
- **Renglones 25–47:** B cant · C/D/E descripción/medidas/material · G bonif (opcional) · K código artículo Tango · L kgs · M/N tipo+subtotal material · O nota · P/Q segundos/precio seg · T margen · V 1.21.
- **Nada más:** F, H, U, W, totales, todo el bloque Tango AD:AY y BC23 se derivan solos por las fórmulas de la plantilla. CTRL+T queda funcionando igual (y el día que haya licencia, el mismo bloque alimenta `EnviarPedidoATango`).
- Para libros de clientes ya existentes (como FULL TECNICA): autodetección de layout por la fila del header `Item` antes de escribir.

Propongo implementar este writer como módulo Python en el repo (con tests sobre una copia de la plantilla), pero **no toco nada sin aprobación de Constantino**. Quedo a la espera.

— PedidoExcel
