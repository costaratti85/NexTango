# Reporte Codex - Legacy Panel Integration

## Objetivo

Integrar el programa legacy de paneles decorativos dentro de Nextango mediante una capa adaptadora, sin modificar su algoritmo, y dejar una demo local util para Constantino.

## Ubicacion del legacy

`C:\SistemaIndustrial\Nextango\Paneles decorativos funcionando`

La carpeta legacy estaba presente como carpeta no versionada. No se modificaron archivos dentro de esa carpeta.

## Archivos principales detectados

- `Paneles decorativos funcionando/main.py`: archivo principal y orquestador del motor legacy.
- `Paneles decorativos funcionando/config/user_input.py`: entrada interactiva por consola/Tk.
- `Paneles decorativos funcionando/config/settings.py`: objeto `Settings` usado por el motor.
- `Paneles decorativos funcionando/dxf/importer.py`: importador DXF legacy.
- `Paneles decorativos funcionando/dxf/mixed_exporter.py`: exportador DXF legacy.
- `Paneles decorativos funcionando/layout/cad_result_layout.py`: acomoda resultados antes de exportar.
- `Paneles decorativos funcionando/geometry/tresbolillo_pattern.py`: patron tresbolillo circular.
- `Paneles decorativos funcionando/pattern_library.json`: biblioteca legacy, con rutas historicas externas.

## Como se ejecuta el legacy

Modo original:

```powershell
cd "C:\SistemaIndustrial\Nextango\Paneles decorativos funcionando"
python main.py
```

Ese modo es interactivo:

- pide patron por consola,
- puede abrir dialogos Tk para elegir/guardar DXF,
- pide material, espesor, margen, modo de generacion y medidas de chapa.

Para Nextango no se automatizo la UI. Se llamaron directamente las funciones existentes del legacy:

- `create_cad_result_items_from_batch(settings)`
- `arrange_cad_result_items(items)`
- `MixedDXFExporter().save(items, output_file)`

Esto evita tocar el algoritmo y evita depender de intervencion visual humana para la demo.

## Parametros detectados

El legacy recibe datos mediante `Settings`:

- `pattern_type`: `dxf` o `tresbolillo`
- `pattern_name`
- `input_file` para patrones DXF
- `step_x`, `step_y` para patrones DXF
- `hole_diameter`, `hole_distance` para tresbolillo
- `material`
- `thickness`
- `margin`
- `sheet_sizes`: lista de `(width, height, quantity)`
- `cut_partial_figures`
- `output_file`

## Archivos que genera

El legacy genera DXF mediante `MixedDXFExporter.save(...)`.

La demo Nextango genera:

- `outputs/panel_legacy_demo/panel_result.json`
- `outputs/panel_legacy_demo/quotation_payload.json`
- `outputs/panel_legacy_demo/cut_piece_payload.json`
- `outputs/panel_legacy_demo/PED-LEGACY-DEMO-001_legacy_panel.dxf`
- `outputs/panel_legacy_demo/manifest.json`

## Dependencias

- Python
- `ezdxf`
- `tkinter` para el modo interactivo original

Se agrego `ezdxf>=1.4` a `pyproject.toml` porque el importador/exportador legacy lo requiere.

## Adaptador creado

Archivo:

- `apps/sistema_industrial/sistema_industrial/presets/legacy_panel_adapter.py`

Responsabilidad:

- localizar la carpeta legacy,
- preparar `Settings` con input normalizado,
- ejecutar el motor legacy desde su propia carpeta,
- exportar el DXF con el exportador legacy,
- devolver resultado normalizado sin modificar el algoritmo.

## Servicio creado

Archivo:

- `apps/sistema_industrial/sistema_industrial/presets/panel_service.py`

Responsabilidad:

- tomar un input normalizado Nextango,
- llamar al adaptador legacy,
- construir `quotation_payload` estilo ERPNext,
- construir `cut_piece_payload`,
- escribir `panel_result.json`, `quotation_payload.json`, `cut_piece_payload.json` y `manifest.json`.

Resultado normalizado incluido:

- `preset_code`
- `preset_name`
- `material`
- `thickness_mm`
- `width_mm`
- `height_mm`
- `quantity`
- `calculated_resources`
- `dxf_path`
- `warnings`
- `legacy_result_raw`
- `cut_piece_payload`
- `quotation_payload`

## Script demo

Archivo:

- `tools/run_panel_legacy_demo.py`

Comando para Constantino:

```powershell
cd C:\SistemaIndustrial\Nextango
$env:PYTHONPATH="apps/sistema_industrial"
python tools/run_panel_legacy_demo.py
```

Resultado esperado:

- imprime las rutas de los archivos generados,
- genera un DXF legacy,
- genera payload de cotizacion,
- genera pieza pendiente,
- genera manifest de trazabilidad.

## Tests agregados

Archivo:

- `tests/test_legacy_panel_adapter.py`

Cubre:

- el adaptador encuentra el programa legacy,
- el adaptador ejecuta una corrida tresbolillo y genera DXF,
- el servicio devuelve resultado normalizado con quotation/cut piece payloads.

## Tests corridos

```powershell
$env:PYTHONPATH='apps/sistema_industrial'; python -m pytest -q
```

Resultado:

```text
19 passed, 7 warnings in 2.85s
```

Las warnings vienen de `ezdxf`/`pyparsing`, no del codigo Nextango.

## Demos corridas

Demo legacy nueva:

```powershell
$env:PYTHONPATH='apps/sistema_industrial'; python tools/run_panel_legacy_demo.py
```

Resultado:

- `outputs/panel_legacy_demo/panel_result.json`
- `outputs/panel_legacy_demo/quotation_payload.json`
- `outputs/panel_legacy_demo/cut_piece_payload.json`
- `outputs/panel_legacy_demo/PED-LEGACY-DEMO-001_legacy_panel.dxf`
- `outputs/panel_legacy_demo/manifest.json`

Demo tecnica anterior:

```powershell
$env:PYTHONPATH='apps/sistema_industrial'; python tools/demo_panel_to_cut_batch.py
```

Resultado:

- `local_output/quotation_payload.json`
- `local_output/cut_queue.json`
- `local_output/CUT_BATCH_CHAPA_3MM_DEMO.dxf`
- `local_output/CUT_BATCH_CHAPA_3MM_DEMO.manifest.json`
- `part_count`: 2

## Limitaciones

- La demo usa el patron legacy `tresbolillo`, porque no depende de rutas historicas externas.
- `pattern_library.json` contiene rutas viejas como `C:/Python/LaserCAD/input.dxf`; para patrones DXF reales hay que normalizar la carga desde Nextango.
- El legacy devuelve `cut_length_mm=0` y `pierce_count=0`; el adaptador preserva esos valores y emite warnings, sin inventar formulas.
- La salida `outputs/` esta ignorada por git; la demo la regenera localmente.
- No hay todavia DocType Frappe conectado al servicio.

## Limites respetados

- No se modifico el algoritmo legacy.
- No se modificaron archivos dentro de `Paneles decorativos funcionando`.
- No se toco ERPNext core.
- No se conecto Tango real.
- No se implemento nesting.
- No se implemento G-code.
- El legacy queda encapsulado como motor dentro de Nextango, no como programa paralelo.

## Proximos pasos para SI Preset en Frappe

1. Crear un metodo de DocType `SI Preset` que arme `LegacyPanelServiceInput`.
2. Guardar el resultado en DocTypes `SI Client Piece`, `SI Cut Piece` y/o `SI Cut Batch` segun el flujo.
3. Persistir el DXF como File privado en Frappe.
4. Persistir `manifest.json` o su contenido como trazabilidad auditable.
5. Crear permisos para vendedor/taller/admin antes de exponerlo en UI.
6. Agregar un endpoint Frappe fino que llame `LegacyPanelService`, sin mover reglas al adaptador Frappe.
