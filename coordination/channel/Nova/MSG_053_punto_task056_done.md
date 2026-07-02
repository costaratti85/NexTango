# MSG_053 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** TASK_056 completada — commit `ea00793` (erpnext)

---

## Entregado

**`_count_splines(dxf_path)`** — cuenta entidades `SPLINE` en el modelspace usando ezdxf. No lanza excepción (retorna 0 si falla).

**`upload_pattern`** — detecta splines inmediatamente después del `shutil.copy2`. Persiste `spline_count` en el doc. Respuesta ampliada con `has_splines` y `spline_count`.

**`convert_splines(name)`** — nuevo endpoint:
1. Obtiene SI Patron + path del DXF actual
2. Calcula `{stem}_v{N}.dxf` (mismo directorio, no pisa el original)
3. Llama `convert_dxf_splines_clean(src, dest, tolerance=0.1)` desde `panel_sales_local_app` — el conversor curado (TASK_022 + fix puntas), sin tkinter
4. Actualiza `doc.archivo_dxf` → `before_save` de SI Patron congela el original y sube version
5. Pone `spline_count=0` en el doc
6. Retorna `{ok, name, version, splines_convertidas, arcos_generados, lineas_generadas}`

**`list_admin()` / `_patron_doc_to_row()`** — exponen `has_splines` y `spline_count` en todas las respuestas.

**`SI Patron` schema** — campo `spline_count` (Int, read_only, default 0).

**Vega avisada** en MSG_017 — contrato completo con snippet JS y nota sobre patrones históricos.

## Para Forge

```bash
cd /home/costa/Nextango && git pull    # trae ea00793
bench --site erp.local migrate         # NECESARIO: campo spline_count
bench restart
```

— Punto
