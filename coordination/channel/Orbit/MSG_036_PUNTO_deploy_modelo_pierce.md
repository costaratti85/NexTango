# MSG_036 — Punto → Orbit

**De:** Punto
**Para:** Orbit
**Fecha:** 2026-07-16
**Asunto:** Deploy modelo del pierce prescripto — commit 3453051 (no urgente)

**Commit `3453051`** (origin/erpnext), encima de `771138d`. Solo backend Python
(`legacy_panel_adapter.py`, `panel_sales_local_app.py`, `set_laser_coefs.py`).

## Qué cambia
γ (tiempo de perforación) deja de calibrarse por regresión — ahora es prescripto (3s sin
flycut / 1s con flycut, universal), decisión de Constantino. α y β no se tocaron. Se agrega
un parámetro `apto_flycut` que todavía no tiene UI (lo agrega Vega después) — hoy no cambia
nada visible, el default es `False` (3s), igual que el comportamiento actual.

## Pasos
1. `git pull` → quedar en `3453051`.
2. `supervisorctl restart all`.
3. **NO** hace falta `bench build` (sin JS) ni `bench migrate` (sin DocType nuevo).
4. Opcional, no urgente: si querés limpiar el dato viejo en DB, `laser_c_s_per_m2` del
   registro "Chapa doble decapada 2.0mm" en SI Material Corte ya no se usa — podés dejarlo
   como está (1.1852, inofensivo, el código lo ignora) o correr de nuevo
   `set_laser_coefs.run` para que quede en 0. No es necesario para que funcione.

No urgente — no cambia el comportamiento actual hasta que Vega conecte el checkbox de
"apto flycut". Deployalo cuando te quede cómodo.

— Punto
