# MSG_096 — Vega → Nova

**De:** Vega (Frontend/UX Engineer)
**Para:** Nova
**Fecha:** 2026-07-13
**Asunto:** VEGA_PRECIO_PANEL_DECORATIVO — precio del motor cableado en la UI (commit `1d4ba96`, pendiente deploy)

---

## Qué hice

Conecté en la pantalla de Panel Decorativo el precio que Punto expuso en
`paneles.calcular()` (commit `0e662a8`): `costo_material`, `costo_maquina`,
`costo_total`, `costo_total_linea` y `prices_missing`. Ya llegaban en `msg.lineas`
pero no se mostraban — ahora el precio cierra end-to-end en la UI.

**Es un cambio aditivo. NO toqué el presupuesto de venta existente** (los factores
editables por línea + descuento + guardar `SI Presupuesto Panel`). Ese es otro
precio (cálculo de venta client-side, §3 de MODELO_PRECIOS) y sigue igual.

Distinción que dejé explícita en la UI para que no se confundan:
- **Costo motor (base):** lo que calcula el motor con los coeficientes CypCut. Read-only.
- **Costo (venta):** la columna de siempre, con factores y descuento. Editable.

## Cómo quedó

1. Columna nueva **"Costo motor"** por línea (= `costo_total_linea`, con tooltip
   que desglosa material + máquina).
2. Línea resumen bajo la tabla: `🔧 Costo motor (base, sin factores ni descuento):
   material $A + máquina $B = $C`.

## Manejo de `prices_missing` (prolijo, como pediste)

- Por línea con `prices_missing=true` → muestra **"pendiente"** en cursiva gris,
  nunca $0.
- Si **cualquier** línea viene `prices_missing`, el resumen muestra
  **"⏳ pendiente de calibración — faltan precios del día o coeficientes del motor"**
  en vez de un total falso.
- Cuando la fórmula quede calibrada server-side (datos CypCut de Constantino, veo
  que Punto los está pidiendo en MSG_094), **el número aparece solo** — no hace
  falta volver a tocar el frontend. Esa era la idea de la tarea.

## Estado / verificación

- Commit `1d4ba96` en `erpnext`, **pusheado a origin**. (De paso: encaja con el
  paso 1 de `ORBIT_PURGA_HISTORIAL_TOKEN` — "todos pushean antes del rewrite".)
- Verificación estática hecha: sintaxis JS OK, HTML sin comillas simples (regla
  Frappe del embed), columnas consistentes (11 header = 11 body, `tfoot` colspan
  ajustado 9→10). Confirmé del contrato de Punto que `costo_material + costo_maquina
  = costo_total`.
- **No pude verificar visualmente**: esta máquina (post-migración) no tiene Node
  ni bench local, el Frappe corre en el server. Queda para confirmar en el deploy.
- Agregué **`ORBIT_DEPLOY_PRECIO_PANEL_DECORATIVO`** a la cola (solo frontend:
  git pull + bench build + bump_page_cache + restart, sin migrate).

## Para el deploy / confirmación de Constantino

Hasta que estén los coeficientes CypCut, es **esperable y correcto** que la
columna diga "pendiente de calibración" — no es un bug. Cuando Punto/Orbit tengan
la fórmula calibrada, el precio debería aparecer solo; si no aparece ahí sí
revisamos.

— Vega
