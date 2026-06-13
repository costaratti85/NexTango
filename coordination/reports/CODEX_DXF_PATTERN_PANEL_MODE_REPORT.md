# Reporte Codex - DXF Pattern Panel Mode

## Objetivo

Exponer en la interfaz local de venta interna la modalidad legacy de chapa decorativa por patron DXF repetido, sin modificar el algoritmo ni archivos del programa viejo.

## Funcion legacy localizada

Carpeta:

- `C:\SistemaIndustrial\Nextango\Paneles decorativos funcionando`

Funciones principales:

- `Paneles decorativos funcionando/main.py`
  - `load_pattern(settings)`
  - `generate_cut_mode_geometry(...)`
  - `generate_centered_full_mode_geometry(...)`
  - `create_cad_result_items_from_batch(settings)`

Archivos de soporte:

- `Paneles decorativos funcionando/dxf/importer.py`
  - `DXFImporter.load(filename)` carga el patron DXF.
- `Paneles decorativos funcionando/dxf/mixed_exporter.py`
  - `MixedDXFExporter.save(items, filename)` genera el DXF final.
- `Paneles decorativos funcionando/config/user_input.py`
  - En el flujo interactivo viejo, `choose_pattern(settings)` setea:
    - `settings.pattern_type = "dxf"`
    - `settings.input_file`
    - `settings.step_x`
    - `settings.step_y`

La repeticion en grilla ocurre en `main.generate_cut_mode_geometry(...)`:

- calcula `cols = int(usable_width / step_x) + 3`
- calcula `rows = int(usable_height / step_y) + 3`
- itera filas/columnas
- mueve cada figura con `figure.translated(dx, dy)`
- recorta contra el margen si corresponde

## Campos legacy requeridos

El motor legacy recibe un objeto `Settings` con:

- `pattern_type = "dxf"`
- `pattern_name`
- `input_file`: ruta al DXF patron
- `step_x`: offset X / paso X
- `step_y`: offset Y / paso Y
- `material`
- `thickness`
- `margin`
- `sheet_sizes`: lista `(ancho, alto, cantidad)`
- `cut_partial_figures`
- `output_file`

Importante: el legacy no recibe filas/columnas como control directo en esta ruta. Calcula filas y columnas desde ancho/alto util y `step_x/step_y`. En la interfaz Nextango se muestran filas/columnas como referencia operativa y se guardan en trazabilidad, pero no se usan para alterar el algoritmo legacy.

## Cambios en adaptador

Archivo:

- `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py`

Se mantiene el llamado al legacy intacto y se soportan dos tipos legacy:

- `tresbolillo`
- `dxf`

El modo Nextango `dxf_pattern_grid` se traduce a `pattern_type="dxf"` para el legacy.

El adaptador ahora valida:

- existe el archivo DXF patron,
- existen offset X/Y (`step_x_mm`, `step_y_mm`),
- el tipo de patron legacy es soportado.

Tambien registra en `legacy_result_raw.request`:

- `pattern_dxf_path`
- `offset_x_mm`
- `offset_y_mm`
- `step_x_mm`
- `step_y_mm`
- `rows`
- `columns`

## Cambios en servicio

Archivo:

- `apps/sistema_industrial/sistema_industrial/presets/panel_service.py`

Se agrego:

- `panel_mode`

Valores:

- `tresbolillo`
- `dxf_pattern_grid`

El servicio normaliza:

- `panel_mode="tresbolillo"` -> `pattern_type="tresbolillo"`
- `panel_mode="dxf_pattern_grid"` -> `pattern_type="dxf"`

El payload de cotizacion y el resultado normalizado incluyen:

- `panel_mode`
- `pattern_dxf_path`
- `offset_x_mm`
- `offset_y_mm`
- `rows`
- `columns`

## Cambios en interfaz local

Archivo:

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

La pantalla ahora permite elegir:

1. `Tresbolillo`
2. `Patron DXF repetido`

Para `Tresbolillo` muestra:

- diametro,
- distancia.

Para `Patron DXF repetido` muestra:

- archivo DXF patron,
- offset X,
- offset Y,
- filas,
- columnas.

La interfaz simple usa ruta local del DXF patron en vez de upload binario. Ejemplo cargado por defecto:

```text
C:\SistemaIndustrial\Nextango\Paneles decorativos funcionando\input.dxf
```

## Como probar

Comando:

```powershell
cd C:\SistemaIndustrial\Nextango
python tools/run_panel_sales_app.py
```

Abrir:

```text
http://127.0.0.1:8765
```

Elegir:

- `Modo de panel`: `Patron DXF repetido`
- `Archivo DXF patron`: `C:\SistemaIndustrial\Nextango\Paneles decorativos funcionando\input.dxf`
- `Offset X mm`: `84`
- `Offset Y mm`: `84`
- `Ancho mm`: `300`
- `Alto mm`: `200`
- `Material`: `chapa`
- `Espesor`: `3`
- `Cantidad`: `1`

Salida esperada en:

- `outputs/panel_sales_demo/panel_result.json`
- `outputs/panel_sales_demo/quotation_payload.json`
- `outputs/panel_sales_demo/cut_piece_payload.json`
- `outputs/panel_sales_demo/manifest.json`
- `outputs/panel_sales_demo/VENTA-CLIENTE-DEMO-PANEL-DXF-REPETIDO_legacy_panel.dxf`

## Tests

Comando:

```powershell
$env:PYTHONPATH='apps/sistema_industrial'; python -m pytest -q
```

Resultado:

```text
25 passed, 7 warnings in 3.78s
```

Cobertura agregada:

- tresbolillo sigue funcionando,
- `dxf_pattern_grid` ejecuta el legacy con `input.dxf`,
- genera salida normalizada,
- `main.py` del legacy no se modifica durante la corrida,
- el formulario HTTP acepta modo DXF repetido y genera archivos.

## Demo ejecutada

Se ejecuto una generacion real de `dxf_pattern_grid`.

Resultado:

- `panel_mode`: `dxf_pattern_grid`
- DXF final: `C:\SistemaIndustrial\Nextango\outputs\panel_sales_demo\VENTA-CLIENTE-DEMO-PANEL-DXF-REPETIDO_legacy_panel.dxf`
- Manifest: `C:\SistemaIndustrial\Nextango\outputs\panel_sales_demo\manifest.json`

## Limitaciones

- La interfaz local permite ingresar ruta local del DXF patron; todavia no sube archivos desde browser.
- Filas y columnas se guardan como trazabilidad, pero el legacy calcula la grilla desde dimensiones de chapa y offset X/Y.
- El selector usa por ahora dos modos base; todavia no administra biblioteca de patrones DXF desde la UI.
- El legacy sigue devolviendo `cut_length_mm=0` y `pierce_count=0`; se preservan esos valores sin inventar formulas.
- No hay persistencia ERPNext/Frappe todavia.

## Limites respetados

- No se modifico el algoritmo legacy.
- No se modificaron archivos dentro de `Paneles decorativos funcionando`.
- No se implemento nesting.
- No se implemento G-code.
- No se conecto Tango real.
- No se toco ERPNext core.
