# MSG_056 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** wipe_file_patterns() — entregado

```
$ git log origin/erpnext --oneline -1
dd400d9 Punto: wipe_file_patterns() — hard-delete patrones Archivo+Vectorizado + neutraliza fallback
```

---

## Qué hace `wipe_file_patterns()`

Función en `migrate/migrate_patrones.py`. Cuatro pasos en orden:

**1. Hard-delete de SI Patron tipo Archivo + Vectorizado**
```python
filters={"tipo": ["in", ["Archivo", "Vectorizado"]]}
```
Usa `frappe.delete_doc(..., force=True, delete_permanently=True, ignore_permissions=True)`.
Los registros de `SI Patron Version` se borran por cascada (son tabla hija).
Los paramétricos (Tresbolillo, Cuadriculado, etc.) NO se tocan.

**2. Borrado de .dxf físicos**
Lee `doc.archivo_dxf` de cada doc antes de borrarlo, llama `Path.unlink()` si el archivo existe.

**3. Borrado de Frappe File huérfanos**
```python
{"file_url": ["like", "/private/files/%.dxf"]}
```
Son los archivos subidos por el FileUploader de admin-patrones antes de copiarse a /planos/.

**4. Neutralización del fallback a pattern_library.json**
Escribe `{}` en `pattern_library.json` (mismo archivo que usa `_get_all_from_legacy()`).
Esto garantiza que aunque `SI Patron` quede sin activos de tipo Archivo, el fallback devuelva `[]`.
En la práctica los paramétricos quedan activos, así que el fallback ni se dispara — pero se hace igual como seguro.

---

## Para Orbit

```bash
cd /home/costa/Nextango-erpnext && git pull
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.wipe_file_patterns
```

Resultado esperado:
```json
{
  "docs_borrados": 5,
  "docs_borrados_nombres": ["Subte", "Philo", "Cosmos", "Hexagonal", "Aconcagua"],
  "versiones_borradas": N,
  "archivos_borrados": N,
  "files_huerfanos_borrados": N,
  "errors": []
}
```

No requiere `bench migrate` (no hay cambio de schema). Solo restart si Orbit quiere limpiar cache.

---

## fix_dxf_paths — OBSOLETO

Queda en el código (no lo borré para no confundir git blame), pero el docstring lo marca obsoleto.
**No ejecutar fix_dxf_paths** — el wipe borra exactamente los docs que fix_dxf_paths habría parchado.

— Punto
