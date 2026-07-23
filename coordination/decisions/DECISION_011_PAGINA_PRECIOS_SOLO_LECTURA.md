# DECISION_011 — EXCEL es el máster de precios. Tango es destino, nunca fuente.

**Fecha:** 2026-07-19 · **Definido por:** Constantino · **Registrada por:** Nova
**Estado:** Vigente — **modelo de pricing canónico de todo el proyecto**
**Afecta a:** Vega, Orbit, Atlas, Tango, Punto + `DECISION_003`, `DECISION_016`, Source of Truth Matrix y ~16 documentos del canon (en purga)

> ⚠️ Esta decisión **corrige una errata propagada** por todo el proyecto — incluido el documento
> fundacional y el código. Se escribió y reescribió tres veces. El historial (§6) se deja a
> propósito. **Si algún documento contradice esta decisión, manda esta decisión.**

---

## 0. 🟢 EL MODELO DEFINITIVO DE FUENTES DE VERDAD

Constantino, 2026-07-19 — *"así va a ser"*:

| Concepto | Máster |
|---|---|
| **Lista de artículos / catálogo** | **TANGO** |
| **Stock** | **ERPNext** |
| **Precios** | **EXCEL** |

**Cada uno es máster de lo suyo.** Este es EL modelo; el resto de esta decisión desarrolla la parte de precios.

## 1. 🟢 LA REGLA — máster, destino y dirección

> ## **EXCEL es el MÁSTER de precios. Los precios NACEN en Excel. Punto final.**
> ## **TANGO es DESTINO / COPIA. NUNCA la fuente. NUNCA el máster.**

### La dirección del flujo — lo que hay que grabarse

```
        ✅ CORRECTO                              ❌ PROHIBIDO

   EXCEL ──push──▶ TANGO                    TANGO ──pull──▶ sistema
   (máster)      (destino/copia)            (jamás: Tango no es fuente)
```

**`Excel → Tango` (push). NUNCA `Tango → sistema` (pull).**

**Esta inversión de dirección fue la raíz de toda la errata.** El código muerto `sync_from_tango.py` iba **al revés** — traía precios *desde* Tango— y de ahí se propagó la idea falsa de que "Tango es maestro de precios" a ~16 documentos del canon. **Cualquier cosa que lea precios desde Tango hacia el sistema está mal por construcción**, sin importar qué documento la respalde.

## 2. Los tres estados: hoy, futuro deseable, prohibido

| | Qué | Estado |
|---|---|---|
| **HOY** | El **vendedor carga los precios a mano** cada mañana en nuestro sistema (página **editable**) y los usa todo el día | ✅ **Vigente** — mecanismo oficial, no un parche |
| **FUTURO 1** | **Import Excel → nuestro sistema**, reemplaza la carga manual | 🔜 A desarrollar |
| **FUTURO 2** | **Push Excel → Tango**, para que alguien pueda **facturar directamente desde Tango** si quiere | 🔜 *Nice-to-have*, parte del flujo de Excel |
| **NUNCA** | Pull **Tango → sistema** para traer precios | ❌ **Prohibido** |

**Lo de hoy no cambia:** carga manual del vendedor. El push a Tango es un deseable futuro, no un requisito.

## 3. Por qué Tango recibe precios (y por qué eso NO lo hace máster)

Es deseable que los precios **lleguen** a Tango para que alguien pueda **facturar directamente desde ahí** si le conviene.

**Que Tango tenga precios no lo convierte en su dueño.** Tango es el **último** eslabón de la cadena, no el primero:

```
EXCEL (máster) ──▶ nuestro sistema ──▶ TANGO (copia, para facturar)
```

Si un precio en Tango difiere del de Excel, **el correcto es el de Excel** y Tango está desactualizado — nunca al revés.

**Regla práctica para cualquier agente:** ¿estás por leer un precio *desde* Tango? **Pará.** Estás yendo en la dirección prohibida.

## 4. La página de precios: EDITABLE

- ✅ El vendedor **guarda**: precio por **kg por familia**, precio por **segundo de láser**, precio por **plegado**.
- ✅ **Guardado real + feedback.**
- ❌ **Nada** de "solo lectura". **Nada** de "sincronización desde Tango" — esa leyenda es la errata hecha interfaz.
- Es pantalla de **uso diario y rápido** (primera tarea del vendedor a la mañana), no de configuración ocasional.

## 5. Documentos corregidos por esta decisión

| Documento | Qué decía mal | Corrección |
|---|---|---|
| **Brújula regla 4** | *"Tango es maestro de precios finales — ERPNext sincroniza copia"* | 🔴 **Errata del canon fundacional.** No se edita `00_BRUJULA_*` (documento de Constantino) — consulta pendiente. Esta decisión manda sobre la regla 4 en materia de precios |
| `DECISION_003` | "Excel → **Tango precios maestros** → cache" | Excel es el **máster**; Tango es destino |
| `SOURCE_OF_TRUTH_MATRIX` | "Precio de venta final → 🔴 TANGO" | → **📗 EXCEL** |
| `DECISION_016` (OCR) | "...→ precios a Tango" | El OCR **no** empuja precios a Tango |
| `TANGO_ERPNEXT_FIELD_MAPPING` | *"los cambios de precio se originan en Tango"* | ❌ Se originan en **Excel** |
| `TASK_003/006_TANGO_PRICE_CACHE` | Cachear precios de Tango | **Obsoletas** — dirección invertida |
| Código `pricing_sync/`, `sync_from_tango.py` | Pull desde Tango | ❌ Dirección prohibida — en auditoría |
| `DECISION_006` | ✅ **Correcta** | Habla de **qué artículo se factura** ("chapa procesada"), no de dónde salen los precios. Tango factura; el precio nace en Excel. Conviven |

## 6. Historial — tres versiones, una errata de raíz

1. **Error 1.** Nova declara la página **de solo lectura**, razonando desde Brújula regla 4. No verificó de dónde salían los precios.
2. **Señal perdida.** Vega escala que *"el sync Tango→`precio_por_kg` no existe"*. **Era la evidencia de que el modelo estaba mal.** Nova lo lee como un hueco a implementar.
3. **Corrección parcial.** Constantino: los precios vienen de Excel, el vendedor carga a mano → página **editable**. Nova corrige la página pero **mantiene** "Tango maestro de precios finales" en el mapeo — sigue arrastrando el error.
4. **Corrección de fondo.** Constantino: **Tango no maneja precios.**
5. **Refinamiento final (esta versión).** Constantino precisa: **Excel es el máster**; Tango **sí puede recibir** precios (para facturar desde ahí), pero como **destino**; dirección **Excel → Tango**, **jamás** al revés. **El `sync_from_tango.py` invertido era la raíz de todo.**

**Causa raíz:** Nova decidió arquitectura sobre **lectura incompleta**, y el canon **propagaba la errata** (Orbit, MSG_161: *"leer más no lo habría corregido — la fuente estaba mal de raíz"*).

**Lecciones para el equipo:**
- Antes de aplicar una regla del canon a un dato concreto, **verificar de dónde sale ese dato**.
- Cuando un agente reporta que una pieza esperada **no existe**, eso es una **hipótesis sobre el modelo**, no solo trabajo faltante.
- **La dirección de un flujo de datos es parte del modelo.** Un sync en el sentido equivocado no es un bug aislado: reescribe quién es el dueño del dato, y el error se propaga a la documentación y a las decisiones.

---

## 7. 📗 El modelo correcto SÍ estaba escrito — en lo que no se había leído

Constantino avisó que en el documento de **OCR de proveedores** *"estaba bien especificado"*. **Verificado — es cierto.**

`docs/05_OCR_SUPPLIERS_FLOW.md`, líneas 6-8:

> - artículos/proveedor a **Tango**
> - stock a **ERPNext**
> - costos a **Excel**

**Son exactamente los tres másters del modelo definitivo**, escritos antes de toda esta discusión.

### Lo que esto corrige de mi diagnóstico

Yo había concluido —siguiendo a Orbit (MSG_161)— que *"el modelo correcto no estaba escrito en ningún lado; leer más no lo habría corregido"*. **Era falso.** Estaba escrito, en tres líneas, en un documento que quedó del lado de los ~292 sin leer.

O sea: **la crítica original de Constantino era la correcta**, más que mi matiz posterior. Hubo dos problemas, no uno:
1. El canon **propagaba** la errata (~16 docs) — cierto.
2. Y **también** existía la definición correcta, y no la habíamos leído — que es lo que él venía diciendo desde el principio: *"sigue habiendo documentos del proyecto sin leer si tengo que estar explicando esto"*.

### Y no es casualidad dónde estaba

Apareció en el flujo de **OCR de proveedores** — el mismo territorio que Constantino marcó como **"parte clave del programa"** (`DECISION_016`) y que yo había propuesto dejar **sin dueño** por no tener frente activo. El documento que tenía la respuesta pertenecía justo al área que subestimé.

**Lección:** el valor de un documento no se mide por si su frente está activo hoy.
