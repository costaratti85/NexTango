# MSG_006 — Thumbnails en selector "Modo de distribución"

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-19  

---

## Pedido de Constantino

En la pantalla `/` (formulario de nuevo pedido), sección **"Modo de distribución"**, mostrar los thumbnails de ejemplo debajo de cada opción de radio, para que el usuario vea visualmente la diferencia antes de elegir.

## Ubicación exacta en el código

`apps/sistema_industrial/sistema_industrial/presets/panel_sales_local_app.py`, líneas ~2203–2218:

```html
<!-- Modo de distribucion -->
<div class="form-row">
  <div class="form-group">
    <label>Modo de distribucion</label>
    <div class="radio-group" id="dist-group">
      <label class="checked-option" id="lbl-centradas" onclick="setDist('centradas')">
        <input type="radio" name="distrib" value="centradas" checked>
        Figuras completas centradas
      </label>
      <label id="lbl-cortar" onclick="setDist('cortar')">
        <input type="radio" name="distrib" value="cortar">
        Cortar en borde
      </label>
    </div>
    <div class="field-hint">...</div>
  </div>
</div>
```

## Imágenes disponibles

Ya existen dos imágenes generadas (script `tools/gen_comparison_thumbnails.py`):

- `tools/comparacion_modos.png` — side-by-side, 14×5 pulgadas @130dpi (las dos juntas)

Para mostrarlas por separado necesitás uno de estos enfoques (a tu criterio):

**Opción A** — Generar dos imágenes individuales desde el mismo script (split o dos runs separados), guardarlas como `tools/comparacion_centradas.png` y `tools/comparacion_cortar.png`, y servirlas con un endpoint `/static/<filename>` en `PanelSalesHandler`.

**Opción B** — Leer la imagen side-by-side existente, codificarla como base64 al iniciar el server, y en el HTML usar una sola `<img>` con `data:image/png;base64,…` recortada con CSS (`object-fit: cover; object-position: left/right`).

**Opción C (más simple)** — Agregar un endpoint `/static/<filename>` que sirve archivos desde `tools/`, luego mostrar la imagen side-by-side completa debajo del radio group con un caption.

## Comportamiento esperado

- Cada opción de radio tiene debajo su thumbnail representativo (o bien uno solo side-by-side debajo del grupo).
- Tamaño razonable para el formulario: ~300–400px de ancho por thumbnail.
- No bloquea el layout ni rompe el form en mobile.

---

Nova
