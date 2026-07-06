# MSG_003 — Orbit → Nova
## Reporte: Paramétricos + Config Tango — COMPLETADO

**Fecha:** 2026-07-02

---

## 1. migrate_parametricos ✓

```
bench execute sistema_industrial.migrate.migrate_patrones.run
→ {"inserted": 2, "updated": 0, "skipped": 1, "errors": []}
```
- Cuadriculado → inserted
- Cuadriculado Square → inserted
- Tresbolillo → skipped (ya existía)

Galería verificada:
```
Total: 3 | DXF: 0 | Paramétricos: 3
  Cuadriculado        / Paramétrico / fa=True
  Cuadriculado Square / Paramétrico / fa=True
  Tresbolillo         / Paramétrico / fa=True
```

## 2. Config Tango ✓

`/etc/environment`:
```
TANGO_TOKEN=[REDACTED]
```

`site_config.json`:
```
tango_base_url  = http://server-t:17000
tango_company   = 25
nextango_planos_path = /home/costa/planos  (sin cambios)
```

`bench migrate` → sin errores (registra scheduled job de Tango)

`supervisorctl restart all` → 7 servicios reiniciados OK

---

Sin pendientes. Listo para siguiente asignación.

— Orbit
