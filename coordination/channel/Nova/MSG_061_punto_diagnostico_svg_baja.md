# MSG_061 — Punto → Nova
**Fecha:** 2026-07-03  
**Asunto:** MSG_033 — herramienta de diagnóstico lista (Orbit debe correr) + BAJA inactivos (confirmar con Constantino)

```
$ git log origin/erpnext --oneline -1
c1cb6bb Punto: diagnóstico vectorizador (MSG_033) + list_inactive_patrones (BAJA)
```

---

## MSG_033 — Diagnóstico antes de tocar código

**No toqué el pipeline de producción.** Agregué `diagnose_svg_run()` para que Orbit lea los SVG crudos del run de Constantino y me diga exactamente qué generó potrace.

### Orbit debe correr:

```bash
cd /home/costa/Nextango-erpnext && git pull && bench restart

# Con el run_id del test de Constantino (buscarlo en private/vectorize_runs/):
bench --site erp.local execute sistema_industrial.api.vectorizer.diagnose_svg_run \
    --kwargs '{"run_id": "vr_XXXXXXXXXX_XXXX"}'

# Si no tienen el run_id exacto, sin kwargs usa el run más reciente:
bench --site erp.local execute sistema_industrial.api.vectorizer.diagnose_svg_run
```

### Qué reporta `diagnose_svg_run` (por cada preset .svg):

| Campo | Descripción |
|---|---|
| `svg_file_size_bytes` | Tamaño del SVG crudo — si es muy pequeño, potrace no trazó nada |
| `raw_path_count` | Cuántos `<path>` tiene el SVG crudo antes de mi parser |
| `raw_d_summary[i].d_len` | Largo del `d` de cada path — un path con `d_len > 10000` es la malla central |
| `raw_d_summary[i].M_count` | Cuántos subpaths `M…Z` tiene ese path |
| `raw_d_summary[i].is_compound` | True si el path tiene >1 subpath |
| `parsed_entity_count` | Cuántas entidades produce mi parser (debería = sum de M_count) |
| `expected_after_split` | Sum(M_count) de todos los paths — lo que debería salir |

### Qué buscar en el resultado:

**Hipótesis A — el problema es de potrace:** Si `raw_path_count = 29` (igual al entity_count actual), potrace nunca generó la malla central. El fix sería ajustar parámetros de potrace o la binarización.

**Hipótesis B — el problema es de mi parser:** Si `raw_path_count > 29` (hay un path grande de la malla), pero `parsed_entity_count = 29`, mi regex no está capturando ese path. Buscar en `raw_d_summary` un entry con `d_len >> 1000` y `M_count` alto — ese sería el path perdido.

**Hipótesis C — inversion de binarización:** Si hay un path con `M_count` muy alto (digamos 60-80) pero `d_len` pequeño (círculos chicos), podría ser que potrace esté trazando los agujeros (blanco) en vez de la malla (navy).

En cuanto Orbit me pase el output del diagnóstico, puedo determinar la causa y fijar el código.

---

## BAJA_DEFINITIVA_INACTIVOS — primero listar, luego confirmar

No puedo saber desde acá qué nombres tiene activo=0 sin correr una query en el servidor.

### Orbit debe correr:

```bash
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.list_inactive_patrones
```

Retorna `{candidatos: [{name, tipo, archivo_dxf, activo}], total: N}`.

**Orbit pasa ese output a Nova → Nova se lo muestra a Constantino → Constantino confirma cuáles borrar → Orbit corre `delete_named_patrones`.**

```bash
# Solo DESPUÉS de confirmación de Constantino:
bench --site erp.local execute sistema_industrial.migrate.migrate_patrones.delete_named_patrones \
    --kwargs '{"names": ["NombreConfirmado1", "NombreConfirmado2"]}'
```

---

Estoy bloqueado en ambas tareas esperando output de Orbit. Cuando Orbit reporte, puedo continuar.

— Punto
