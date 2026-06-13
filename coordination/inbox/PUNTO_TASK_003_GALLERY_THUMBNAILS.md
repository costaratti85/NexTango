# Tarea para Punto — Thumbnails para galería de patrones

**De:** Nova  
**Fecha:** 2026-06-12  
**Prioridad:** Media — desbloquea a Vega para usar imágenes reales en el mockup  
**Dependencia:** Esta tarea no bloquea a Vega (puede mockear con placeholders), pero sí desbloquea la implementación final

---

## Contexto

El módulo de Paneles Decorativos va a tener una galería visual donde el vendedor elige el patrón con los ojos. Cada patrón necesita una imagen de preview (thumbnail). Vega está diseñando el UX de esa galería.

**Los thumbnails son imágenes estáticas pre-generadas** — no dinámica, no en tiempo real. Se generan una vez y se guardan en disco. El servidor las sirve como archivos estáticos.

---

## Lo que Punto tiene que hacer

### 1. Generar thumbnails PNG para cada patrón de la librería

Escribir un script `tools/generate_pattern_thumbnails.py` que:
- Itera sobre todos los patrones en `Programas_hechos/Panel Decorativo/pattern_library.json`
- Para cada patrón DXF: usa el motor para generar la geometría sobre una chapa de ejemplo (ej. 200x200mm, margen 10mm), y renderiza esa geometría como PNG usando `matplotlib` o `ezdxf.addons.drawing`
- Para Tresbolillo: genera un preview con parámetros fijos de ejemplo (diámetro 20mm, distancia 60mm, chapa 200x200mm)
- Guarda los thumbnails en `apps/sistema_industrial/sistema_industrial/static/pattern_thumbnails/` con nombre `{nombre_patron}.png`
- Tamaño objetivo: 300×300px, fondo blanco, líneas en color oscuro

### 2. Endpoint para servir los thumbnails

En `panel_sales_local_app.py`, agregar soporte para `GET /static/pattern_thumbnails/{nombre}.png` — sirve el archivo PNG desde disco.

### 3. API para listar patrones con URL de thumbnail

El endpoint existente `GET /api/patterns` debe incluir en cada entrada la URL del thumbnail:
```json
{
  "name": "Rombo mediano",
  "type": "dxf",
  "file_path": "...",
  "step_x": 84,
  "step_y": 84,
  "thumbnail_url": "/static/pattern_thumbnails/Rombo mediano.png"
}
```

Si no existe thumbnail para un patrón, devolver `"thumbnail_url": null`.

---

## Consideraciones técnicas

- El motor legacy corre con `_legacy_import_context` (CWD = directorio del motor). El script de thumbnails debe usar el mismo mecanismo o invocar directamente `LegacyPanelAdapter`.
- `ezdxf` ya es una dependencia del proyecto (verifica en `pyproject.toml`). Para renderizar DXF a imagen se puede usar `ezdxf.addons.drawing` + `matplotlib`. Si no está disponible, usar `matplotlib` directamente dibujando las polilíneas del resultado del motor.
- El script debe correr sin errores aunque la librería esté vacía (genera solo el thumbnail del Tresbolillo).

---

## Verificación

1. `python tools/generate_pattern_thumbnails.py` corre sin errores
2. Existe al menos `apps/sistema_industrial/sistema_industrial/static/pattern_thumbnails/Tresbolillo.png`
3. `GET /static/pattern_thumbnails/Tresbolillo.png` desde el servidor devuelve una imagen válida
4. `GET /api/patterns` incluye `thumbnail_url` en cada entrada
5. Los tests existentes siguen pasando

---

## Nota sobre la arquitectura futura

Punto debe saber que la conexión futura entre Paneles Decorativos y los Presets de Plegados requiere el concepto de **cara principal**: cada preset de plegado define un rectángulo que es la cara que recibe el patrón. Cuando esa feature llegue, Punto va a recibir el rectángulo de la cara principal como input en lugar del ancho/alto directo. El motor no cambia — solo cambia de dónde vienen las dimensiones.

---

## Reportar en

`coordination/reports/PUNTO_GALLERY_THUMBNAILS_REPORT.md`
