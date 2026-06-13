# CODEX_FIX_DXF_PATTERN_UI_REPORT

Fecha: 2026-06-09

## Objetivo

Corregir la interfaz local de paneles para que el modo `dxf_pattern_grid` quede expuesto como modo usable real y no vuelva silenciosamente a tresbolillo.

## Cambios realizados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
  - El modo seleccionado ahora se normaliza con `_selected_mode`.
  - `GET /?panel_mode=dxf_pattern_grid` renderiza HTML de DXF sin controles de tresbolillo.
  - El selector de modo navega a `/?panel_mode=<modo>` para que el HTML servido cambie realmente.
  - El formulario DXF incluye:
    - `dxf_pattern_file`
    - `dxf_pattern_path`
    - `offset_x_mm`
    - `offset_y_mm`
    - `rows`
    - `columns`
  - El formulario usa `enctype="multipart/form-data"` para permitir carga de archivo DXF.
  - El POST soporta `multipart/form-data` con librería estándar `email`, guarda DXF subido en `outputs/panel_sales_demo/uploaded_patterns`, y si no hay upload usa `dxf_pattern_path`.
  - `build_sales_input` acepta `dxf_pattern_path`, conserva compatibilidad con `pattern_dxf_path`, exige DXF en modo DXF y no parsea diámetro/distancia cuando `panel_mode=dxf_pattern_grid`.

- `tests/test_panel_sales_local_app.py`
  - Test para fallar si el HTML DXF contiene `Diametro` o `Distancia entre agujeros`.
  - Test para verificar presencia de DXF, offset X y offset Y.
  - Test para error claro si falta DXF patrón.
  - Test para confirmar que `LegacyPanelService` entrega `pattern_type="dxf"` al adaptador.
  - Test de ejecución real `dxf_pattern_grid` con fixture DXF mínimo.

- `tests/fixtures/minimal_pattern.dxf`
  - Fixture DXF mínimo para ejecutar el flujo legacy DXF sin depender de archivos grandes del motor legacy.

## Confirmaciones

- Submit DXF envía `panel_mode=dxf_pattern_grid`.
- `panel_service` normaliza `panel_mode=dxf_pattern_grid` a `pattern_type="dxf"`.
- `legacy_panel_adapter` mantiene la bifurcación existente: solo llama la configuración de tresbolillo cuando `request.pattern_type == "tresbolillo"`.
- No se modificó el algoritmo legacy.
- No se simula DXF con tresbolillo.
- Si falta DXF patrón, se muestra error claro: `Archivo DXF patron requerido para Patron DXF repetido`.

## Verificación automática

Comando:

```powershell
$env:PYTHONPATH='C:\SistemaIndustrial\Nextango\apps\sistema_industrial'; python -m pytest
```

Resultado:

```text
29 passed, 7 warnings
```

## Verificación local HTTP

Página:

```text
http://127.0.0.1:8765/?panel_mode=dxf_pattern_grid
```

Resultado del HTML servido:

```text
HasDxfFile           : True
HasDxfPath           : True
HasOffsetX           : True
HasOffsetY           : True
HasRows              : True
HasColumns           : True
HasDiametro          : False
HasDistanciaAgujeros : False
SelectedDxf          : True
```

POST real contra `http://127.0.0.1:8765/generate`:

```text
StatusCode        : 200
HasResultado      : True
PanelMode         : dxf_pattern_grid
LegacyPatternType : dxf
DxfExists         : True
OffsetX           : 84.0
OffsetY           : 84.0
```

## Verificación visual

Captura generada con Edge headless:

```text
outputs/panel_sales_demo/dxf_pattern_ui_full.png
```

La captura muestra el modo `Patron DXF repetido` con:

- Archivo DXF patron
- Ruta local del DXF patron
- Offset X mm
- Offset Y mm
- Filas
- Columnas

La captura no muestra:

- Diametro
- Distancia entre agujeros
