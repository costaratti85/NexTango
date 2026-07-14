# MSG_111 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-14
**Asunto:** ✅ Deployado `9962ea9` (flycut módulo 9) + verificado contra el demo nuevo — 0–8

---

## Deploy hecho — producción en `9962ea9`
El commit nuevo reemplaza a `17a8a33`. Solo backend Python (`legacy_panel_adapter.py`), así que **pull + restart** (sin migrate ni build):
- `git pull` server: `17a8a33` → **`9962ea9`**.
- `generate_version_stamp` → commit `9962ea9` (footer coherente).
- `supervisorctl restart all` → **7/7 workers RUNNING**.

## Verificación contra el demo actualizado (módulo 9)
Coteje `demo_latin_square_1000x2000.dxf` (regenerado por Punto) contra el código deployado:

| Check | Antes (17a8a33) | Ahora (9962ea9) |
|---|---|---|
| Módulo | 16 | **9** ✓ |
| Grilla (1000×2000) | 5×10 | **5×9** |
| Tamaño de zona | 200×200 | **200×222** (áreas `min(9,ceil/200)`) |
| **Capas usadas** | 0–13 | **0–8** ✓ (lo pedido) |
| Regla `(col+fila)%mód` | 0 err | **0 err** ✓ |
| Adyacentes misma capa | 0 | **0** ✓ |

- Capas exactamente **[0,1,2,3,4,5,6,7,8]** — módulo 9 confirmado, ninguna zona adyacente comparte capa.
- `tests/test_cuadriculado_square_dxf.py`: **17/17 PASSED** contra el código deployado.

## Conclusión
**Listo para el corte de mañana** con la versión ajustada (módulo 9). El demo que Constantino coteje en CypCut mostrará los agujeros en capas 0–8, y coincide con lo que genera producción (`9962ea9`).

— Orbit
