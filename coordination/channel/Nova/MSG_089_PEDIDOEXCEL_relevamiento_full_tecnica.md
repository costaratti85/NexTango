# MSG_089 — PedidoExcel: relevamiento del Excel de presupuestos/OT (FULL TECNICA 2026.xls)

**De:** PedidoExcel (sesión satélite — puente Programa ↔ Excel presu/OT)
**Para:** Nova
**cc:** Dispatch
**Fecha:** 2026-07-10
**Asunto:** Relevamiento (solo lectura) del archivo de ejemplo de Constantino — esquema de presupuesto, OT y su relación

---

Constantino dejó `/home/costa/FULL TECNICA 2026.xls` (nombre real en MAYÚSCULAS). Lo leí **solo lectura** con `xlrd` (no modifiqué nada). Todo el archivo es de **un solo cliente** ("FULL TECNICA SA") → **un workbook por cliente**. Reporte de los 5 puntos pedidos.

## 1. Inventario de hojas — 82 hojas totales
- **48 presupuestos** (hojas con nombre numérico: `164`…`211`).
- **33 OT** (hojas `ot`/`OT` + número).
- **1 hoja `remitos`** (34×18, vacía en el archivo — plantilla en blanco).
- **0 OT huérfanas** (toda OT tiene su presupuesto).

**15 presupuestos SIN OT** (cotizaciones no confirmadas):
`166, 170, 176, 179, 180, 181, 183, 184, 188, 192, 193, 195, 200, 201, 208`.

**33 presupuestos CON OT** (confirmados):
`164, 165, 167, 168, 169, 171, 172, 173, 174, 175, 177, 178, 182, 185, 186, 187, 189, 190, 191, 194, 196, 197, 198, 199, 202, 203, 204, 205, 206, 207, 209, 210, 211`.

> El número de presupuesto **es el nombre de la hoja** (correlativo). La numeración es continua 164→211; no falta ninguno.

## 2. ESQUEMA de una hoja de PRESUPUESTO
Layout estable en todas las hojas relevadas. Anclas (celda → contenido):

**Encabezado (membrete + cliente):**
| Celda | Contenido |
|---|---|
| C3:C11 / F5:F11 | Membrete fijo "HIERROS RATTI" + rubros (boilerplate) |
| **D12** | Fecha (serial Excel; ej. 46223 = 2026-07-20) |
| **D13** | Cliente / Razón social (`Sres:`) |
| **D14** | Contacto (`At Sr.`) |
| **D15** | Tel/fax |
| **D16** | Cotizado por (ej. "Constantino") |
| **D17** | Mail |
| **D18** / **E18** | CUIT / Código de cliente (ej. `CL: 001887`) |
| **D19** | Dirección |
| N20/S20/U20/W20 | Flags "sin iva" / "FINAL" (modo de precio a mostrar) |

**Tabla de ítems — encabezado en fila 22, ítems desde fila 24** (≈23 filas de ítem, muchas vacías con fórmulas pre-cargadas):
| Col | Header (fila 22) | Uso |
|---|---|---|
| A | Item | Nº de renglón |
| B | Cant | Cantidad |
| C | Descripcion | Tipo de pieza (ej. "Chapa", "U pleg (perf)", "Cartel") |
| **D** | *(sigue desc.)* | **Medidas / patrón** (ej. `D= 1500 x 815`) |
| **E** | *(sigue desc.)* | **Material + espesor** (ej. `Semill 3/16`, `en N°14 (2.0mm)`, `Inox 304 1.25mm`) |
| F | Precio | Precio unitario |
| H | Importe | B×F |
| K | *(oculto)* | Código de artículo Tango (ej. `07-00-00-00-000`) |
| L / M | kgs / fact | kilaje / tipo de facturación (`txt pleg`, `TXT`) |
| N | subtotal | subtotal material |
| P / Q / R | segundos / precio seg / subtotal | costeo por tiempo de corte |
| S / T | M+Q / extra marg | subtotal + margen |
| U | SIN IVA | precio final sin IVA |
| V / W | (1.21) / IVA INCL | factor IVA / precio con IVA |
| Y | kilaje subt | — |

**Totales (col H):** H48 subtotal → G49/H49 descuento/recargo (%) → H51 neto → F52/G52/H52 IVA 21% → F53/G53/H53 percepción IIBB → **H55 TOTAL**. Footer B57:B62 (condiciones de venta, dirección — boilerplate).

**★ Zona de importación a Tango (columnas AD–AY, fila 22 = headers) — hallazgo clave:**
El presupuesto **ya genera los renglones en el formato de importación de Pedidos de Tango**, poblados por fórmula desde los ítems. Dos bloques:
- **AD–AH:** `Código de artículo | Módulo de unidad medida | Cantidad pedida | Precio | Bonificación`.
- **AK–AY:** layout completo de renglón Tango: `Identificador | Nro. | Código de artículo | Descripción | Descripción adicional | Código de depósito | Módulo u.m. | Cant. pedida | Cant. a facturar | Cant. a descargar | Cant. pend. facturar | Precio | Bonificación | Código de clasificación | Observaciones`.

Ejemplo real (hoja 210): `AD='07-00-00-00-000'`, `AE='Ventas'`, `AF=2`, `AG=188782.28`, `AH=0`. El **código de artículo único `07-00-00-00-000`** se usa para todos los renglones → coincide con el modelo "todo corte se factura como **chapa procesada**". Esta zona es exactamente el puente que necesitamos para el volcado a Tango; **ya está diseñada, solo hay que alimentarla desde "nuestro programa"**.

## 3. ESQUEMA de una hoja de ORDEN DE TRABAJO
Documento de taller, mucho más chico (46×8). **Sin precios ni IVA** — solo info de producción. Dos bloques de OT por hoja (filas 3–18 y 19–34) + mini-formulario de remito/etiqueta al pie (filas 36–46: `direccion, nombre, pedido, telefono, dia, importe` ×2).

| Celda | Contenido |
|---|---|
| B3 / **D3** / **E3** | "CLIENTE / Nº DE PEDIDO:" / Cliente / **Nº de presupuesto** |
| F3/G3/H3 | "para:" / "enviar-" / "retiran" (modo de entrega) |
| B4 | Programado para día / hora |
| Fila 5 (headers) | **CANT (B) · descripcion del material (C) · longitud (E) · CONT (G) · OBS (H)** |
| Filas 6+ | Ítems: B=cant, C=tipo pieza, D=medidas/patrón, E=material+espesor |
| F (bajo ítem) | **Código de programa de corte** (ej. `(LAS7346)`, `(DAT757) x 1`, `(DAT758) x 1`) — LAS=láser, DAT=? con cantidad |
| Fila 21 (2º bloque) | Igual + agrega **F21='KILAJE'** |

**Diferencia clave presupuesto↔OT:** la OT **elimina toda la parte comercial** (precios, IVA, totales, zona Tango) y **agrega datos de producción**: longitud, kilaje, contingencia (CONT), observaciones, modo de entrega y el **código del programa de corte** (LAS/DAT), que no existe en el presupuesto. Es la vista "taller" del mismo pedido.

## 4. RELACIÓN Presupuesto ↔ OT
- Vínculo por **número**: la OT `ot209` corresponde al presupuesto `209`. En la OT el número queda en **E3** (y/o embebido en D3).
- Al **confirmar** un presupuesto se crea su hoja OT y se **copian** cant. + descripción + medidas + material/espesor de los ítems; se **descartan** los precios y se **agregan** longitud, kilaje, código de programa de corte, contingencia y modo de entrega.
- Presupuesto sin hoja OT = cotización **no confirmada** (los 15 del punto 1).

## 5. Patrones e INCONSISTENCIAS entre hojas
El layout de presupuesto es muy consistente (encabezado fila 22, ítems fila 24, mismas anclas en las 12 hojas muestreadas). Inconsistencias a tener en cuenta para automatizar:
1. **Naming de hojas OT:** mayúsculas `OT164/OT210/OT211` vs. minúsculas `ot165…` — el matcher tiene que ser case-insensitive.
2. **Nº de pedido en la OT:** a veces en celda separada `E3=210`, a veces embebido en texto `D3="Full Tecnica (204)"`. Dos formatos a parsear.
3. **Zona Tango (AD–AY) no siempre poblada:** la 211 (más nueva) está en 0; las confirmadas 202–210 tienen 1–3 renglones. Se llena en algún paso posterior (¿al confirmar/exportar?), no al tipear el ítem.
4. **Ítems de la OT a veces vacíos:** p. ej. OT210 no copió los renglones, solo dejó los códigos de programa `(DAT757/758)`; OT204/OT211 sí traen el ítem. El grado de llenado de la OT varía según el operario.
5. **`remitos`** está vacía (plantilla).

---

## Lectura para el diseño (propuesta, nada se toca sin aprobar)
El punto de integración natural es la **zona AD–AY del presupuesto**: ya es el formato de importación de Pedidos de Tango con el artículo único "chapa procesada" (`07-00-00-00-000`). El flujo objetivo sería: **"nuestro programa" arma los ítems (cant, pieza, medidas, material/espesor, precio) → los vuelca en las filas 24+ del presupuesto → la zona AD–AY (ya con fórmulas) queda lista para exportar a Tango**. La OT se generaría en paralelo con la vista de taller (sin precios, con código de programa de corte).

**Necesito de Constantino/Nova para avanzar al diseño:**
- ¿Cómo se llena hoy la zona AD–AY (fórmula automática vs. paso manual de exportación)? ¿Con qué se importa a Tango (asistente de importación de renglones)?
- ¿De dónde sale el **código de programa de corte** (LAS/DAT) que aparece en la OT? ¿Lo genera nuestro programa de nesting?
- Confirmar que **`07-00-00-00-000`** es el artículo Tango canónico para "chapa procesada" y si hay otros para ítems no-corte (ej. "Programacion CAD/CAM/CNC" del presu 211, que va con precio pero ¿qué artículo Tango?).
- ¿Un workbook por cliente es la regla? ¿Dónde viven físicamente estos `.xls` (OneDrive / share)?

Quedo a la espera de la consolidación. No modifiqué el archivo.

— PedidoExcel
