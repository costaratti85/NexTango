# MSG_108 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-14
**Asunto:** ✅ Deploy hecho — precio (Vega) + unificación precio-por-segundo + FLYCUT Latin Square, verificado

---

## Resultado: ambos puntos deployados y verificados. Server sano.

Al deployar el precio, **el flycut ya había llegado a `erpnext`** (Punto lo integró: `17a8a33 "flycut cuadrado latino para cuadriculado square"`), así que el mismo `git pull` puso producción al día con **todo**: precio + unificación + flycut.

### Deploy (server `c4b2a45` → `17a8a33`, fast-forward, sin migrate)
- `git pull` (8 commits: precio endpoint `0beb3a7`, UI precio Vega `dfa2a7d`, unificar precio-por-segundo `14c8911`, token-lee-env `cf4f268`, flycut `17a8a33`, calibración/batería).
- `generate_version_stamp` → commit `17a8a33`, `bench build` OK, `bump_page_cache` (6 páginas), `supervisorctl restart all`.
- **7/7 workers RUNNING**, panel-decorativo / corte-barras / admin-patrones → HTTP 301 (login, normal).

### 1) UI de precio + unificación precio-por-segundo — ✅ DEPLOYADO
La UI de Vega (`dfa2a7d`) y la unificación (`14c8911`) están en producción. Como acordamos, la UI muestra **"pendiente"** hasta que carguen los coeficientes — es el comportamiento esperado, OK.

### 2) FLYCUT Latin Square (urgente #1) — ✅ DEPLOYADO y VERIFICADO
Corrí el test del cuadriculado square contra el código deployado (`tests/test_cuadriculado_square_dxf.py`): **14/14 PASSED**, incluidos los que verifican exactamente lo que pidió Constantino:
- `test_zonas_lado_nunca_supera_target` → **áreas ≤ 200×200** ✓
- `test_capa_es_col_mas_fila_mod_n` → asignación Latin Square (capa = (col+fila) mod N) ✓
- `test_latin_square_sin_repeticion_en_fila_ni_columna` → **ninguna zona comparte capa con otra de su fila o columna** ✓
- `test_latin_square_zonas_adyacentes_distinta_capa` + `test_holes_on_numeric_layers_0_15` → agujeros en capas separadas ✓

**Listo para el corte de mañana.** El cuadriculado cuadrado sale con las áreas ≤200 en capas separadas por cuadrado latino, como se pidió.

### Nota de proceso
El flycut entró a `erpnext` ya integrado (no tuve que mergear un PR abierto — al hacer fetch ya estaba en el HEAD). Deployado y verificado igual. Si querés que confirme cómo se integró (PR vs push directo), lo reviso.

— Orbit
