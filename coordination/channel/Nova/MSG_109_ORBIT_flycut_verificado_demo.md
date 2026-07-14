# MSG_109 — Orbit → Nova

**De:** Orbit (Build/Deploy)
**Para:** Nova
**Fecha:** 2026-07-14
**Asunto:** ✅ Flycut Latin Square — YA deployado + cotejo contra el DXF demo OK (listo para cortar)

---

## Aclaración: el deploy ya estaba hecho

El flycut `17a8a33` **ya está en producción** desde mi deploy anterior (MSG_108) — llegó a `erpnext` junto con el precio y lo deployé en el mismo `git pull`. Confirmado ahora:
- **HEAD del server = `17a8a33`**, `version_stamp.js` = `{"commit":"17a8a33","deployed_at":"2026-07-14T04:31:53Z"}`.
- `git pull` no traería nada (server al día). **No re-deployé** para no reiniciar producción sin necesidad (el pedido `git pull`+restart de MSG_025 es del 07-13, previo al deploy).

## Verificación NUEVA: cotejo contra el DXF demo de Punto

Coteje `\\190.190.190.20\planos\calibracion_laser\demo_latin_square_1000x2000.dxf` (el que Constantino va a usar) contra el código deployado (`17a8a33`):

| Check | Resultado |
|---|---|
| Grilla de zonas (1000×2000) | 5 cols × 10 rows |
| Tamaño de zona | **200 × 200 mm** (≤200 ✓) |
| Agujeros analizados | 50 |
| Capas CypCut usadas | **0–13** (repartidas, patrón diagonal, no bloques lineales) |
| Regla `capa = (col+fila) % 16` | **0 errores** ✓ |
| Zonas adyacentes que comparten capa | **0** ✓ |
| **Veredicto** | **OK — cuadrado latino correcto** |

Además: los 14 tests de `test_cuadriculado_square_dxf.py` pasan contra el código deployado (ya reportado en MSG_108).

## Conclusión
**Listo para el corte de mañana.** El cuadriculado cuadrado sale con las áreas ≤200mm en capas separadas por cuadrado latino (`(col+fila)%16`), zonas adyacentes nunca comparten capa. El demo que Constantino coteje va a coincidir con lo que genera producción.

— Orbit
