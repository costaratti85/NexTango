# Propuesta (v2, alcance acotado) — Exportar SOLO Ferretería de ERPNext → Tango

**De:** Forge · **Para:** Constantino (vía Nova) · **Fecha:** 2026-07-14
**Estado:** DISEÑO / investigación. **No construí ni cargué nada.**
**Reemplaza el alcance** de `FORGE_PROPUESTA_EXPORT_ERPNEXT_A_TANGO.md`: ese cubría todo el catálogo; **este cubre SOLO ferretería.** El mecanismo de generación y la advertencia del archivo siguen valiendo igual.

**Alcance nuevo (definición de Constantino):**
- **Ferretería = todos los artículos cuyo código empieza con `06-`.** Es puramente comercial (sin procesamiento). **Su máster pasa a ERPNext** y se baja a Tango con la plantilla de actualización masiva.
- **Todo lo demás** (caños, chapas, material procesado) **NO se toca**: sigue con Tango como máster. Este export los **excluye**.

---

## 1. Confirmación del alcance contra los datos reales (consultado en vivo)

| Chequeo | Resultado |
|---|---|
| Items con `item_code` que empieza en `06-` | **50** |
| Items en el grupo "Ferretería" | **50** |
| `06-` que NO están en "Ferretería" | **0** |
| "Ferretería" que NO empieza con `06-` | **0** |

**Coinciden exactamente.** O sea: el prefijo `06-` y la categoría "Ferretería" son hoy lo mismo. Esto **elimina la ambigüedad** que tenía el diseño general (donde 7 familias caían en 5 grupos con pérdida). Acá es 1 a 1.

**Cómo se filtra en ERPNext:** por el campo **`item_code`** con el patrón `06-%` (es el criterio que definió Constantino y el más robusto: no depende de que alguien renombre la categoría). El grupo "Ferretería" daría el mismo resultado hoy, pero el código es la fuente de verdad.

Muestra real de estos 50 (todos uniformes):
- Código tipo `06-01-01-00-001`, nombre p.ej. "Electrodos 2,00 mm Conarco 13A".
- **Unidad:** "Nos" (unidad) en todos · **Compra y venta:** sí en todos · **Lleva stock:** no (hoy) · tienen su `si_tango_id`.

---

## 2. Por qué este alcance es MUCHO más simple

Los 3 problemas grandes del diseño general **desaparecen o se achican** para ferretería:

| Problema del diseño general | En ferretería |
|---|---|
| Reverso categoría→familia **ambiguo** (muchos-a-uno) | ✅ **Resuelto**: Ferretería → familia **"06 - FERRETERIA"**, valor único |
| Unidades sin KG/METRO/M² en la plantilla | ✅ **No aplica**: ferretería es por **UNIDAD** (la plantilla sí tiene "UNIDAD"). Mapeo trivial `Nos → UNIDAD` |
| Escalas/variantes complejas | ✅ Ferretería va **sin escala** (artículos simples de reventa) |
| Perfil variable | ✅ **Uniforme**: todos compra+venta → Perfil **"A"** |
| Muchos-a-uno, 2.189 artículos | ✅ Solo **50 artículos**, homogéneos |

Lo único que **sigue igual** es la parte fiscal (IVA, percepciones) y el mecanismo del archivo (§5 del doc general). Pero al ser 50 artículos, se puede **probar con 1** y validar todo el circuito barato.

---

## 3. Mapeo campo por campo — SOLO ferretería (98 columnas)

Leyenda: 🟢 directo · 🟡 transformar · ⚪ default/constante (igual para los 50) · 🔴 gap por definir.

### Lo que ERPNext llena bien para ferretería
| Col | Columna Tango | Valor para ferretería | Tipo |
|---|---|---|---|
| E (5) | **Código** | `item_code` (ya es el mismo de Tango) | 🟢 |
| F (6) | **Descripción** | `item_name` | 🟢 |
| G (7) | Descripción adicional | vacío (o parte de `description`) | ⚪ |
| H (8) | Sinónimo | vacío | ⚪ |
| I (9) | Código de barras | `barcodes[0]` si existe, si no vacío | 🟡 |
| M (13) | **Perfil** | **"A"** (compra-venta) — constante | ⚪ |
| AP (42) | **UM de stock 1** | **"UNIDAD"** (de `Nos`) — constante | 🟡→trivial |
| O (15) | **Lleva stock** | `is_stock_item` → hoy **false/"No"**. ⚠ ver §6 (¿quieren stock de ferretería?) | 🟡 |
| CS (97) | Eliminar | "No" (o "Sí" solo para dar de baja) | ⚪ |
| CQ/CR (95/96) | Observaciones / Comentarios | vacío | ⚪ |

### Categoría / código
| Col | Columna Tango | Ferretería | Tipo |
|---|---|---|---|
| J (10) | Código de base | familia fija **"06 - FERRETERIA"**; el "código de base" propio del artículo, a confirmar si Tango lo pide en updates | 🟡/🔴 |
| C (3) / D (4) | Tipo / Escala | "sin escala" | ⚪ |
| K/L (11/12) | Valores de escala 1/2 | vacío | ⚪ |
| AI (35) | Código tipo bien | lookup Tango, vacío | 🔴 |

### Stock / comportamiento (constantes para los 50)
| Col | Columnas | Valor | Tipo |
|---|---|---|---|
| P,Q,AD,R,S,T,U,V,W (16-23,30) | Partidas, descarga negativo, método/orden, series, scrap | defaults (false / NRO / A / 0) | ⚪ |
| AQ/AR/AS (43-45) | Stock máx/mín/punto pedido | vacío (o según §6 si llevan stock) | ⚪/🔴 |

### Fiscal / comercial — los gaps que quedan
| Col | Columna Tango | Ferretería | Tipo |
|---|---|---|---|
| BB (54) | **Código de IVA Ventas** | **no está en ERPNext** (probablemente IVA 21% = código 1, pero hay que confirmarlo) | 🔴 |
| BC–BT (55-72) | Percepciones IVA/IIBB, imp. internos, IVA compras | no está en ERPNext | 🔴 |
| B (2) | Proveedor habitual | `supplier_items` / vacío | 🔴 |
| Y/Z/AA (25-27) | % comisión / bonificación / utilidad | vacío/0 | 🔴 |
| CF (84) | NCM | `gst_hsn_code` si se carga, si no vacío | 🔴 |

### Resto (vigencias, AFIP, exportación, comprobantes electrónicos, transporte)
| Col | Columnas | Ferretería | Tipo |
|---|---|---|---|
| N/AN/AO, CI–CO, BX–CH, CP, BV… | fechas, tipo ítem AFIP, SIAp, turismo, comprobantes electrónicos/exportación, tiendas, producto terminado | vacío / default | ⚪/🔴 |
| CT (98) | **ROW_VERSION** | control de versión de Tango — casi seguro hay que traerlo de Tango | 🔴 |

**Reparto para ferretería:** 🟢/⚪ (directo o constante conocido) ≈ **30-35 columnas** · 🟡 pocas · 🔴 gaps ≈ **fiscal + ROW_VERSION + base**. **Mucho mejor** que el catálogo completo (que tenía ~55-60 gaps).

---

## 4. La pregunta que sigue mandando (igual que antes, pero barata de probar acá)

Cuando Tango importa, la celda **vacía** ¿la **ignora** (caso A) o la **sobrescribe** (caso B)?
- **Caso A** → nos alcanza con Código + las columnas que cambiamos; Tango conserva IVA/percepciones/etc. **Ideal para ferretería** (ERPNext dueño del catálogo, Tango sigue con lo fiscal).
- **Caso B** → hay que llenar bien también lo fiscal.

Como ahora son **50 artículos**, esto se **prueba con 1**: exportar un solo artículo de ferretería con las columnas mínimas, subirlo a Tango y ver si respeta o borra el IVA. **Recomiendo esa prueba como primer paso** (antes de construir nada).

---

## 5. Cómo se generaría (sin cambios respecto al diseño general)

- **NO fabricar el .xlsx de cero** (la plantilla tiene 81 hojas + hoja oculta `_metadata` con claves internas que Tango probablemente valida). Enfoque seguro: **partir de la plantilla oficial descargada y pegar solo las 50 filas** de ferretería en la hoja "Artículos".
- **Disparo/entrega:** botón "Exportar ferretería a Tango" en una página de ERPNext que genere y **descargue** el archivo (Constantino lo revisa y lo sube), o dejarlo en el share `\\190.190.190.20\compartida\intercambio\`. Recomiendo la descarga manual para empezar (son 50, se revisa a ojo).

---

## 6. Detección de cambios (acotada a ferretería)

- Filtro base: `item_code LIKE '06-%'`.
- **Primera vez:** exportar los 50.
- **Incremental:** por fecha de última modificación (`modified`) del Item, filtrando dentro de ferretería. Simple, nada que construir salvo el generador.
- Opcional más fino: flag `si_tango_dirty` por hook (solo si hace falta).

---

## 7. Lo que necesito que defina Constantino (acotado)

1. **(Crítico) Caso A/B** — lo resolvemos con **una prueba de 1 artículo** de ferretería. ¿Autorizás esa prueba puntual cuando llegue el momento?
2. **¿Ferretería lleva stock en ERPNext** o queda como catálogo comercial? (hoy `is_stock_item=0`; define columnas O/AQ/AR/AS).
3. **IVA de ferretería:** ¿es todo 21% (código 1 en Tango)? ¿o hay excepciones? (para la columna BB si estamos en caso B).
4. **Código de base / ROW_VERSION:** si Tango los exige en updates, hay que traerlos de Tango al importar (o probar que no hacen falta para actualizar existentes).
5. Confirmás que el filtro es **`item_code` con prefijo `06-`** (lo tomo así salvo aviso).

---

### En una frase
Acotar a **ferretería (`06-`, 50 artículos)** vuelve el export **mucho más simple**: familia única, unidad trivial (UNIDAD), perfil uniforme (A), sin escalas. Quedan como gaps solo **lo fiscal + ROW_VERSION**, y eso se resuelve con **una prueba de 1 artículo** para saber si Tango pisa o respeta las celdas vacías. Sigo sin construir nada hasta esa definición.

— Forge
