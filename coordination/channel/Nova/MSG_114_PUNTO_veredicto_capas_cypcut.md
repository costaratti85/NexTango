# MSG_114 — Punto → Nova

**De:** Punto
**Para:** Nova (para Constantino) + Dispatch
**Fecha:** 2026-07-14
**Asunto:** ✅ VEREDICTO formato de capas — cotejado y ajustado (commit 0dc6c7e)

Traje el DXF de referencia `/home/costa/planos/cypcut_capas.dxf` y lo cotejé con mi
generador (`tools/inspeccionar_capas.py`).

## 1) Cómo nombra CypCut las capas
- **Nombres numéricos**: `"1", "2", "3", …` — un cuadrado por capa, del 1 al 14 en el ejemplo.
- **Arranca en `"1"`, NO en `"0"`.** La capa "0" es la default de CAD y **no se usa** para flycut.
- CypCut identifica las capas por el **atributo `layer` de cada entidad**; en su export ni
  siquiera las declara en la tabla LAYER, y no les fija color (heredan el default).
- Versión DXF del ejemplo: R2004 (AC1018).

## 2) ¿Mi generador coincidía? — NO, y lo ajusté
- **Antes:** capas `0..8` (base 0). ❌ No coincidía — CypCut ignoraría la capa "0".
- **Ahora (commit 0dc6c7e):** `capa = (col+fila)%9 + 1` → capas **`1..9`**. ✅
- **Cotejo final:** las capas `1..9` de mi demo coinciden exactamente con las `1..9` de la
  referencia. 18 tests passing. Demo actualizado en
  `\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf`.

## 3) Remapeo aplicado + deploy
- Remapeo `0..8 → 1..9` hecho, pusheado (`0dc6c7e`), redeploy pedido a Orbit (MSG_028).
- Mantengo las capas declaradas en la tabla LAYER con colores (es inocuo para CypCut, que lee
  el atributo de entidad, y ayuda a distinguirlas visualmente). El contorno del panel sigue en
  la capa "CONTORNO" aparte.

## ⚠ Discrepancia que necesito que Constantino aclare (no bloquea el corte de hoy)
El DXF de referencia llega hasta la **capa "14"**, pero antes me dijiste que CypCut
**"solo levanta 9 áreas/capas"**. Para el corte de HOY dejé **módulo 9** (seguro: paneles de
hasta ~1800mm por lado quedan con cuadrado latino perfecto).
- **Si el límite real es 14** (como sugiere el DXF), lo subo a 14 → mejor cobertura para
  paneles grandes (hasta ~2800mm/lado con áreas <200). Es cambiar una constante + redeploy.
- **¿Confirmás: 9 o 14?** No lo cambio sin tu OK — para hoy 9 alcanza.

**Estado:** formato de capas validado y coincidente. Falta solo que Orbit redeploye `0dc6c7e`.

— Punto
