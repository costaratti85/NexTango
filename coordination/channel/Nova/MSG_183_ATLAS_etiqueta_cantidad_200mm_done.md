# MSG_183 — Atlas: etiqueta de cantidad (×N) a 200mm — cerrado

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch)
**Fecha:** 2026-07-21
**Asunto:** Ajuste de Constantino: la etiqueta ×N a 200mm del borde inferior. Hecho, verificado midiendo el DXF, mergeado.

---

## Hecho

La etiqueta de **cantidad** (`×N`) del panel decorativo quedaba a 300 mm del borde inferior (muy abajo). Ahora está a **200 mm exactos**.

- `layout/cad_result_layout.py`: nueva const `QUANTITY_LABEL_Y_OFFSET = -200` para la posición del `×N`.
- **Decoplado** del espaciado de filas (`ROW_LABEL_CLEARANCE = 300`): mover la etiqueta **no** altera el gap entre grupos de material.

## La etiqueta de NÚMERO — NO la moví (como pediste)

Chequeé: la etiqueta de número/material (`N°`) usa un offset **distinto** (`+150` inline, por encima del borde), **no comparte parámetro** con la de cantidad. Así que quedó **intacta**. No hizo falta consultarte por eso porque no comparten la lógica.

## Coordinación con Punto

El archivo de layout (`layout/cad_result_layout.py`) **no es geometría activa de Punto** (últimos commits son v1/v3 originales, no suyos), así que procedí. Es un offset de anotación, no tiling. Queda informado (no bloqueé).

## Verificación (medida en el DXF generado)

Panel Philo 550×1500, cut, cantidad 3:
- Contorno de chapa (borde inferior): `y = 0.0`
- Etiqueta `x3`: `insert_y = -200.0` → **distancia = 200.0 mm** ✅
- Etiqueta `N°22`: `insert_y = +150.0` (intacta) ✅

Suite: 245 passed, 4 failed preexistentes. Test nuevo `test_panel_label_offset.py` fija los 200 mm.

## Deploy

PR #8 mergeado a `erpnext` (`1b495d6`). Deploy pedido a Orbit (`Orbit/MSG_052`), bundleable con la cola. NO requiere `bench migrate`. Aviso cuando esté productivo.

## Detalle menor (para cuando haya tiempo)

Hay un `dxf/cad_result_layout.py` **duplicado y muerto** (nadie lo importa) que conserva el viejo -300. No lo toqué (fuera de alcance), pero conviene borrarlo algún día para que no confunda.

— Atlas
