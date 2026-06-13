# PUNTO_TASK_004 — Deuda técnica: thumbnail renderer

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-13  
**Prioridad:** Baja — no bloquea nada, resolver cuando haya ciclo libre

---

## Tres items identificados en la verificación post-Nova

### 1. Límite de profundidad en el renderer recursivo

`_draw(geom)` en `generate_pattern_thumbnail` es recursivo sobre `Piece.entities`. Con geometría normal esto no es un problema, pero no hay límite documentado. Agregar un parámetro `depth=0` con corte en `depth > 10` y un `logger.warning` si se alcanza. Protección defensiva, no optimización.

### 2. Thread daemon para thumbnail

Los threads de generación de thumbnails son `daemon=True`. Si el servidor se detiene mientras un thumbnail está generándose, la generación se aborta silenciosamente. Aceptable para uso interno actual. Documentarlo con un comentario en el código (`# daemon: se aborta si el servidor para — aceptable para uso local`). Sin cambios de comportamiento.

### 3. Resolución de thumbnail fija

Los parámetros `figsize=(3, 3), dpi=100` están hardcodeados. Extraerlos como constantes al tope del módulo:

```python
THUMBNAIL_SIZE_INCHES = 3
THUMBNAIL_DPI = 100
```

Sin cambios de comportamiento. Solo facilita ajustarlos en el futuro si se necesita mayor resolución.

---

## Criterio de aceptación

- 42 tests siguen pasando después de los cambios
- No se modifica ningún comportamiento visible para el usuario
