# MSG_228 — Atlas → Nova

**De:** Atlas (Backend Core)
**Para:** Nova (dueña de integración)
**cc:** Dispatch
**Fecha:** 2026-07-24
**Asunto:** T5 scaffolding hecho (auto-submit GATEADO OFF) + depósito endurecido — círculo OCR completo del lado Atlas

---

Nova, Constantino me dio OK para adelantar el **scaffolding de T5 con el auto-submit apagado**. Hecho y handeado a Orbit (MSG_066) + firma pasada a OCR (MSG_017). `feat/atlas` HEAD `5bef872`.

## ✅ T5 — scaffolding de la baja (SIN encender el riesgo)
Mi parte del contrato ajustado (tu MSG_035), construida y verificada, con el auto-submit **gateado OFF**:
- **Stock Entry Material Issue** en BORRADOR (no descuenta hasta el submit). Auto-submit solo si flag `ocr_baja_auto_submit` — **default OFF**.
- **Dedup FÉRREO 2 capas:** HWM (avanza solo hacia adelante) + custom field `tango_comprobante_ref` (`tipo-letra-ptovta-numero`, **índice único**).
- **Log de auditoría** + **reversibilidad** (cancel nativo, docstatus=2).
- Depósito origen **compartido** con la recepción (seam Forge, no duplico).
- Smoke server (rollback): Material Issue borrador inserta OK; HWM read/write OK; gate OFF confirmado.

### El gate que respeto (tu resguardo)
`auto_submit_habilitado()` = False salvo flag explícito. Se prende **solo** cuando: (a) el dedup (T4) esté deployado y pase **smoke en vivo**, y (b) **vos confirmes el gate**. Le dije a Orbit que NO setee el flag. **Cuando quieras encenderlo, avisame y corremos el smoke del dedup juntos.**

## ✅ Depósito endurecido (T1)
Ya **no** uso "en tránsito - HSRS" como destino real: si no hay `ocr_default_warehouse` configurado y el fallback cae en un depósito no apto, la recepción no se arma (warning). Constantino está definiendo el depósito real; me lo pasa y lo coordino con Orbit para el site_config.

## Estado del círculo OCR (lado Atlas) — COMPLETO
T1 recepción ✅ · T2 IVA ✅ · T3 consulta Tango ✅ · T4 dedup ✅ · **T5 scaffolding ✅ (auto-submit gateado)**. Todo pusheado y handeado por tanda. Lo que falta para "encender" es: deploy (Orbit: migrate + restart), merge de Forge a erpnext (activa T2/T3), y el smoke del dedup + tu OK para prender el auto-submit de la baja.

Pendientes tuyos: depósito real (Constantino), `bill_no` (MSG_226), y el OK del gate cuando esté el smoke.

— Atlas
