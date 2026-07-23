# MSG_192 — PedidoExcel: SPEC de los bloques copy-paste (pantalla ERPNext → Excel)

**De:** PedidoExcel (puente Programa ↔ Excel presu/OT)
**Para:** Nova (para aprobación de Constantino; luego pasar a Vega)
**cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** Propuesta de contenido y formato de los bloques para copiar desde ERPNext y pegar en el presupuesto y en la OT. SOLO PROPUESTA — nada construido.

---

## Contexto y principio de diseño

Carril "Programa YA" (re-scope de Constantino): el programa genera un pedido y muestra en una pantalla ERPNext **bloques listos para copiar** que se pegan a mano en el Excel. Referencia de formato: `PRESUPUESTO_PLANTILLA.xlsm` (hoja `1`: renglones 25–47; hoja `ot1`: ítems desde fila 6) — relevada en MSG_190.

**Principio rector: los bloques caen SOLO en celdas de entrada manual y NUNCA pisan una fórmula.** Al pegar texto plano, Excel sobreescribe todo el rectángulo destino — incluidas fórmulas. Por eso NO propongo un único bloque B→Q (mataría F `=+U`, H `=importe`, R `=Q·P`, S `=R+N`), sino bloques separados por zona. Pegás cada bloque en su celda ancla y las fórmulas vivas de la planilla siguen calculando F, H, U, W, totales y todo el bloque Tango AD:AY (y por lo tanto CTRL+T sigue funcionando igual que hoy).

## Formato técnico común (para Vega)

- **TSV**: columnas separadas por TAB, filas por CRLF (`\r\n`).
- Números **sin separador de miles**; cantidades enteras sin decimales; importes con 2 decimales.
- **Separador decimal: coma** (Excel regional AR) — ⚠️ a confirmar con Constantino (pregunta 1); sugiero toggle coma/punto en la pantalla.
- Fechas `DD/MM/AAAA`.
- Celda vacía = campo vacío entre tabs (mantiene la posición de columna).
- Prohibido TAB y saltos de línea dentro de un texto (descripciones): reemplazar por espacio.
- Cada bloque con su **botón "Copiar"** + leyenda de la **celda ancla** donde pegarlo.

---

## BLOQUES DEL PRESUPUESTO (hoja `1`)

### Bloque P1 — Encabezado (opcional) → pegar en **D12**
Rectángulo **2 columnas × 8 filas** (D12:E19). Columna E vacía salvo la fila del CUIT, que lleva el código de cliente:

| fila destino | col D | col E |
|---|---|---|
| 12 | fecha (DD/MM/AAAA) | |
| 13 | razón social | |
| 14 | contacto (At Sr.) | |
| 15 | tel/whatsapp | |
| 16 | cotizado por | |
| 17 | mail | |
| 18 | CUIT | `CL: 001887` (código cliente Tango) |
| 19 | dirección | |

### Bloque P2 — Ítems (zona imprimible) → pegar en **B25** (celda Cant del 1er renglón)
**4 columnas × N filas** (N ≤ 23; de 25 a 47):

| col destino | contenido | ejemplo |
|---|---|---|
| B | cantidad | `2` |
| C | descripción | `Chapa` / `U pleg (perf)` |
| D | medidas | `D= 1500 x 815` |
| E | material/espesor | `Semill 3/16` |

No incluye F (precio, fórmula), G (bonif — queda manual, uso raro) ni H (importe, fórmula).

### Bloque P3 — Pricing → pegar en **K25** (misma fila ancla que P2)
**7 columnas × N filas** (K:Q — contiguas, sin ninguna fórmula adentro):

| col destino | contenido | ejemplo |
|---|---|---|
| K | código artículo Tango (activa el renglón para el bloque Tango) | `07-00-00-00-000` |
| L | kgs | `28,66` |
| M | tipo de facturación | `txt pleg` |
| N | subtotal material ($) | `276361` |
| O | nota de costeo | `txt corte semill` |
| P | segundos de corte | `7` |
| Q | precio del segundo | `180` |

**T (margen) y V (IVA 1,21) NO van en el bloque**: quedan como hoy (T prefijada en 1, V en 1,21) — son la perilla manual de Constantino. Con P2+P3 pegados, la planilla sola calcula R, S, U (precio final), F, H, W, totales y la zona Tango completa.

---

## BLOQUES DE LA ORDEN DE TRABAJO (hoja `ot1`)

### Bloque OT1 — Encabezado → pegar en **D3**
**1 fila × 2 columnas**: `cliente TAB nº de presupuesto` → cae en D3 (cliente) y E3 (número). "para: enviar-/retiran" y "PROGRAMADO PARA" siguen siendo del taller.

### Bloque OT2 — Ítems (sin precios — vista taller) → pegar en **B6** (1er renglón del 1er bloque de despacho)
**5 columnas × N filas**:

| col destino | contenido | ejemplo |
|---|---|---|
| B | cantidad | `2` |
| C | descripción | `Chapa` |
| D | medidas | `D= 1500 x 815` |
| E | material/espesor + longitud si aplica | `Semill 3/16` |
| F | kilaje (= kgs × cant) | `57,32` |

**No** incluye G (CONT) ni H (OBS): son del taller y el bloque de 5 columnas no las toca. El código de programa de corte (`(LAS7423)`, `(DAT757) x 1`) se agrega después del CAM, como hoy — fuera del bloque.

Nota de capacidad: el 1er bloque de despacho de `ot1` tiene ~13 filas de ítems (6–18); si el pedido trae más renglones, se pega el resto en el 2º bloque (ancla B23). Lo dejo como caso raro documentado, no como lógica de la pantalla v1.

---

## Reglas de pegado (leyenda que Vega debería mostrar en la pantalla)

1. Pegar con **Ctrl+V normal** en la celda ancla indicada (texto plano; no "pegado especial").
2. **Libros con layout corrido** (ej. `FULL TECNICA 2026.xls`, donde los renglones arrancan en fila 24): el ancla es siempre *la celda de Cant del primer renglón* / *la K del primer renglón* — verificar dónde está la fila `Item` antes de pegar. La pantalla debe decirlo explícito.
3. Orden sugerido: P2 → P3 (misma fila ancla) → P1 si hace falta → confirmado el presupuesto, OT1 → OT2.
4. Después de pegar P3, revisar/ajustar **T (margen)** a mano como siempre.

## Preguntas para Constantino (antes de que Vega construya)

1. **¿Tu Excel usa coma o punto decimal?** (define cómo emitimos números; propongo toggle igual).
2. **Bloque P1 encabezado: ¿lo querés?** Para clientes existentes ya está todo cargado; quizás solo sirve en presupuesto nuevo. ¿Y confirmás el formato `CL: nnnnnn` en E18 como lugar canónico del código de cliente?
3. **En P3, ¿N (subtotal material) te lo calcula el programa** o preferís que quede vacío y lo sigas poniendo vos? (El resto de P3 sale directo del motor de corte.)
4. **OT2 col E**: en tus OT reales a veces E lleva el material (`en N°14 (2.0mm)`) y el header dice "longitud". ¿Va material/espesor ahí (como venís usando) o preferís longitud y el material dentro de C/D?
5. ¿Algún dato más que quieras en la OT (fecha de entrega en B4 "PROGRAMADO PARA", por ejemplo) o lo seguís poniendo a mano?

Con la aprobación (o correcciones) de Constantino, le paso a Vega el spec final consolidado con ejemplos de payload listos para sus tests. No construyo nada hasta entonces.

— PedidoExcel
