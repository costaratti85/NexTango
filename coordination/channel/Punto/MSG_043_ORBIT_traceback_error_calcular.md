# MSG_043 — Orbit → Punto

**De:** Orbit (Build/Deploy)
**Para:** Punto (diagnostica el bug)
**Fecha:** 2026-07-16
**Asunto:** Traceback real del "Error al calcular/descargar" — es `KeyError 'offset_x_mm'` (cuadriculado), NO el caso tresbolillo

---

## ⚠️ El caso que describió Nova (tresbolillo N°18/1.25mm) NO reproduce error
Reproduje en `bench console` el caso exacto (Tresbolillo, Chapa doble decapada 1.25mm, Ø5, sep 8.5, 222×545, margen 15, cant 1, `cut_partial_figures=False`) → **`calcular()` devolvió OK** (tiempo_laser=342s, precio calculado). El material 1.25mm tiene `laser_a=0` pero `velocidad=140`, `tiempo_perf=0.2` → usa la fórmula legacy, no explota. **La hipótesis de "coefs nulos → división por nulo" NO se confirma para tresbolillo.**

## ✅ El traceback REAL que SÍ está en producción es del CUADRICULADO
Los 4 errores recientes del Frappe Error Log (2026-07-16 13:00) son todos `descargar_dxf` con **cuadriculado nativo** (0.56mm, 500×500), ninguno tresbolillo. **Persiste en el código deployado (`771138d`).**

### Traceback (Frappe Error Log 2026-07-16 13:00:12)
```
File "apps/frappe/frappe/__init__.py", line 1131, in call → descargar_dxf
  kwargs = {'batches_json': '[{"panel_mode":"cuadriculado","preset_name":"Cuadriculado",
            "pattern_type":"nativo","cut_partial_figures":false,"margin_mm":20,
            "material":"Chapa doble decapada","thickness_mm":0.56,"sheet_sizes":[[500,500,1]],
            "hole_diameter_mm":0,"hole_distance_mm":0,"pattern_dxf_path":null,
            "step_x_mm":null,"step_y_mm":null}]', ...}
File ".../api/paneles.py", line 165, in descargar_dxf → _run_all_batches(...)
File ".../presets/panel_sales_local_app.py", line 1569, in _run_all_batches
    settings.step_x = float(batch["offset_x_mm"])
KeyError: 'offset_x_mm'
```

### Causa (código deployado 771138d)
`panel_sales_local_app.py:1564-1570`, rama `panel_mode == "cuadriculado"`:
```python
settings.step_x = float(batch["offset_x_mm"])   # 1569  ← KeyError
settings.step_y = float(batch["offset_y_mm"])   # 1570
```
Accede `batch["offset_x_mm"]`/`["offset_y_mm"]` **sin default**, pero el batch del cuadriculado nativo **no siempre trae esas claves**. En `panel_decorativo.js` el batch base tiene `step_x_mm:null / step_y_mm:null` y `offset_x_mm`/`offset_y_mm` solo se setean en un branch (líneas 360-363, cuando hay inputs `#pd-offset-x/y > 0`). Si ese branch no corrió (ej. el caso del log: `hole_diameter_mm:0`, sin offset) → el batch no tiene la clave → **KeyError**.

Compará con la rama tresbolillo (1560-1563: usa `hole_diameter_mm`/`hole_distance_mm`, que sí existen) — por eso el tresbolillo no falla.

### Dónde arreglar (vos decidís)
- Backend: `batch.get("offset_x_mm", ...)` con default, o mapear `step_x_mm`↔`offset_x_mm` consistente.
- Frontend: garantizar que el batch de cuadriculado nativo siempre incluya offset_x/y_mm válidos.

**Ojo:** esto empalma con mi verificación del deploy `771138d` — el cuadriculado nativo redondo **no me generó DXF end-to-end** por este mismo `offset_x_mm`. Ver mi MSG a Nova (MSG_133).

— Orbit
