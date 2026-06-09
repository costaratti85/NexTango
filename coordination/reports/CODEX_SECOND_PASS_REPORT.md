# Reporte Codex - Second Pass

## Objetivo

Validar coherencia del repo despues del primer commit y dejar claro el siguiente paso para convertir `sistema_industrial` en app Frappe instalable sobre ERPNext.

## Estado git

Comando inicial:

```powershell
git status --short
```

Resultado inicial: working tree limpio.

Luego de la revision se aplico una correccion documental menor en `docs/12_FRAPPE_DOCTYPES_BLUEPRINT.md` y se creo este reporte.

## Tests

Comando:

```powershell
$env:PYTHONPATH='apps/sistema_industrial'; python -m pytest -q
```

Resultado:

```text
16 passed in 0.64s
```

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

## Reporte inicial revisado

Archivo revisado:

- `coordination/reports/CODEX_INITIAL_REPO_MOUNT_REPORT.md`

Conclusiones:

- El reporte inicial documenta correctamente los documentos leidos, comandos, tests, demo, archivos tocados y faltantes para bench.
- Mantiene los limites: no ERPNext core, no Tango real, no nesting, no G-code.
- El faltante principal sigue siendo validar instalacion en un bench ERPNext real de prueba.

## DocTypes vs blueprint

Archivo revisado:

- `docs/12_FRAPPE_DOCTYPES_BLUEPRINT.md`

DocTypes esperados y encontrados:

- `SI Preset`
- `SI Client Piece`
- `SI Cut Piece`
- `SI Cut Batch`
- `SI Tango Price Cache`
- `SI Linear Cut Request`

Stubs encontrados en:

- `apps/sistema_industrial/sistema_industrial/doctype/si_preset/si_preset.json`
- `apps/sistema_industrial/sistema_industrial/doctype/si_client_piece/si_client_piece.json`
- `apps/sistema_industrial/sistema_industrial/doctype/si_cut_piece/si_cut_piece.json`
- `apps/sistema_industrial/sistema_industrial/doctype/si_cut_batch/si_cut_batch.json`
- `apps/sistema_industrial/sistema_industrial/doctype/si_tango_price_cache/si_tango_price_cache.json`
- `apps/sistema_industrial/sistema_industrial/doctype/si_linear_cut_request/si_linear_cut_request.json`

Correccion menor aplicada:

- `SI Linear Cut Request` estaba listado como DocType inicial y tambien como futuro. Se removio de la lista futura porque ya existe como stub inicial.

## Archivos tocados

- `docs/12_FRAPPE_DOCTYPES_BLUEPRINT.md`
- `coordination/reports/CODEX_SECOND_PASS_REPORT.md`

## Limites respetados

- No se toco ERPNext core.
- No se implemento nesting.
- No se implemento G-code.
- No se conecto Tango real.
- No se modifico la logica de dominio neutral.

## Proximos pasos para app Frappe instalable

1. Definir version objetivo de Frappe/ERPNext para el bench de prueba.
2. Agregar metadata de instalacion compatible con esa version si `bench get-app` lo requiere.
3. Crear un bench ERPNext sandbox y traer este repo como app.
4. Ejecutar `bench --site <site> install-app sistema_industrial`.
5. Validar que los DocTypes carguen sin errores de schema, naming, permisos o modulo.
6. Crear roles/permisos reales para vendedor, taller, administracion y auditoria.
7. Convertir los facades actuales en endpoints Frappe finos que llamen servicios neutrales existentes.
8. Definir persistencia Frappe para cola de corte, manifest y estado por pieza.
9. Agregar pruebas de instalacion/migracion en entorno bench.
