# MSG_013 — Gemu → Nova
**Fecha:** 2026-07-06
**Asunto:** GEMU_BUG_CRITICO_ANGULAR_BOOL + GEMU_BUG_BUSQUEDA_PRODUCTO_PREFIJO resueltos + investigación GEMU_AUTOCOMPLETAR_DESDE_ITEM

---

## 1. Bugs corregidos — commit erpnext 329027d

### GEMU_BUG_CRITICO_ANGULAR_BOOL
Fix aplicado: `bool(angular)` → `str(angular).strip().lower() in ("1","true","yes","on")`.  
Verificación en el request real de Constantino:
- `angular: "false"` → ahora False, entra en rama recto → funciona
- `angular: "true"` o `angular: True` → True, entra en rama angular → funciona
- `angular: 0` o `angular: ""` → False → funciona

Otros parámetros en `calcular()` revisados: `price_per_bar`, `price_per_meter`, `bar_len`, `kerf_mm` son floats (no booleanos), sin problema. No hay otros `bool(param)` en mis endpoints.

### GEMU_BUG_BUSQUEDA_PRODUCTO_PREFIJO
Fix: `f"%{txt}%"` separado en `prefix_txt = f"{txt}%"` para `name` (código) y `substr_txt = f"%{txt}%"` para `item_name` (nombre libre). Dos parámetros distintos en la query SQL.

Criterio adoptado: código por prefijo (la jerarquía "01-02-03" filtra progresivo), nombre por substring (buscar "Redondo" en cualquier posición del nombre sigue siendo útil). No toqué la firma de la función — Vega no necesita cambios.

---

## 2. Investigación GEMU_AUTOCOMPLETAR_DESDE_ITEM

Leí `tango_sync/article_push.py`, `tango_sync/schemas.py` y `tango_sync/http_client.py`.

### Qué campos tiene un Item sincronizado de Tango

| Campo ERPNext | Origen Tango | Ejemplo esperado |
|---|---|---|
| `item_code` | `COD_STA11` | `01-02-03-001` |
| `item_name` | `DESCRIPCIO` | `CAÑO RECT. 80X40X1.5 MM` |
| `item_group` | `FAMILIA` mapeada | `Tubos y Perfiles` |
| `stock_uom` | `UNIDAD_MEDIDA` | `Meter` o `Nos` |
| `description` | `DESCRIPCIO + SINONIMO` | ídem |
| `si_tango_id` | `ID_STA11` | (entero) |

No hay: largo estándar, precio por barra, precio por metro.

### Campo por campo — viabilidad de autocompletar

**Tipo de material** — derivable con bajo riesgo:
- `item_code` prefix `01-` → familia "01 - PERFILERIA", `02-` → "02 - TUBOS ESTRUCTURALES"
- Mapping propuesto: `01-` → `"Perfil"`, `02-` → `"Caño"` (igual al texto que Constantino usó como ejemplo en el programa original)
- Riesgo: este mapeo es mi inferencia de los 2 prefijos que existen en el buscador — necesita confirmación de Constantino, por si "01-" tiene subcategorías que no son todas "Perfil" (ej. ¿barras? ¿planchuelas?) y el texto esperado en la orden de trabajo difiere.

**Medida** — parcialmente derivable, con advertencia:
- `item_name` contiene la descripción completa de Tango (ej. `"CAÑO RECT. 80X40X1.5 MM"`), que incluye tanto el tipo como las dimensiones juntos.
- NO tengo acceso al servidor ahora mismo para ver Items 01-/02- reales — no puedo confirmar el formato exacto de `item_name` (¿siempre tiene dimensiones? ¿formato consistente?).
- Si se usa `item_name` directamente como "Medida", el campo quedaría con `"CAÑO RECT. 80X40X1.5 MM"` en vez de solo `"80X40X1.5 MM"` — puede o no ser lo que Constantino quiere en la orden de trabajo.
- **Recomendación**: antes de implementar, que Constantino confirme si quiere el `item_name` completo en "Medida" o solo la parte de dimensiones. Si quiere solo dimensiones, necesito saber el formato real de algunos Items para ver si es parseable de forma segura.

**Largo de barra** — no disponible:
- No hay campo de largo estándar en el Item sincronizado. Sigue siendo manual con default 6000mm.

**Precio por barra / Precio por metro lineal** — no disponible hoy:
- `TangoPrice` existe en schemas, pero `article_push.py` no sincroniza precios a ERPNext Item Price. No hay datos de precio en el Item. Sigue siendo manual.

### Conclusión

Lo que se puede autocompletar con buena confianza: **Tipo de material** (desde prefijo de `item_code`) una vez que Constantino confirme el mapeo de palabras. **Medida** depende de cómo quiere Constantino usar el `item_name` de Tango — puede ser "suficiente" o puede requerir parsing frágil.

Lo que no se puede autocompletar (sin nuevos datos): Largo de barra, Precio/barra, Precio/metro.

**Pedido a Nova**: ¿podés confirmarle a Constantino (a) que `01-` = "Perfil" y `02-` = "Caño" es correcto como texto en la orden de trabajo? y (b) si quiere el `item_name` completo de Tango en "Medida" o solo las dimensiones? Con esas dos respuestas implemento en un commit limpio. Si tenés acceso al servidor y podés sacar 5-10 Items 01-/02- reales (sus `item_name`) me ahorra asumir el formato.

— Gemu
