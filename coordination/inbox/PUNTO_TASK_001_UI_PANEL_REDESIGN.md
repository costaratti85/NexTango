# Tarea para Punto — Rediseño de la UI del módulo de paneles

**De:** Nova  
**Fecha:** 2026-06-11  
**Prioridad:** Alta — primera entrega verificable por Constantino  
**Motor:** `C:\SistemaIndustrial\Nextango\Programas_hechos\Panel Decorativo\`

---

## Contexto

El programa en `Programas_hechos/Panel Decorativo/` ya hace todo correctamente:
- Tresbolillo y patrones DXF con el mismo motor
- Librería de patrones persistente (`pattern_library.json`)
- Dos modos de distribución (`cut_partial_figures`)
- Margen sin perforar
- Funciona sobre rectángulos

**El trabajo no es reescribir el motor. Es construirle una UI web que exponga todo lo que ya hace.**

La UI vive en `apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py` y corre en `http://127.0.0.1:8765`. La interfaz web es intencional — a futuro será accesible desde cualquier dispositivo, incluyendo clientes externos.

---

## Correcciones obligatorias antes de la UI nueva

**1. Corregir el adapter al motor canónico.**
En `legacy_panel_adapter.py` línea 19, cambiar:
```python
DEFAULT_LEGACY_DIR = Path(__file__).resolve().parents[4] / "Paneles decorativos funcionando"
```
por:
```python
DEFAULT_LEGACY_DIR = Path(__file__).resolve().parents[4] / "Programas_hechos" / "Panel Decorativo"
```
Verificar antes que los módulos que importa el adapter existen en esa ubicación (`main`, `config.settings`, `layout.cad_result_layout`, `dxf.mixed_exporter`).

**2. Verificar que los tests siguen pasando** después del cambio de path.

---

## Flujo que debe implementar la UI

### Paso 1 — Encabezado del trabajo
- Cliente o referencia
- Nombre del trabajo / número de pedido

### Paso 2 — Forma exterior
Desplegable: `Rectángulo` (único por ahora)

### Paso 3 — ¿Perforar?
Toggle o desplegable: Sí / No  
- Si **No**: la pieza va como rectángulo limpio, sin patrón
- Si **Sí**: aparece el selector de patrón

### Paso 4 — Librería de patrones (solo si perforar = Sí)
La librería usa `config/pattern_library.py` y `pattern_library.json` del motor. Exponer:

- Lista de patrones guardados → al elegir uno, carga sus parámetros
- **Tresbolillo** → parámetros: diámetro del agujero (mm) + distancia entre centros (mm)
- **Patrón DXF** (de librería) → parámetros: offset X (mm) + offset Y (mm)
- Botón **Cargar patrón nuevo**: nombre + archivo .dxf + offset X + offset Y → guarda en librería
- Botón **Borrar patrón**: elimina de la librería

### Paso 5 — Margen sin perforar
Campo numérico: **Margen (mm)** — borde desde el borde de la pieza hasta la zona perforada.  
*(A futuro podría ser por lado; por ahora un valor aplica a los cuatro lados)*

### Paso 6 — Modo de distribución
Radio o desplegable con dos opciones:
- **Figuras completas centradas** — calcula cuántas figuras entran sin cortar, descarta las que no entran, centra el resultado (`cut_partial_figures = False`)
- **Cortar en borde** — multiplica filas y columnas, las figuras que caen sobre el margen se cortan (`cut_partial_figures = True`)

### Paso 7 — Material y espesor
- Material (texto)
- Espesor mm (número)

### Paso 8 — Lista de piezas
Textarea o input múltiple donde el usuario ingresa:
```
2 de 1000x1500
3 de 500x800
1 de 250x250
```
Formato: `<cantidad> de <ancho>x<alto>`

Botón **AGREGAR** — acumula este lote (patrón + material + espesor + lista de piezas) en una tabla de lotes pendientes.

El usuario puede volver al paso 3 y agregar otro lote con diferente patrón/material.

### Paso 9 — Tabla de lotes acumulados
Muestra todos los lotes agregados:
- Patrón | Modo | Margen | Material | Espesor | Piezas
- Opción de eliminar un lote

### Paso 10 — Generar
Botón **GENERAR DXF** — ejecuta el motor para todos los lotes, genera:
- DXF compilado con todas las piezas
- `panel_result.json`
- `quotation_payload.json`
- `manifest.json`

El DXF debe mostrar las piezas **ordenadas: filas por espesor, dentro de cada fila ordenadas por cantidad descendente**.

---

## Lo que hay que eliminar de la UI actual

- El desplegable "Preset / tipo de panel" (duplicado e innecesario)
- Los campos **Filas** y **Columnas** (el motor los ignora, confunden)
- El campo "Modo de panel" actual — reemplazado por el nuevo flujo

---

## Modelo de datos — cambios en `LegacyPanelServiceInput`

El modelo actual maneja una sola pieza a la vez. Para la nueva UI con múltiples piezas y lotes, `panel_sales_local_app.py` necesita:
- Una estructura de "lote" (un patrón + material + espesor + lista de `(ancho, alto, cantidad)`)
- Una lista de lotes que se acumulan antes de generar
- El motor ya acepta `sheet_sizes = [(ancho, alto, cantidad), ...]` — hay que pasarle toda la lista

No crear nuevas clases en `panel_service.py` o `legacy_panel_adapter.py` si no es necesario. `LegacyPanelRunRequest.sheet_sizes` ya acepta múltiples tamaños.

---

## Librería de patrones — integración

El motor legacy ya tiene `config/pattern_library.py`. El adapter debe poder:
- Leer los patrones guardados en `pattern_library.json` para mostrar la lista en la UI
- Guardar nuevos patrones llamando a `PatternLibrary.add_pattern()`
- Eliminar patrones llamando a `PatternLibrary.delete_pattern()`

Estas operaciones deben ocurrir sobre el `pattern_library.json` dentro de `Programas_hechos/Panel Decorativo/`, que es la fuente de verdad de la librería.

---

## Verificación antes de marcar como terminado

1. `python tools/run_panel_sales_app.py` levanta sin errores
2. Modo **Tresbolillo + Figuras completas centradas**: agregar 2 de 300x200, generar → DXF tiene el patrón centrado sin cortes
3. Modo **Tresbolillo + Cortar en borde**: mismas medidas → DXF tiene agujeros cortados en el borde
4. Modo **DXF patrón**: cargar `Programas_hechos/Panel Decorativo/input.dxf`, generar → DXF correcto
5. Lote múltiple: agregar 3 piezas de distintos tamaños, generar → todas aparecen en el DXF
6. Librería: cargar patrón nuevo → aparece en la lista en la próxima sesión
7. Sin perforar: generar rectángulo sin patrón → DXF tiene solo el contorno exterior
8. `python -m pytest` → todos los tests pasan

---

## Reportar en

`coordination/reports/PUNTO_PANEL_UI_REDESIGN_REPORT.md`

Incluir: qué cambió, screenshot o descripción del resultado para cada modo, si el adapter al motor nuevo fue compatible sin ajustes.
