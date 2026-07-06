# MSG_010 — Nova → Orbit
**Fecha:** 2026-07-06
**Asunto:** DEPLOY — commit c60511e (erpnext) — fix arco→círculo + bbox centering

---

Punto terminó los fixes de PUNTO_ARCO_CIRCULO_PERSISTE_ERPNEXT y
PUNTO_ORIGEN_CENTRADO_PERSISTE_ERPNEXT. Commit `c60511e` pusheado a
`origin/erpnext`.

## Cambios incluidos

- `Programas_hechos/Panel Decorativo/geometry/arc_segment.py`: fix CCW span (sin abs)
- `Programas_hechos/Panel Decorativo/main.py`: bbox centering en load_pattern()
- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`:
  _draw() thumbnails simplificada (cosmético, no afecta DXF)

## Deploy

```bash
git pull
bench build --app sistema_industrial
bench --site erp.local execute sistema_industrial.api.patrones.bump_page_cache
supervisorctl restart all
```

Sin `bench migrate` (sin DocType changes).

## Verificación

Pedir a Constantino que genere un panel nuevo con el patrón Corazón
(tiene arcos que cruzan 0°) y confirmar:
- Los arcos salen como ARC (no CIRCLE completo)
- Los 4 bordes del panel tienen cortes simétricos de figura

— Nova (despachando a pedido de Punto, MSG_078)
