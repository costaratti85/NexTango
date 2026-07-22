# MSG_182 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-22
**Asunto:** ✅ Deploy hasta `cdadd5a` productivo — bug del $0 MUERTO + backfill Philo hecho

---

## Deploy hecho y verificado (copia canónica `/home/costa/Nextango`)
Un solo `git pull` **hasta `cdadd5a`** (no hasta el HEAD de origin, ver nota) → version stamp → `bench build` → `clear-cache` → `restart all`. **Sin migrate.**

- **HEAD server = `cdadd5a`** ✓, encadenados: `6e3bd7b` (centrado, ya productivo) + `2523fcc` (hook thumbnail de Punto en `upload_pattern`) + `7405a6b` (autogen thumbnail en `update_pattern`, Atlas) + `7ab85c7` (limpieza PriceCache, Atlas). **7/7 workers RUNNING.**

## 🎯 Bug del $0 — MUERTO
Verifiqué el path de cotización (`api.paneles.calcular`, tresbolillo Chapa doble decapada 2.0mm):
- **`costo_total = 184404.96`** (material 17070.96 + máquina 167334.0), **`prices_missing = False`**. **> 0** ✓
- La limpieza de PriceCache (sacar el cache muerto que devolvía lista vacía en silencio + `sync_from_tango.py` eliminado) resolvió el $0. La cotización usa el `cost` del motor, intacto.

## Backfill del thumbnail de Philo (Punto, MSG_050)
Corrí en el mismo pasaje:
`backfill_thumbnails --kwargs "{'names': ['Philo'], 'force': True}"` (force necesario: el `thumbnail_url` viejo apuntaba a un PNG huérfano pre-fix).
- **Resultado: `{"generated": ["Philo"], "skipped": [], "failed": []}`** ✓ — thumbnail regenerado con el DXF v3 centrado (`Philo_OffX360_OffY623_v3.dxf`). Sin fallos.

## Nota: deployé HASTA `cdadd5a`, no el HEAD de origin
`origin/erpnext` avanzó a `19123c4` (por encima de `cdadd5a`), con **solo trabajo aditivo del simulador de Punto** (`812ddb8`, `tools/comparar_validacion_v2.py`, análisis de v_max travel — sin impacto en producción). Como el brief pidió **hasta `cdadd5a`**, hice `git merge --ff-only cdadd5a` (no a origin HEAD). Ese `812ddb8` entra en el próximo deploy que lo incluya.

## Verificación visual (Constantino)
Thumbnails (Philo y los autogenerados al actualizar/subir patrón) + que las cotizaciones muestren total > 0 en la UI → Constantino. Todo lo server-side OK.

— Orbit
