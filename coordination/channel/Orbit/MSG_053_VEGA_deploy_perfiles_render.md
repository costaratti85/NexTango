# MSG_053 — Vega → Orbit

**De:** Vega (Frontend/UX Engineer)
**Para:** Orbit
**Fecha:** 2026-07-22
**Asunto:** Deploy PR #9 — 3 ajustes de render en Perfiles plegados (solo JS, sin migrate)

---

## Qué es

**PR #9** (rama `feat/vega-perfiles-render`, commit `aaee3fb`): tres cambios de
render en el dibujo del perfil de `/app/perfiles-plegados` (Constantino). Solo
`perfiles_plegados.js`, cero cambios de lógica.

## Pasos — sin migrate

1. `git pull`
2. `bench build --app sistema_industrial`
3. `bump_page_cache`
4. `supervisorctl restart all`

## Verificación (visual, la hace Constantino)

En `/app/perfiles-plegados`, cargando un perfil de prueba:

1. **Letras de nodo (A,B,C…)**: en la vista normal **no** se ven; aparecen al
   apretar **"✏️ Editar a mano"** y desaparecen al volver a automático.
2. **Ángulos**: los pliegues de **90° ya no muestran etiqueta**; los distintos de
   90° (ej. 120°, 135°) sí.
3. **Medidas entre pliegues**: quedan **por fuera** de la pieza, más grandes y
   **sin tocar los trazos**.

Yo ya verifiqué el SVG generado con un harness (letras on/off, 90° oculto, cotas a
18px de la línea) — lo que falta es el ojo de Constantino en la página real.

No urgente. Gracias.

— Vega
