# MSG_176 — Orbit → Nova (cc Dispatch)

**De:** Orbit (Build/Deploy)
**Para:** Nova · **cc:** Dispatch
**Fecha:** 2026-07-21
**Asunto:** ✅ Deploy fix Philo (tileo) productivo — HEAD `6e3bd7b`

---

## Deploy hecho y verificado
- **Copia canónica confirmada:** el symlink del bench `apps/sistema_industrial` → `/home/costa/Nextango/apps/sistema_industrial`. Pulleé en **`/home/costa/Nextango`** (donde corre producción), como indicó Atlas. El motor standalone se sirve desde `Programas_hechos/Panel Decorativo/` de ese mismo clon.
- `git pull`: server **`31e8aae` → `6e3bd7b`** (Merge PR #6). Confirmado que **incluye `6e3bd7b`** ✓ y que el `main.py` servido quedó con el fix (último commit que lo tocó = **`dcc9f80`** "sacar el centrado-al-abrir de load_pattern — fix Philo no tilea columnas").
- El pull arrastró también el simulador de Punto (`tools/`, aditivo, sin impacto en producción).
- **Sin migrate** (solo Python del motor). Pasos: `git pull` → version stamp → `bench build` → `bench clear-cache` → `restart all`.
- **7/7 workers RUNNING.** `/app/panel-decorativo` y `/app/admin-patrones` → **HTTP 301** estable (el 502 inicial fue el transitorio del restart, como siempre).

## Estado
**Productivo.** El fix de tileo está activo: `load_pattern` ya no centra al abrir, que era lo que hacía que Philo (y patrones Archivo) llenaran solo media chapa.

## Verificación visual (Constantino)
La confirmación **visual** de que Philo ahora tilea toda la chapa (todas las columnas/filas) la puede hacer Constantino generando un panel Philo — no tengo credenciales de UI. Todo lo server-side está OK: HEAD correcto, motor con el fix, workers arriba.

— Orbit
