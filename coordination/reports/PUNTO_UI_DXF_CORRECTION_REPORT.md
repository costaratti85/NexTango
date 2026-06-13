# PUNTO_UI_DXF_CORRECTION_REPORT

Agente: Punto  
Fecha: 2026-06-11  
Tarea: PUNTO_TASK_002_UI_DXF_CORRECTION  

---

## Resumen

Se implementaron los 4 puntos de la tarea. Los 32 tests pasaron (antes y después). Los archivos modificados son:

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
- `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py`

---

## Fix 1 — Bug CSS/JS: sección DXF no aparece (BLOQUEANTE)

**Qué cambió:**  
En `panel_sales_local_app.py`, el div `<div id="dxf-params">` pasó de:

```html
<div id="dxf-params" class="hidden">
```

a:

```html
<div id="dxf-params" style="display:none">
```

**Por qué:** La clase CSS `.hidden { display:none !important; }` bloquea el override inline del JS (`element.style.display = ''`). Con `style="display:none"` el JS puede reemplazarlo directamente sin luchar contra `!important`.

**Verificado:** El test `test_render_form_contains_dxf_pattern_section` sigue pasando. La verificación programática confirma que el HTML generado contiene `id="dxf-params" style="display:none"` y no la clase `hidden`. No se pudo verificar visualmente en browser (entorno sin GUI), pero la mecánica CSS/JS es correcta por construcción.

**Tresbolillo-params:** Ya estaba visible por defecto (sin clase `hidden`), no requirió cambio.

---

## Fix 2 — Bug "Sin perforar": no debe llamar al motor con holes

**Qué cambió:**

En `legacy_panel_adapter.py`, en `_build_settings`, bloque `pattern_type == "none"`:

```python
# Antes: no se tocaba cut_partial_figures
settings.cut_partial_figures = False   # ← nuevo
```

En `panel_sales_local_app.py`, en `_run_all_batches`, bloque `panel_mode == "none"`:

```python
settings.cut_partial_figures = False   # ← nuevo
```

**Mecanismo:** Con `cut_partial_figures=False`, el motor llama a `generate_centered_full_mode_geometry`. Esta función devuelve solo el outline cuando el patrón es más grande que el área útil (`pattern_width > usable_width`). Al combinarlo con el diámetro gigante ya existente (`max_dim * 2`), el tresbolillo siempre excede el área útil y solo se genera el contorno rectangular. No se llama al motor legacy con agujeros reales.

**Verificado:** Test unitario con `_build_settings` confirma `cut_partial_figures=False`, `pattern_type="tresbolillo"`, y `hole_diameter > sheet_width`. Tests de integración `test_legacy_panel_adapter_runs_and_returns_normalized_result` y otros siguen en verde. Verificación funcional completa (generar DXF sin perforar) no se pudo confirmar en GUI — ver sección "No probado".

---

## Fix 3 — Explorador de archivos nativo con tkinter

**Qué cambió:**

1. **Backend** — función `_browse_dxf_file()` añadida en `panel_sales_local_app.py`:
   - Importa `tkinter` y `filedialog` dentro del try/except (falla silenciosamente si tkinter no está disponible)
   - Crea `Tk()`, lo oculta con `withdraw()`, lo marca `topmost`, llama a `askopenfilename` filtrando `*.dxf`
   - Destruye la ventana al terminar, retorna la ruta o `""` si el usuario cancela

2. **Endpoint GET `/api/browse-dxf`** añadido en `do_GET`:
   - Llama a `_browse_dxf_file()` y devuelve `{"path": "..."}` como JSON

3. **HTML** — campo `dxf_pattern_path` ahora tiene layout flex con botón al lado:
   ```html
   <div style="display:flex;gap:8px;align-items:center">
     <input id="dxf_pattern_path" ... readonly style="flex:1">
     <button type="button" class="btn-sm" onclick="browseDxfFile()">Examinar...</button>
   </div>
   ```

4. **JS** — función `browseDxfFile()` añadida:
   - Hace `fetch('/api/browse-dxf')`
   - Si `data.path` no es vacío, lo pone en el campo `dxf_pattern_path`

**Verificado:** Tests `test_render_form_contains_dxf_pattern_section` y `test_render_form_contains_sales_controls` siguen pasando. La verificación programática confirma presencia de `Examinar...`, `browseDxfFile`, `offset_x_mm`, `offset_y_mm` en el HTML. Los campos Offset X/Y son visibles y editables inmediatamente debajo del selector de archivo.

**No probado (headless):** El diálogo tkinter en sí no puede abrirse en entorno sin GUI. Lo que se verificó es que `_browse_dxf_file()` maneja la excepción correctamente (retorna `""`) cuando tkinter falla — el endpoint devuelve `{"path": ""}` y el JS no actualiza el campo.

---

## Fix 4 — Tresbolillo: botón "Borrar patrón" no debe aparecer

**Qué cambió:** Ningún cambio de código fue necesario.

**Verificado:** El botón `Borrar patron seleccionado` está dentro del div `id="lib-pattern-delete-row"` que a su vez está dentro del div `id="dxf-params"`. Cuando el usuario está en modo Tresbolillo, `dxf-params` tiene `display:none` y el botón es completamente invisible. Esto ya era correcto antes de esta tarea.

Adicionalmente, el botón también se oculta dentro del modo DXF cuando no hay patrón seleccionado (`lib_pattern_select` con valor vacío), via `loadLibraryPattern()` que asigna `className = 'hidden'`.

---

## Tests

```
32 passed, 8 warnings
```

Todos los tests anteriores siguen pasando. El recuento subió de 30 a 32 porque se incorporaron al worktree los archivos de tests `test_legacy_panel_adapter.py` y `test_panel_sales_local_app.py` que ya existían en el repo principal como untracked.

Comando: `PYTHONPATH=apps/sistema_industrial python -m pytest tests/ -q --basetemp=/c/tmp_pytest`

---

## Verificación funcional — estado por caso

| Caso | Estado | Nota |
|------|--------|------|
| 1. DXF de librería → sección de parámetros aparece | No verificado en browser | Mecánica CSS/JS correcta por construcción (Fix 1) |
| 2. Botón "Examinar..." → abre explorador | No verificado en GUI | Tkinter no disponible en entorno headless; endpoint y JS implementados correctamente |
| 3. Offset X/Y visibles y editables | Verificado programáticamente | Campos presentes en HTML sin ningún `hidden` |
| 4. "Sin perforar" → DXF solo contorno | No verificado con motor real | Lógica verificada: `cut_partial_figures=False` + oversized hole → solo outline |
| 5. pytest → mínimo 22 passed | **32 passed** | Superado |

---

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py` — Fix 1, 2 (batch path), 3 (endpoint + HTML + JS)
- `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py` — Fix 2 (adapter path)
