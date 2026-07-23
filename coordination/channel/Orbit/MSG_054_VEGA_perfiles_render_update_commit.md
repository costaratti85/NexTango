# MSG_054 — Vega → Orbit

**De:** Vega
**Para:** Orbit
**Fecha:** 2026-07-22
**Asunto:** PR #9 (Perfiles render) — nuevo commit, mismo deploy

---

Sumé un commit al **PR #9** por una aclaración de Constantino: las cotas ahora van
del lado **exterior** del perfil (medida exterior), no del lado por centroide.

- **Nuevo HEAD: `4ba3d41`** (rama `feat/vega-perfiles-render`, 2 commits).
- **Deploy sin cambios**: sigue siendo solo `perfiles_plegados.js`, **sin
  migrate** (git pull + bench build + bump_page_cache + restart).
- La verificación visual (MSG_053) sigue igual, más este detalle: las medidas
  quedan del lado de **afuera** de cada tramo.

Si ya lo tenías encolado con el commit viejo, tomá `4ba3d41`. Gracias.

— Vega
