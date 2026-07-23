# 🟡 PROPUESTA — SPLIT del máster de artículos por prefijo (ferretería "06-" → ERPNext)

**Estado:** 🟡 **PROPUESTA — NO confirmada. NO es canon.** Requiere **ratificación explícita de Constantino**.
**Origen:** Constantino, con **"creo que"** — sigue siendo propuesta, no definición.
**Registrado por:** Nova · **Fecha:** 2026-07-22
**Acotación 2026-07-22:** NO es invertir todo el catálogo. Es un **split por tipo de producto** (ver §1). Mucho menos riesgoso.

---

## ⚠️ Por qué esto va con guantes

Esto es un **cambio de fuente de verdad** — el mismo tipo de cambio que, cuando se **asumió mal**, nos costó la errata de precios (~16 documentos + código contaminados, tres correcciones, la crítica de Constantino). La lección de `DECISION_011` fue explícita:

> **La dirección de un flujo de datos es parte del modelo.** Un cambio de dirección no es un detalle: reescribe quién es el dueño del dato, y el error se propaga a la documentación y a las decisiones.

Por eso este documento **no cambia nada** del canon vigente. Solo:
1. registra la propuesta,
2. marca qué habría que actualizar **SI** se confirma,
3. la manda al brief para **ratificación explícita**.

**Hasta que Constantino diga "sí, confirmado" con esas palabras, el canon vigente sigue mandando.**

---

## 1. Qué propone Constantino — un SPLIT por prefijo de código, NO invertir todo

El máster de artículos queda **partido por tipo de producto**:

| Segmento | Código | Máster propuesto | Sync |
|---|---|---|---|
| **Ferretería** (comercial, sin procesamiento) | empieza con **`06-`** | → **ERPNext** | ERPNext → Tango (Excel plantilla actualización masiva) |
| **Caños, chapas, material PROCESADO** | otros prefijos | **Tango** (SIN CAMBIOS) | como hoy |

- Solo **ferretería `06-`** cambia de dueño. Todo lo procesado sigue con el canon actual.
- **Por qué es coherente:** la ferretería es el segmento **puramente comercial** de Constantino, el que alimenta el **OCR de proveedores** (compras → stock → catálogo). Tiene sentido que ese lo maneje entero desde ERPNext. No es un capricho: es alinear el dueño con quién opera el dato.
- **Por qué es de bajo riesgo:** son **~50 artículos** (Item Group Ferretería), no los 2.189. El resto del catálogo no se toca.

## 2. Qué dice el canon HOY (lo que esto ACOTA, no invierte)

`SOURCE_OF_TRUTH_MATRIX` hoy: **lista de artículos → TANGO** (para todo).

La propuesta lo **parte**: `06-` → ERPNext; resto → Tango. No es "dar vuelta el modelo definitivo del 2026-07-19" — es **acotar una excepción** a un segmento comercial. Sigue exigiendo **ratificación** (es cambio de fuente de verdad, aunque quirúrgico), pero el riesgo es chico y la lógica es clara.

## 3. 🔴 Documentos/decisiones a actualizar SI se confirma (NO tocar todavía)

Dejo el mapa listo para ejecutar **rápido y completo** el día que se confirme — y para que se vea el **tamaño del cambio** antes de aprobarlo:

| Documento | Qué cambia |
|---|---|
| `SOURCE_OF_TRUTH_MATRIX` | Fila "Lista de artículos" → **split**: `06-` ERPNext (dir. ERPNext→Tango), resto Tango |
| `DECISION_018` (PedidoExcel) | Frontera "Tango máster del catálogo" → aclarar que ferretería `06-` es ERPNext |
| `DECISION_016` (OCR) | Para ferretería `06-`: artículo nuevo → **ERPNext** → se empuja a Tango. (El OCR es justo de proveedores de ferretería → encaja) |
| Memoria `carga-articulos-erpnext` | Notar el split por prefijo |
| Código `tango_sync/article_push.py` | Hoy empuja Tango → ERPNext. Para `06-` haría falta un **export** ERPNext → Tango (lo diseña Forge). El push existente **no se toca** para el resto |
| Brújula §3 (flujo OCR) | "agregar a Tango" → para ferretería, "agregar a ERPNext y empujar a Tango" |

**Riesgo — ahora chico:** el segmento afectado es **ferretería (~50 artículos)**, no los 2.189. Aun así, definir el **delta** (qué es "cambio" en ERPNext que se empuja a Tango) y no re-empujar a ciegas los `06-` que Tango ya tiene. Escritura a Tango = zona fiscal → aprobación de Constantino. Con 50 items es **manejable y auditable**, muy distinto del escenario de invertir todo.

## 4. Qué está haciendo Forge (como PROPUESTA, no ejecución)

Constantino ya le pidió a Forge **diseñar el export ERPNext → Tango** en el formato de la plantilla de actualización masiva. **Es diseño/propuesta** — no se importa nada a Tango, no se cambia el máster. Encaja en el modo noche (investigación). El diseño sirve **igual** aunque la inversión no se confirme (un export a Tango puede ser útil sin invertir el máster).

## 5. Qué necesito de Constantino

Una sola cosa, explícita: **¿confirmás invertir el máster de artículos a ERPNext, o era pensarlo en voz alta?**

- Si **sí** → ejecuto el mapa de §3 de una, y coordino con Forge/Tango el delta seguro contra los 2.189 existentes.
- Si **no / todavía no** → el canon vigente sigue (Tango máster), y el export de Forge queda como herramienta disponible sin cambiar la fuente de verdad.

**Nadie cambia el máster ni escribe a Tango hasta esa palabra.**
