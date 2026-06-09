# Reporte Codex - Initial Repo Mount

## Leido

- README.md
- docs/00_BRUJU_MESSAGE_TO_TEAM.md
- docs/00_PROJECT_NORTH_STAR.md
- docs/22_FIRST_SLICE_TEAM.md
- docs/23_AGENT_PERMISSIONS_MATRIX.md
- docs/24_MONDAY_CODEX_SINGLE_ORDER.md
- docs/25_AGENT_HANDOFF_PROTOCOL.md
- docs/26_DEFINITION_OF_DONE.md
- docs/27_FIRST_SLICE_BACKLOG.md
- docs/28_EXECUTION_COMMANDS.md
- docs/29_AGENT_ZOO.md
- docs/CODEX_ONE_SHOT_REPO_MOUNT_ORDER.md
- docs/12_FRAPPE_DOCTYPES_BLUEPRINT.md

## Hecho

- Revise la estructura actual del repo.
- Verifique que la logica de dominio queda desacoplada de Frappe en `core`, `application`, `presets`, `quoting`, `pricing_sync` y `cutting`.
- Instale la dependencia dev declarada (`pytest`) para poder ejecutar la suite local.
- Prepare estructura minima de app Frappe sin requerir bench:
  - `modules.txt`
  - `config/desktop.py`
  - carpeta `doctype`
  - stubs JSON/Python para DocTypes iniciales.
- Actualice el blueprint interno de DocTypes para alinear la primera rebanada con:
  - SI Preset
  - SI Client Piece
  - SI Cut Piece
  - SI Cut Batch
  - SI Tango Price Cache
  - SI Linear Cut Request
- Agregue test neutral para validar que los stubs Frappe existen y conservan nombres/modulo esperados.
- Ejecute demo panel decorativo -> quotation payload -> cola de corte -> lote DXF.
- No implemente nesting.
- No implemente G-code.
- No toque ERPNext core.
- No toque Tango real.

## Comandos corridos

```powershell
Get-ChildItem -Force
Get-Content README.md
Get-Content docs/00_BRUJU_MESSAGE_TO_TEAM.md
Get-Content docs/00_PROJECT_NORTH_STAR.md
Get-Content docs/22_FIRST_SLICE_TEAM.md
Get-Content docs/23_AGENT_PERMISSIONS_MATRIX.md
Get-Content docs/24_MONDAY_CODEX_SINGLE_ORDER.md
Get-Content docs/25_AGENT_HANDOFF_PROTOCOL.md
Get-Content docs/26_DEFINITION_OF_DONE.md
Get-Content docs/27_FIRST_SLICE_BACKLOG.md
Get-Content docs/28_EXECUTION_COMMANDS.md
Get-Content docs/29_AGENT_ZOO.md
Get-Content docs/CODEX_ONE_SHOT_REPO_MOUNT_ORDER.md
rg --files
git status --short
$env:PYTHONPATH='apps/sistema_industrial'; python -m pytest -q
$env:PYTHONPATH='apps/sistema_industrial'; python tools/demo_panel_to_cut_batch.py
python -m pip install -r requirements-dev.txt
Test-Path local_output/quotation_payload.json
Test-Path local_output/cut_queue.json
Test-Path local_output/CUT_BATCH_CHAPA_3MM_DEMO.dxf
Test-Path local_output/CUT_BATCH_CHAPA_3MM_DEMO.manifest.json
```

## Tests

- Primer intento: `python -m pytest -q` fallo porque el Python local no tenia `pytest`.
- Instalacion dev: `python -m pip install -r requirements-dev.txt` exitosa luego de aprobar red.
- Suite final: `PYTHONPATH=apps/sistema_industrial python -m pytest -q`
- Resultado final: `16 passed in 0.18s`

## Demo

Comando:

```powershell
$env:PYTHONPATH='apps/sistema_industrial'; python tools/demo_panel_to_cut_batch.py
```

Resultado:

- `local_output/quotation_payload.json`
- `local_output/cut_queue.json`
- `local_output/CUT_BATCH_CHAPA_3MM_DEMO.dxf`
- `local_output/CUT_BATCH_CHAPA_3MM_DEMO.manifest.json`
- `part_count`: 2

## Archivos tocados

- apps/sistema_industrial/sistema_industrial/modules.txt
- apps/sistema_industrial/sistema_industrial/config/__init__.py
- apps/sistema_industrial/sistema_industrial/config/desktop.py
- apps/sistema_industrial/sistema_industrial/doctype/__init__.py
- apps/sistema_industrial/sistema_industrial/doctype/si_preset/__init__.py
- apps/sistema_industrial/sistema_industrial/doctype/si_preset/si_preset.py
- apps/sistema_industrial/sistema_industrial/doctype/si_preset/si_preset.json
- apps/sistema_industrial/sistema_industrial/doctype/si_client_piece/__init__.py
- apps/sistema_industrial/sistema_industrial/doctype/si_client_piece/si_client_piece.py
- apps/sistema_industrial/sistema_industrial/doctype/si_client_piece/si_client_piece.json
- apps/sistema_industrial/sistema_industrial/doctype/si_cut_piece/__init__.py
- apps/sistema_industrial/sistema_industrial/doctype/si_cut_piece/si_cut_piece.py
- apps/sistema_industrial/sistema_industrial/doctype/si_cut_piece/si_cut_piece.json
- apps/sistema_industrial/sistema_industrial/doctype/si_cut_batch/__init__.py
- apps/sistema_industrial/sistema_industrial/doctype/si_cut_batch/si_cut_batch.py
- apps/sistema_industrial/sistema_industrial/doctype/si_cut_batch/si_cut_batch.json
- apps/sistema_industrial/sistema_industrial/doctype/si_tango_price_cache/__init__.py
- apps/sistema_industrial/sistema_industrial/doctype/si_tango_price_cache/si_tango_price_cache.py
- apps/sistema_industrial/sistema_industrial/doctype/si_tango_price_cache/si_tango_price_cache.json
- apps/sistema_industrial/sistema_industrial/doctype/si_linear_cut_request/__init__.py
- apps/sistema_industrial/sistema_industrial/doctype/si_linear_cut_request/si_linear_cut_request.py
- apps/sistema_industrial/sistema_industrial/doctype/si_linear_cut_request/si_linear_cut_request.json
- apps/sistema_industrial/sistema_industrial/erpnext_extensions/doctype_blueprint.py
- docs/12_FRAPPE_DOCTYPES_BLUEPRINT.md
- tests/test_frappe_doctype_stubs.py
- coordination/reports/CODEX_INITIAL_REPO_MOUNT_REPORT.md

## Falta para instalar como app Frappe real

- Crear metadata completa de app instalable para bench si el repo se va a consumir directamente desde `bench get-app` (`pyproject`/`setup` de app, segun version de Frappe objetivo).
- Validar los DocTypes dentro de un bench ERPNext de prueba con `bench --site <site> install-app sistema_industrial`.
- Ajustar permisos por rol real de vendedor, taller, admin y auditoria.
- Conectar los stubs DocType a servicios/adaptadores finos que llamen la logica neutral existente.
- Definir persistencia real para cola de corte y manifest dentro de Frappe, sin reemplazar CypCut ni postprocesador.
- Agregar fixtures o migraciones Frappe si se requieren para workspace, roles y permisos.
- Crear pruebas de instalacion en bench/sitio de prueba cuando exista entorno ERPNext.
