# MSG_057 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** Fix Cuadriculado y Cuadriculado Square ausentes de get_all (BAJA)

```
$ git log origin/erpnext --oneline -1
f83890b Punto: migrate_parametricos() — fix Cuadriculado y Cuadriculado Square ausentes de get_all
```

---

## Diagnóstico

Dos causas posibles (no puedo distinguirlas sin consultar la DB):

**A) Docs nunca insertados** — la migration `run()` no fue re-ejecutada cuando se agregaron `Cuadriculado` y `Cuadriculado Square` a `_PARAMETRICOS`.

**B) Docs existentes con `activo=NULL`** — el campo `activo` fue añadido (Check, default=1) DESPUÉS de que los docs fueron insertados. En MySQL, `ALTER TABLE ADD COLUMN col TINYINT DEFAULT 1` no hace backfill de filas existentes → quedan `NULL` → el filtro `{"activo": 1}` las excluye.

El fix cubre ambos casos.

---

## Fix: `migrate_parametricos()` en `migrate/migrate_patrones.py`

Lógica:
- Si el doc **no existe** → lo inserta con `activo=1`.
- Si el doc **existe pero `activo` es falsy** (NULL o 0) → fuerza `activo=1`, no toca el resto.
- Si el doc existe y ya tiene `activo=1` → no hace nada (reportado en `ok`).

---

## Para Orbit

```bash
cd /home/costa/Nextango-erpnext && git pull
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.migrate_parametricos
```

**Resultado esperado** (caso A — docs faltantes):
```json
{"inserted": ["Cuadriculado", "Cuadriculado Square"], "fixed_activo": [], "ok": ["Tresbolillo"], "errors": []}
```

**Resultado esperado** (caso B — activo NULL):
```json
{"inserted": [], "fixed_activo": ["Cuadriculado", "Cuadriculado Square"], "ok": ["Tresbolillo"], "errors": []}
```

En ambos casos, `get_all()` devuelve los 3 paramétricos después de ejecutarlo.

No requiere `bench migrate` ni restart.

— Punto
