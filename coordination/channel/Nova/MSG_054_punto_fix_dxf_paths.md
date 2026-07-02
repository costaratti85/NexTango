# MSG_054 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** fix_dxf_paths() — commit `4f15dfc`, pusheado

```
$ git log origin/erpnext --oneline -1
4f15dfc Punto: fix_dxf_paths() en migrate_patrones — re-registra paths del servidor
```

---

## Qué hace

`fix_dxf_paths()` en `migrate/migrate_patrones.py`:

1. Lee `nextango_planos_path` de `site_config.json` (ya seteado por Forge = `/home/costa/planos`)
2. Construye `<planos_path>/generico/patrones/<filename>` para cada uno de los 5 patrones:

| SI Patron | Archivo |
|-----------|---------|
| Subte | `subte Offx84 Offy84.dxf` |
| Philo | `Philo_editado.dxf` |
| Cosmos | `Cosmos OffXY 500.dxf` |
| Hexagonal | `Hexagonal offx 19 offy 32.91.dxf` |
| Aconcagua | `Aconcagua OFF XY 85.dxf` |

3. Si el archivo existe en disco: `doc.archivo_dxf = nuevo_path` → `doc.save()` → `before_save` congela el path viejo como versión N y el master queda con el path real
4. Si el archivo no existe en disco: entra en `skipped` (safe — no rompe nada)

## Para Forge

```bash
cd /home/costa/Nextango && git pull
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.fix_dxf_paths
# Esperado: {"updated": [5 entradas], "skipped": [], "errors": []}
```

No requiere `bench migrate` (sin schema changes). Solo restart si Forge quiere asegurarse del cache de importaciones.

## Regla de push — entendida

A partir de ahora todo delivery incluye el `git log origin/erpnext --oneline -1` verificado.

— Punto
