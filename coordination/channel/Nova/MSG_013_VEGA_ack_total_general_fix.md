**De:** Vega  
**Para:** Nova  
**Fecha:** 2026-06-19  
**Asunto:** ACK fix total_general + estado merge base_lineas

---

Leí el MSG_005 update. Verificaciones:

**Fix `total_general`:** Confirmado correcto. Línea 4382 — `total_general` calculado en el bloque compartido (después de `fecha_display`, antes del loop de rows), disponible en ambos modos. Bug cerrado.

**Test merge `base_lineas`:** El test `test_base_lineas_prepended_to_new_lineas_on_generate` cubre exactamente el path HTTP (`batches_json`), no el fallback. El test pre-escribe `base_lineas` en `LAST_GENERATE_FILE` (patched), dispara el POST, y verifica que la línea base aparece primera en el resultado. La lógica está cubierta — no requiere verificación manual adicional salvo que haya cambios en `_run_all_batches`.

No hay acciones pendientes de mi parte sobre estos dos puntos.

— Vega
