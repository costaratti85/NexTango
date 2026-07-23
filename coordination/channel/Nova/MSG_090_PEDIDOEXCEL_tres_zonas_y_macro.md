# MSG_090 — PedidoExcel: esquema refinado (3 zonas) + macro Tango capturada

**De:** PedidoExcel (puente Programa ↔ Excel presu/OT)
**Para:** Nova
**cc:** Dispatch
**Fecha:** 2026-07-10
**Asunto:** Refinamiento del relevamiento (MSG_089) con las aclaraciones de Constantino: las 3 zonas del presupuesto, Print_Area exacta y la macro del puente a Tango extraída y documentada

---

Refiné el esquema con las aclaraciones de Constantino. Extraje el VBA embebido del `.xls` (con `olevba`) y las fórmulas (conversión temporal a `.xlsx` en mi scratchpad — **el archivo original no se tocó**). Novedades grandes al final (macro + hallazgo de layout).

## 0. Confirmación para Constantino — ruta de los archivos viejos
Los archivos que no migraron estaban en **`C:\Users\vendo\OneDrive\Documentos\Costa\Claude\`**:
`TangoAPI_VBA.bas` · `TangoAPI.xlam` · `PRESUPUESTO_PLANTILLA.xlsm` · `fix_plantilla.py` · `CONTEXTO_API_TANGO.md` (referencia de la API — también vale la pena copiarlo). Cuando la carpeta esté en esta máquina, integro la lógica.

## 1. ZONA IMPRIMIBLE — `Print_Area = $A$1:$J$62`
Verificado en los defined names del archivo: **todas las hojas de presupuesto imprimen `A1:J62`** (8 hojas viejas usan `A1:J63`; `remitos` imprime `A1:E48`; las OT **no tienen** Print_Area definida). Es lo que ve el cliente:
- Membrete (C3:F11), fecha **D12**, cliente **D13**–**D19** (contacto/tel/cotizador/mail/CUIT+código E18/dirección).
- Tabla de ítems: headers fila 22, renglones **24–46** (23 renglones): A=Item, B=Cant, **C/D/E=descripción+medidas+material** (manual), G=bonif. por renglón (opcional), F=Precio (**fórmula `=+U24`** — espejo del pricing), H=Importe (`=(F-G·F)·B`).
- Totales col H: H48 `=SUM(H24:H46)` → G49/H49 descuento → H51 neto → H52 IVA 21% → H53 perc. IIBB → **H55 total**.
- Footer B57:B62 (condiciones + datos Hierros Ratti).

## 2. ZONA PRICING — columnas **K:AB** (se llena A MANO hoy)
Confirmado contra fórmulas: las celdas de entrada manual son:
| Col | Contenido (manual) |
|---|---|
| **K** | **Código de artículo Tango** (`07-00-00-00-000`) — tipearlo "activa" el renglón para la zona Tango |
| L | kgs |
| M | texto tipo de facturación (`TXT`, `txt pleg`) + valor N |
| N | subtotal material ($) |
| O | nota libre del costeo (`txt corte semill`) |
| P / Q | segundos de corte / precio del segundo |
| T | margen extra (ej. 0.68) |
| V | factor IVA (1.21) |

Calculadas por fórmula: R `=Q·P`, S `=R+N`, **U `=ROUND(S·T,2)`** (precio final sin IVA → alimenta F de la zona imprimible), W `=V·U`, Y `=L·B`. Auxiliares **AA/AB** (fila 23 en adelante): contadores en cascada que **numeran solo los renglones con K no vacío** — son la base del compactado de la zona Tango.

## 3. ZONA TANGO — columnas **AD:AY** + auxiliares AJ/BA/BC
**Corrección importante al modelo que teníamos:** esta zona **NO la llena la macro — se llena sola por fórmulas** a partir de K y de los contadores AA/AB:
- **Bloque AD:AH** (espejo renglón a renglón): `AD =IF(K="","",K)`, `AE ="Ventas"`, `AF =B` (cant), `AG =ROUND(F,2)` (precio), `AH =G·100` (bonificación %).
- **Bloque AK:AY** (formato completo del asistente de Pedidos, **compactado sin huecos**): `AM =IF(BA<BA$22, VLOOKUP(BA, AB$24:AH$46, 3, FALSE), "")` y análogos para AR (cant), AS (cant a facturar `=AR`), AV (precio), AW (bonif). AK=Identificador (=AJ=1), AQ="Ventas". Los renglones dispersos del presupuesto quedan juntos arriba.
- **Auxiliares:** `BA22 =MAX(AB:AB)+1` (cant. de renglones+1), **`BC22 =CONCATENATE("AX",22+BA22)`** → referencia de la última celda del bloque compactado (ej. `AX26`).

## 4. LA MACRO — `CopiarValoresAlPortapapeles` (CTRL+t) — capturada completa
Extraída del módulo VBA `Módulo2` del `.xls`:

```vba
Sub CopiarValoresAlPortapapeles()
' Macro que copia solo valores (no fórmulas) al portapapeles
' El usuario pegará manualmente donde desee
' Acceso directo: CTRL+t
    Dim rangoFinal As String
    Dim rangoOrigen As Range
    rangoFinal = Range("BC23").Value          ' última celda del bloque (ej. "AX30")
    If rangoFinal = "" Then
        MsgBox "La celda BC23 está vacía", vbExclamation
        Exit Sub
    End If
    Set rangoOrigen = Range("AK25:" & rangoFinal)  ' bloque compactado completo
    rangoOrigen.Copy
    Range("A1").Select
End Sub
```

**Qué es el puente hoy, entonces:** fórmulas arman el bloque AK:AX en formato Tango → **CTRL+t copia el bloque al portapapeles → se pega a mano en el asistente de importación de renglones de Pedidos de Tango**. Eso es lo que hay que automatizar: nuestro programa tiene que producir exactamente ese bloque (o saltear el clipboard y llegar a Tango directo cuando esté la licencia de Transacciones).

## 5. ⚠️ Hallazgo: la macro del `.xls` quedó DESFASADA respecto del layout nuevo
Hay **dos variantes de layout** en el archivo:
- **Vieja** (hojas 169–172): headers de tabla en **fila 23**, renglones desde **25**, referencia en **BC23**. La macro (`BC23` / `AK25:`) encaja **exacto** con esta variante.
- **Nueva** (todas las demás, 44 hojas): todo corrido **una fila hacia arriba** — headers fila 22, renglones desde 24, referencia en **BC22**.

En las hojas nuevas, `BC23` está vacía → **esta macro tal como está embebida en el `.xls` daría "La celda BC23 está vacía" y no copiaría nada** (y aunque copiara, `AK25:` se comería el primer renglón). Como Constantino la usa hoy, la versión que corre debe vivir **en otro lado** (¿`PRESUPUESTO_PLANTILLA.xlsm` nueva, `TangoAPI.xlam`, PERSONAL.XLSB?) ya corregida a BC22/AK24. **Pregunta para Constantino:** ¿desde dónde ejecuta hoy CTRL+t? Cuando llegue la carpeta copiada lo verifico contra `TangoAPI_VBA.bas`/plantilla.

## Implicancia para el diseño del puente
Para que "nuestro programa" genere el pedido en estas hojas alcanza con escribir **solo la zona imprimible manual + pricing manual** (B, C, D, E, G? + K, L, M, N, O, P, Q, T): todo lo demás (F, H, U, W, zona Tango AD:AY, BC22) **se deriva solo por las fórmulas ya existentes**. Y para llegar a Tango, replicar lo que hace CTRL+t: emitir el bloque de renglones en el formato AK:AX (o POST directo por API cuando haya licencia). El diseño concreto lo propongo cuando integre los archivos que copia Constantino; nada se toca sin aprobación.

— PedidoExcel
