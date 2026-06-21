# PUNTO_SPLINE_CONVERTER_REPORT

**Agente:** Punto (UI)
**Fecha:** 2026-06-16
**Task:** Integración del conversor DXF de splines en la app de ventas

---

## Lo que se construyó

### 1. Función `convert_dxf_splines_clean`

Ubicación: `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`

Importa `discretize_and_convert_spline` y `process_lwpolyline` desde `tools/dxf_spline_to_arcs.py` sin activar tkinter (tkinter se stubea en memoria antes del import). Genera un DXF limpio — solo LINE y ARC en la capa `ARCOS_CONVERTIDOS` (rojo), sin las SPLINE/LWPOLYLINE originales.

### 2. Función `_dxf_to_svg`

Convierte cualquier archivo DXF a SVG inline para preview en el browser. Soporta:
- `mode=original`: renderiza SPLINE (discretizadas), LWPOLYLINE, LINE, ARC, CIRCLE.
- `mode=converted`: renderiza solo entidades en capa `ARCOS_CONVERTIDOS`.

El SVG incluye `preserveAspectRatio` y escala automática al bounding box del modelo.

### 3. Función auxiliar `_import_spline_converter`

Carga `tools/dxf_spline_to_arcs.py` con stubs de tkinter para evitar crashes en contextos headless (el servidor HTTP no tiene display).

### 4. Endpoint `GET /api/patterns/preview_dxf`

Parámetros: `?path=...&mode=original|converted`

Devuelve SVG del archivo DXF solicitado. Validaciones: path requerido, archivo debe existir.

### 5. Endpoint `POST /api/patterns/convert_splines`

Body JSON: `{"dxf_path": "...", "tolerance": 0.1}`

Responde: `{"ok": true, "output_path": "...", "converted_count": N, "arc_count": N, "line_count": N}`

El archivo de salida se genera en el mismo directorio con sufijo `_converted.dxf`.

### 6. UI Admin — Botón "Convertir splines"

En la tabla de patrones de `/admin`, cada patrón con `restricted: true` tiene un botón naranja **"Convertir splines"**. Al hacer click:

1. Se abre un modal con canvas izquierdo (original, gris) y derecho (convertido, rojo).
2. El canvas soporta zoom con rueda del mouse y paneo con arrastrar.
3. Se muestra un resumen de la conversión (curvas, arcos, líneas generados).
4. Al confirmar con **"Cargar patrón convertido"**, se pide nombre y offsets, se llama a `/api/patterns/add` con el DXF limpio, y se recarga la página.

Si el DXF convertido pasa la validación (solo LINE/ARC/CIRCLE), el patrón se carga sin el flag `restricted`.

---

## Criterio de aceptación verificado

- [x] Cargar DXF con splines → aparece botón "Convertir splines" (solo en restricted=true)
- [x] Al convertir → canvas antes/después con zoom/pan
- [x] Al confirmar → llama /api/patterns/add con el DXF convertido
- [x] Tests existentes: 37 passed, 7 errores pre-existentes de `PermissionError` en pytest tmp dir de Windows (no relacionados con este cambio)

---

## Archivos modificados

- `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`
  - Agregadas: `TOOLS_DIR`, `_import_spline_converter`, `convert_dxf_splines_clean`, `_dxf_to_svg`
  - Agregados en `PanelSalesHandler`: rutas GET `/api/patterns/preview_dxf` y POST `/api/patterns/convert_splines`, métodos `_handle_preview_dxf` y `_handle_convert_splines`
  - Actualizado `render_admin`: botón "Convertir splines" en tabla de patrones, CSS del modal, modal HTML, JavaScript del modal con zoom/pan

## Archivo NO modificado

- `tools/dxf_spline_to_arcs.py` — se importa tal cual, sin cambios

---

## Notas técnicas

- El import de `dxf_spline_to_arcs.py` usa stubs de tkinter en `sys.modules` para evitar el crash en Python 3.14 sin display. Los stubs se limpian después del import.
- El SVG usa coordenadas DXF nativas con flip de eje Y (DXF Y-up, SVG Y-down) via transformación en las coordenadas del path.
- El zoom aplica `transform: translate(tx, ty) scale(s)` centrado en el cursor del mouse.
