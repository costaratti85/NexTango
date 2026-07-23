# Propuesta — Exportar artículos de ERPNext → plantilla de Tango (STA11)

**De:** Forge · **Para:** Constantino (vía Nova) · **Fecha:** 2026-07-14
**Estado:** DISEÑO / investigación. **No construí ni cargué nada.**
**Contexto:** modelo nuevo (a confirmar) = **ERPNext es el máster del catálogo**; cada cambio de artículo en ERPNext se baja a Tango generando el Excel de "actualización masiva" (hoja "Artículos", 98 columnas, proceso STA11 = 87).

---

## 0. La pregunta que define TODO el diseño (necesito respuesta)

Cuando Tango importa esta plantilla, una celda **vacía**, ¿qué hace?
- **(A) La ignora** → solo actualiza las columnas que llenamos, y deja el resto del artículo como está en Tango. → **Nos alcanza con llenar Código + las pocas columnas que ERPNext realmente domina.** Simple y seguro.
- **(B) La sobrescribe con vacío** → si mandamos una columna vacía, **borra** ese dato en Tango. → Tendríamos que llenar **las 98 correctamente** o arruinamos la ficha del artículo en Tango.

**Todo el resto de la propuesta cambia según esto.** Hay que confirmarlo con el proveedor de Tango o probándolo con 1 artículo. **Yo recomiendo asumir (B) hasta que se pruebe** (es lo prudente), pero diseñar para poder hacer (A) apenas se confirme.

Relacionado: la última columna **`ROW_VERSION`** y las "claves" internas del archivo (hoja `_metadata`) son mecanismos de **control de versión** de Tango. Es muy probable que Tango exija que el archivo **salga de su propia descarga** (con esas claves) y que solo le peguemos las filas — ver §5, es clave.

---

## 1. Qué tiene ERPNext HOY para llenar (la realidad)

De las 98 columnas de Tango, ERPNext **hoy solo tiene datos genuinos para ~6**, porque el sync original (`article_push.py`) trajo poco: código, nombre, categoría, unidad, descripción y el flag de stock. Todo lo demás (impuestos, escalas, perfiles, AFIP…) **nunca se importó a ERPNext**, así que no está.

Campos disponibles en el Item de ERPNext (los útiles): `item_code`, `item_name`, `item_group`, `stock_uom`, `sales_uom`, `purchase_uom`, `description`, `is_stock_item`, `is_sales_item`, `is_purchase_item`, `brand`, `gst_hsn_code`, `barcodes` (tabla), `valuation_rate`, `last_purchase_rate`, `si_tango_id`, `variant_based_on`, `has_variants`.

**Conclusión temprana:** para un round-trip fiel hay dos caminos (§6): o **Tango conserva lo suyo** (caso A) o **enriquecemos ERPNext** guardando los campos de Tango que hoy no tiene.

---

## 2. Mapeo campo por campo (98 columnas)

Leyenda: 🟢 **Directo** (sale tal cual de un campo) · 🟡 **Transformar** (necesita conversión) · ⚪ **Default/constante** · 🔴 **Gap / lo define Constantino** (ERPNext no lo tiene).

### Identidad del artículo (lo que ERPNext SÍ domina)
| Col | Columna Tango | Origen ERPNext | Tipo |
|---|---|---|---|
| E (5) | **Código** | `item_code` (= COD_STA11, ya es el mismo) | 🟢 |
| F (6) | **Descripción** | `item_name` | 🟢 |
| G (7) | Descripción adicional | (parte del `description` / vacío) | ⚪/🔴 |
| H (8) | Sinónimo | vacío (no lo guardamos hoy) | 🔴 |
| I (9) | Código de barras | `barcodes[0].barcode` si existe | 🟡 |
| CQ/CR (95/96) | Observaciones / Comentarios | vacío o `description` | ⚪ |

### Categoría / clasificación
| Col | Columna Tango | Origen ERPNext | Tipo |
|---|---|---|---|
| J (10) | **Código de base** | ⚠ Tango arma el código por familia/base; ERPNext solo tiene `item_group`. **Reverso ambiguo** (ver §3) | 🔴 |
| C (3) | Tipo | relacionado a escalas; casi todos "sin escala" | 🔴 |
| D (4) | Escala | idem | 🔴 |
| K/L (11/12) | Código de valor de escala 1/2 | idem (variantes) | 🔴 |
| M (13) | Perfil | A=Compra-Venta / V / C / N. Derivable de `is_sales_item`+`is_purchase_item` | 🟡 |
| AI (35) | Código de tipo bien | lookup Tango (vacío en la muestra) | 🔴 |

### Unidades
| Col | Columna Tango | Origen ERPNext | Tipo |
|---|---|---|---|
| AP (42) | **UM de stock 1** | `stock_uom` → **código Tango** (lookup) | 🟡 |
| AT (46) | UM de stock 2 | vacío | ⚪ |
| AZ (52) | Presentación de ventas | `sales_uom`→código, o vacío | 🟡/⚪ |
| AV/BA/CC… | Equivalencias UM | 1 por defecto, o vacío | ⚪ |
| CK (89) | Código de tipo de unidad | AFIP/turismo | 🔴 |

> ⚠ **Alerta de unidades:** el lookup de unidades de ESTE Tango solo lista `UNIDAD / SINUNIDAD / MESES / AÑOS` — **no aparecen KG / METRO / M²**, que sí usa el taller y sí están del lado ERPNext. La equivalencia UOM(ERPNext) → código MEDIDA(Tango) **está sin resolver** y la tiene que confirmar Constantino / el proveedor de Tango.

### Stock y comportamiento
| Col | Columna Tango | Origen ERPNext | Tipo |
|---|---|---|---|
| O (15) | **Lleva stock** | `is_stock_item` (hoy 0 → "No"). ⚠ codificación `true/false` | 🟡 |
| P (16) | Lleva partidas | vacío/false | ⚪ |
| Q/AD (17/30) | Descarga stock negativo (compras/ventas) | `allow_negative_stock` o default | 🟡/⚪ |
| R/S (18/19) | Método / Orden de descarga | default (NRO / A) | ⚪ |
| U/V/W (21-23) | Series / Scrap / % scrap | vacío/false/0 | ⚪ |
| AQ/AR/AS (43-45) | Stock máx / mín / punto pedido | `safety_stock` o vacío | ⚪/🔴 |

### Comercial / precios / impuestos (dominio hoy de Tango)
| Col | Columna Tango | Origen ERPNext | Tipo |
|---|---|---|---|
| A (1) | Permite venta fraccionada | default (true/false) | ⚪ |
| B (2) | Código de proveedor habitual | `supplier_items` / vacío | 🔴 |
| Y/Z/AA (25-27) | % comisión / bonificación / utilidad | vacío/0 | 🔴 |
| BB (54) | **Código de IVA Ventas** | lookup Tango (1/2/3). ERPNext no lo guarda | 🔴 |
| BC–BT (55-72) | Percepciones IVA/IIBB/Imp. internos, IVA Compras… | **todo lookup fiscal Tango** | 🔴 |
| BV (74) | Producto terminado | default (S/N) | ⚪ |
| BW (75) | Código único de producto | vacío | 🔴 |
| CF (84) | Código NCM | `gst_hsn_code` si se carga, si no vacío | 🟡/🔴 |
| CP (94) | Publica en Tango Tiendas | default (true/false) | ⚪ |

### Vigencias, AFIP, exportación, comprobantes electrónicos
| Col | Columnas | Tipo |
|---|---|---|
| N/AN/AO (14/40/41) | Fecha de alta / Vigente desde / hasta | ⚪ (fecha o vacío) |
| CI–CO (87-93) | Tipo de ítem AFIP, ítem turismo, SIAp Ventas/Compras, actividad económica, modelo percepciones | 🔴 (fiscal, sin equivalente) |
| BX–CE, CG/CH (76-83, 85-86) | UM/presentación para transporte de bienes y comprobantes electrónicos/exportación | ⚪/🔴 |

### Columnas de control del propio archivo
| Col | Columna | Qué hacer |
|---|---|---|
| CS (97) | **Eliminar** | "No"/vacío en export normal; "Sí" solo para bajas | 🟡 |
| CT (98) | **ROW_VERSION** | control de concurrencia de Tango — ⚠ ver §5, casi seguro hay que traerlo de Tango | 🔴 |

**Resumen del mapeo:** 🟢 directo ≈ 2-3 columnas · 🟡 transformar ≈ 8-10 · ⚪ default/constante ≈ 25-30 · 🔴 **gap por definir ≈ 55-60**. Es decir: **hoy, la mayoría de la plantilla no tiene origen en ERPNext.**

---

## 3. Transformaciones necesarias (las 🟡)

1. **Booleanos con DOS codificaciones distintas** (ojo, no es uniforme):
   - `true/false` → columnas: Lleva stock, Permite venta fraccionada, Publica en Tiendas, GENERACOT…
   - `S/N` → columnas: Es remitible, Producto terminado…
   El generador tiene que saber qué codificación usa cada columna (lo tengo relevado de las hojas de referencia del archivo).
2. **Unidad:** `stock_uom` ERPNext (Nos/Kg/Meter/Square Meter) → **código MEDIDA de Tango**. Tabla inversa del `_UOM_MAP` del sync, PERO incompleta (ver alerta de unidades). **Gap a cerrar.**
3. **Perfil (col M):** `is_sales_item` + `is_purchase_item` → `A` (ambos) / `V` (solo venta) / `C` (solo compra) / `N`.
4. **Categoría → familia / código de base (col J, C, D):** el sync original mapeó **7 familias de Tango → 5 Item Groups** (muchos-a-uno, con pérdida). El **reverso es ambiguo**: "Tubos y Perfiles" puede ser "01 - PERFILERIA" **o** "02 - TUBOS ESTRUCTURALES". No se puede reconstruir sin una regla o sin guardar el dato original. → **Gap central (ver §6).**
5. **Código de barras:** de la tabla `barcodes` del Item (si se cargó).

---

## 4. Gaps: columnas de Tango SIN equivalente hoy en ERPNext (las 🔴)

Constantino tiene que definir, para cada bloque, **de dónde sale o si Tango lo conserva**:

- **Escalas / variantes** (Tipo, Escala, valores de escala 1/2, código de base): cómo se modela en ERPNext (¿variantes de Item? ¿o todos "sin escala"?).
- **Fiscal / impositivo** (IVA ventas y compras, percepciones IVA/IIBB, impuestos internos, alícuotas): hoy **no vive en ERPNext**. ¿Lo sigue manejando Tango (caso A) o hay que cargarlo en ERPNext?
- **AFIP / electrónicos** (tipo de ítem AFIP, NCM, SIAp, turismo, comprobantes electrónicos y de exportación): idem.
- **Comercial** (proveedor habitual, % comisión/bonificación/utilidad, listas de precios): ¿ERPNext pasa a ser dueño de esto?
- **Reverso categoría→familia/código de base** (§3.4).
- **ROW_VERSION** (§5).

**Mientras estos gaps no se definan, el export solo puede ser fiel en el bloque "identidad + categoría + unidad + stock".** El resto depende del caso A/B (§0).

---

## 5. Cómo se generaría el Excel — y el riesgo técnico importante

**⚠ Riesgo: NO conviene fabricar el .xlsx desde cero.** El archivo de Tango tiene **81 hojas** (la de artículos + 80 de listas de referencia) y una hoja oculta **`_metadata`** con **claves internas comprimidas** (una por hoja, tipo `H4sIA…`) y el número de proceso (`access = 87`). Tango probablemente **valida esas claves** al importar. Si generamos un workbook nuevo sin ellas, es muy posible que **Tango rechace el archivo**.

**Enfoque recomendado (seguro):**
1. Partir de **la plantilla oficial descargada de Tango** (la que ya tenemos vacía) como "molde".
2. Un **script** abre ese molde, y **solo pega las filas** de artículos en la hoja "Artículos" (respetando las 98 columnas), sin tocar las otras 80 hojas ni `_metadata`.
3. Guarda el archivo resultante listo para subir.

Esto preserva las claves/estructura que Tango espera y nos limita a lo que controlamos: las filas.

**Dónde se dispara y dónde cae el archivo** (opciones, a elegir con Constantino):
- **(a) Botón en una página de ERPNext** ("Exportar artículos a Tango") → genera y **descarga** el .xlsx. Simple para uso manual.
- **(b) Script programado** que deja el archivo en el **share Samba** `\\190.190.190.20\compartida\intercambio\` (o una subcarpeta `tango_export\`), para que Constantino lo tome desde Windows y lo suba a Tango. Bueno para tanda periódica.
- **(c) Report de Frappe** exportable: **descartado** para el archivo final — un report exporta una tabla plana, no puede reproducir el workbook multi-hoja con `_metadata`. Sirve, a lo sumo, como vista previa de las filas.

Recomiendo **(a) para empezar** (control manual, Constantino revisa antes de subir) y dejar (b) para cuando el flujo esté aceitado.

---

## 6. Cómo detectar "qué cambió" (exportar solo cambios)

- **Primera vez:** exportar **todo** (los 2.189). Es la línea base.
- **Incremental, opción simple (recomendada para arrancar):** cada Item de ERPNext tiene fecha de **última modificación** (`modified`). Guardamos la fecha del último export y exportamos solo los Items con `modified > último_export`. Cero campos nuevos, funciona ya.
- **Incremental, opción robusta:** un **flag "pendiente de Tango"** (custom field `si_tango_dirty`) que se **prende solo** cuando cambia un artículo (vía hook de ERPNext) y se **apaga** al exportar. Es más preciso (distingue "cambió algo que a Tango le importa" de "se tocó un campo irrelevante"), pero requiere construir el hook.
- **Bajas:** para borrar en Tango, esos artículos van con la columna **"Eliminar" = Sí** (no se borran de ERPNext salvo que se decida).

**Recomendación:** arrancar con el **watermark por `modified`** (nada que construir salvo el generador) y evaluar el flag `dirty` si hace falta más precisión.

---

## 7. El camino robusto para "máster en ERPNext" (recomendación de fondo)

Si de verdad ERPNext pasa a ser el máster, lo prolijo es que **ERPNext guarde lo que hoy no tiene** de cada artículo, para que el round-trip sea fiel y sin ambigüedad. Dos sub-opciones:
- **Mínima (caso A):** ERPNext domina solo **catálogo** (código, nombre, categoría, unidad, descripción, barras, alta/baja); **Tango sigue dueño de lo fiscal**. El export llena solo esas columnas y confía en que Tango conserva el resto. **Requiere confirmar el caso A (§0).**
- **Completa (caso B):** al importar de Tango, **guardar en ERPNext los campos Tango que faltan** (familia original, código de base, escalas, códigos fiscales, ROW_VERSION) en **custom fields** o en un doctype compañero "Datos Tango del Artículo". Así el export reconstruye las 98 columnas sin adivinar. Más trabajo, pero es lo correcto si ERPNext manda de verdad.

Esto es una **decisión de alcance de Constantino**, no técnica: ¿ERPNext dueño solo del catálogo, o también de lo fiscal/comercial?

---

## 8. Lo que necesito que defina Constantino

1. **(Crítico) Caso A o B del §0:** ¿Tango ignora las celdas vacías o las sobrescribe? (confirmar con el proveedor o probando 1 artículo).
2. **Alcance del máster:** ¿ERPNext dueño solo del **catálogo**, o también de **fiscal/comercial**? (define §6/§7 y cuántos gaps hay que llenar).
3. **Unidades:** el mapa `stock_uom` ERPNext ↔ código MEDIDA de Tango (KG/METRO/M² no aparecen en la plantilla).
4. **Escalas/variantes:** ¿los artículos usan escalas en Tango o van "sin escala"?
5. **Reverso categoría→familia** (§3.4): regla, o aceptamos guardar la familia original al importar.
6. **Disparo/entrega del archivo:** botón con descarga (a) vs archivo al share (b).

---

### En una frase
Técnicamente el export es viable **pegando las filas de ERPNext sobre la plantilla oficial de Tango** (no fabricando el Excel de cero, que Tango probablemente rechace). Pero **hoy ERPNext solo tiene ~6 de las 98 columnas**; que el round-trip sea completo o mínimo depende de **una decisión de Constantino** (¿ERPNext dueño de todo o solo del catálogo?) y de **una prueba** (¿Tango pisa las celdas vacías?).

— Forge
