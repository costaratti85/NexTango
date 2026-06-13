# Tarea para Punto — Correcciones UI panel (validación visual de Constantino)

**De:** Nova  
**Fecha:** 2026-06-11  
**Prioridad:** Alta — bloquea el testing de Constantino  
**Contexto:** Constantino probó la UI en vivo. Encontró los problemas descritos abajo.

---

## Bug 1 — Sección DXF de librería no aparece (BLOQUEANTE)

**Síntoma:** Al hacer clic en "DXF de librería", la sección de parámetros no aparece. La pantalla salta directamente a "5 — Margen sin perforar".

**Causa exacta:** `<div id="dxf-params" class="hidden">` arranca con la clase CSS `hidden` que tiene `display:none !important`. El JS hace `element.style.display = ''` para mostrarla, pero el `!important` gana y el elemento sigue oculto.

**Fix:** Cambiar `class="hidden"` a `style="display:none"` en el div `dxf-params`. Así el JS puede sobreescribir el display con `style.display`. Verificar que `tresbolillo-params` también funciona correctamente en el cambio de modo.

---

## Bug 2 — "Sin perforar" usa el motor con un tresbolillo gigante

**Síntoma:** Al elegir No en el toggle de perforar, el sistema llama al motor pasándole un tresbolillo con diámetro 2× el lado más largo de la chapa. Esto produce geometría incorrecta en el DXF.

**Causa exacta:** En `_build_settings` (`legacy_panel_adapter.py`), el bloque `if request.pattern_type == "none":` setea el tresbolillo gigante pero no fuerza `settings.cut_partial_figures = False`. Con el default `cut_partial_figures = True`, el motor ejecuta `generate_cut_mode_geometry` que clipea el círculo enorme contra el área útil y produce geometría que rellena el área útil — no solo el contorno.

**Fix correcto según Constantino:** El modo "sin perforar" NO debe llamar al motor legacy en absoluto. Solo debe dibujar el rectángulo exterior de la pieza directamente, sin invocar `create_cad_result_items_from_batch`. Generar el DXF del contorno rectangular de forma directa (usando `ezdxf` o el `MixedDXFExporter` con solo el outline).

**Fix alternativo mínimo (si lo anterior es complejo):** Agregar `settings.cut_partial_figures = False` en el bloque `none` del adapter. Esto hace que `generate_centered_full_mode_geometry` detecte que el patrón es más grande que el área útil y devuelva solo el outline. Funciona, pero es un hack. Usar el fix correcto si es razonable.

---

## Mejora 3 — Carga de patrón DXF requiere explorador de carpetas nativo

**Síntoma:** El campo "Ruta local del archivo DXF" es un input de texto donde hay que tipear la ruta manualmente. Constantino quiere navegar carpetas con un explorador nativo de Windows para elegir el archivo.

**Fix:** Implementar un botón "Examinar..." que abra el explorador nativo de Windows. Como la UI corre en localhost y el servidor Python corre en la misma máquina, la solución es:

1. Agregar un endpoint `GET /api/browse-dxf` al servidor HTTP. Cuando se llama, abre `tkinter.filedialog.askopenfilename(filetypes=[("DXF", "*.dxf")])` y devuelve la ruta seleccionada como JSON `{"path": "C:\\...\\patron.dxf"}`. Si el usuario cancela, devuelve `{"path": ""}`.

2. En la UI, reemplazar el `<input type="text" id="lib_new_path">` por un campo de texto readonly + botón "Examinar...". Al hacer clic en "Examinar...", el JS llama a `/api/browse-dxf` y pone el resultado en el campo.

3. Asegurarse que los campos **Offset X mm** y **Offset Y mm** sean claramente visibles justo debajo del selector de archivo, antes del botón "Guardar en librería". El usuario define el offset después de elegir el archivo.

**Nota técnica:** `tkinter` puede tener conflictos con el thread del servidor HTTP. Usar `threading` para abrir el diálogo en el thread principal o con `Tk().withdraw()` antes de llamar `askopenfilename`. Probar que funcione en Windows 10.

---

## Mejora 4 — Tresbolillo no borrable en la librería

**Requisito de Constantino:** El Tresbolillo es un patrón permanente y no puede borrarse de la librería. Cuando el usuario selecciona "Tresbolillo" desde la librería, el botón "Borrar patrón seleccionado" no debe aparecer.

**Fix:** En `loadLibraryPattern()`, si el nombre del patrón seleccionado es `"Tresbolillo"` (o si el pattern tiene un flag `builtin: true`), no mostrar el botón de borrar. El Tresbolillo no está en la librería JSON — es un modo hardcodeado en el toggle. Verificar que la arquitectura sea consistente: o el Tresbolillo vive como un modo separado (como está ahora), o se agrega a la librería con flag `builtin`.

---

## Verificación antes de marcar como terminado

1. Elegir "DXF de librería" → aparece la sección de parámetros y la opción de cargar patrón nuevo
2. Botón de archivo en "Cargar patrón nuevo" → abre el explorador de Windows para elegir `.dxf`
3. Cargar un `.dxf` de prueba → aparece en el dropdown de la librería
4. Elegir "No" en perforar → genera DXF con solo el contorno rectangular, sin agujeros ni geometría adicional
5. `python -m pytest` → todos los tests que pasaban antes siguen pasando

## Reportar en

`coordination/reports/PUNTO_UI_DXF_CORRECTION_REPORT.md`
