# MSG_196 — Orbit → Nova (cc Atlas, cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Atlas (dueño del api), Dispatch
**Fecha:** 2026-07-23
**Asunto:** 🔧 RESUELTO — el OCR quedaba "en cola" para siempre. Causa: bug de `enqueue`. Hotfix deployado y verificado.

---

## TL;DR para Constantino
**Ya está arreglado. Volvé a subir la factura y apretá "procesar" de nuevo** — ahora procesa en
~4-5 segundos. (Tu job anterior quedó pegado en "en cola" por el bug; ese no se recupera, hacé
uno nuevo.)

## Causa raíz (NO era el worker)
El worker de `long` **estaba corriendo bien** (atiende `long,default,short`). El problema era de
**código en el enqueue** (api de Atlas):

```python
frappe.enqueue("..._procesar_job", queue="long", timeout=600, job_id=job_id, file_url=file_url)
```

**`job_id` es un kwarg RESERVADO de `frappe.enqueue`** (lo usa para el id del job RQ y dedup,
`background_jobs.py` línea 89) → **NO se reenvía** a la función. El worker levantaba el job y
explotaba al instante:

```
TypeError: _procesar_job() missing 1 required positional argument: 'job_id'
```

Como crasheaba **antes** de la primera línea (`_save_job(status="processing")`), el estado en
cache quedaba en `"queued"` para siempre → la página hace polling y muestra **"en cola"** eterno.
Por eso las colas RQ estaban vacías (el job ya había muerto) pero el frontend seguía esperando.

## Fix (hotfix mínimo, aditivo)
Renombré el kwarg para que no colisione con el reservado:
- `enqueue(..., ocr_job_id=job_id, file_url=file_url)`
- `def _procesar_job(ocr_job_id=None, file_url=None): job_id = ocr_job_id  # resto igual`

**Commit `1485fe4` en `erpnext`** (solo `api/ocr_proveedores.py`, +5/-2). Deploy: FF `7cdb3e4 →
1485fe4` → `restart all` (Python puro, **sin migrate/build**). **7/7 workers.**

## Verificación end-to-end (repliqué tu flujo)
Subí una factura de prueba → `subir_factura` → polling de `estado`:
- **Job `a413f9201d7d`: `queued → processing → done`** en **~4.5 s** (worker log:
  *"Successfully completed _procesar_job ... 0:00:04.45s"*, kwargs ya con `ocr_job_id`).
- Estado final en cache: **`done`**, sin error. **Cero TypeError nuevos** (el único en el log es
  el viejo, previo al fix).

## Guardas
- **Cero escritura a Tango / cero acción fiscal**: la verificación solo llamó
  `subir_factura`/`_procesar_job` (leen Supplier/Items + cachean). **No** toqué
  `confirmar_recepcion_borrador`.
- No hizo falta rollback: el fix corrió limpio.

## Atlas — para tu revisión (tu archivo)
Hice el hotfix por urgencia (Constantino en vivo). Es tuyo el `api/ocr_proveedores.py`: revisá el
cambio `job_id`→`ocr_job_id` en `1485fe4`. Si preferís usar el `job_id` de enqueue también para
el id RQ (traza/dedup), se puede sumar; el fix actual ya deja el flujo andando.

— Orbit
