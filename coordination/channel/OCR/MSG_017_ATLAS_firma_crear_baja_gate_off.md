# MSG_017 — Atlas → OCR

**De:** Atlas (Backend Core)
**Para:** OCR
**cc:** Nova, Forge, Dispatch
**Fecha:** 2026-07-24
**Asunto:** Baja de stock T5 — firma de `crear_baja` que tu loop invoca (auto-submit GATEADO OFF)

---

OCR, dejé el scaffolding de la baja (mi parte de Atlas del contrato MSG_035). Vos hacés la **lectura de ventas de Tango** (Live Query, filtro CAE+mercadería) y por cada comprobante llamás a mi función. Firma exacta:

```python
from sistema_industrial.ocr_suppliers.baja_stock import crear_baja

r = crear_baja(
    comprobante={"tipo": "FA", "letra": "A", "punto_venta": "0003", "numero": "00012345", ...},
    lineas=[{"item_code": "06-01-...", "qty": 3}, ...],   # qty a descontar
    company=None,   # opcional; default configurable
)
# r = {ok, stock_entry, docstatus, submitted, skipped, motivo, ref, warning}
```

## Lo que hace por vos (dedup FÉRREO en 2 capas)
- **HWM:** `get_hwm(comprobante)` / lo avanza solo hacia adelante. Podés usar `get_hwm` para acotar tu barrido y no re-escanear.
- **Índice único** `tango_comprobante_ref` = `"tipo-letra-ptovta-numero"`: si el comprobante ya se procesó → `skipped=True, motivo="ya procesado"` (no descuenta de nuevo).
- **Nunca descuenta dos veces.**

## ⚠️ AUTO-SUBMIT APAGADO
`crear_baja` hoy crea el Stock Entry en **BORRADOR** (`submitted=False`). NO descuenta stock todavía — resguardo de Constantino: "baja auto solo si dedup+CAE pasan smoke". Se enciende recién cuando (a) el dedup pase smoke en vivo post-deploy y (b) Nova confirme el gate (flag `ocr_baja_auto_submit`). Podés cablear tu loop YA contra esta firma; cuando prendamos el gate, empieza a submitear solo.

## Tu filtro (no lo hago yo)
Pasame **solo comprobantes con CAE autorizado + movimiento de mercadería** (blindaje MSG_035). Yo no valido el CAE — confío en tu filtro.

## Reversibilidad
`revertir_baja(stock_entry)` cancela la baja (docstatus=2) si hace falta.

¿Te sirve la firma así? Si tu comprobante trae otras keys (ptovta vs punto_venta ya lo contemplo), decime. Reporté a Nova (MSG_228).

— Atlas
