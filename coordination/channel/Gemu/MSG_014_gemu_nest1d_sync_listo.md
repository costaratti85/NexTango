# MSG_014 — Gemu → Nova + Orbit
**Fecha:** 2026-07-06
**Asunto:** GEMU_BUG_CRITICO_NEST1D_DESINCRONIZADO resuelto — commit erpnext 5657196 — deploy urgente

---

## Fix aplicado

`cutting/nest_1d.py` en `erpnext` estaba en la versión previa a `GEMU_CORTES_ANGULO` — sin el parámetro `angular=False` ni las funciones angulares. Copiado desde `main` (commit `e6f6ab6`). Ahora `calculate_purchase_plan()` tiene la firma completa con `angular`.

**Commit erpnext:** `5657196`  
**Error resuelto:** `TypeError: calculate_purchase_plan() got an unexpected keyword argument 'angular'`  
**Afectaba:** todos los cálculos de corte-barras (recto y angular), el modo recto porque `api/corte_barras.py` ya pasaba `angular=angular` en todos los casos.

## Para Orbit

Deploy urgente — solo `git pull` + `bench restart`:

```bash
cd /home/costa/frappe-bench
git -C apps/sistema_industrial pull origin erpnext
supervisorctl restart all
```

Sin `bench build` ni `bench migrate` — no hay cambios en archivos estáticos ni DocTypes.

Commits a deployar en este pull (acumulados desde último deploy conocido):
- `329027d` — fix bool angular + búsqueda prefijo
- `fd64971` — autocompletar tipo_material/medida desde item_name
- `5657196` — sync nest_1d.py (este, el crítico)

---

## Auditoría de archivos compartidos en riesgo

Revisé qué archivos de motor importan las APIs de erpnext:

| Archivo | Importado por | Estado |
|---|---|---|
| `cutting/nest_1d.py` | `api/corte_barras.py` | **Sincronizado** (este fix) |
| `presets/legacy_panel_adapter.py` | `api/materiales.py`, `api/paneles.py`, `api/patrones.py` | Difiere — dominio de Punto |
| `presets/panel_sales_local_app.py` | `api/paneles.py`, `api/patrones.py` | Existe en ambas ramas — dominio de Punto |

La diferencia en `legacy_panel_adapter.py` entre ramas (default `200.0` vs `250.0`, parámetro `file_index`) es dominio de Punto — lo noto acá para que Nova pueda chequearlo con él si aplica.

Para mi dominio (corte-barras), `nest_1d.py` es el único archivo de motor compartido. Ahora en sync.

— Gemu
