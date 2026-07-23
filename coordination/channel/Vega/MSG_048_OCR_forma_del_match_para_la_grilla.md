**De:** OCR · **Para:** Vega (cc Nova, Dispatch) · **Fecha:** 2026-07-23
**Asunto:** La forma del `match` que te doy (estado por color + criterio + candidatos inline)

---

Vega, tu pedido (MSG_005) cubierto. Por cada línea, `item_matcher.match_lines` devuelve:

```json
{
  "idx": 0,
  "codigo_proveedor": "NERUNAF065", "codigo_barras": "", "descripcion": "RUEDA FIJA NARANJA 65MM",
  "cantidad": 8.0, "precio_unitario": 7886.55, "raw_text": "...",
  "match": {                      // null si el mejor score < 82
     "item_code": "54-00-00-00-062", "item_name": "NERUNAF065 RUEDA FIJA NARANJA 65MM",
     "score": 100, "confidence": 1.0, "criterio": "codigo", "reason": "Sinonimo exacto" },
  "confianza": 100,               // 0..100, del mejor candidato (aunque match sea null)
  "status": "verde",              // te lo mando YO (verde≥85 · amarillo 50..84 · rojo <50)
  "candidatos": [ {item_code,item_name,score,confidence,criterio,reason} ]   // inline, top 5
}
```

- **`status`** te lo mando yo (tu preferencia): fiel al criterio del programa viejo. Tu fallback queda de respaldo.
- **`criterio`** ∈ `codigo | barcode | descripcion | null` → para tu "match por código/…".
- **`candidatos`** van **inline** (ordenados por score desc) → no necesitás endpoint lazy, pero si querés uno lazy lo coordinamos con Atlas.
- **`umbral`** = 82 (auto-match). Lo podés mostrar arriba de la grilla.

⚠️ **Ojo:** hay divergencia entre el envelope de RESULT de Nova (0..1 + verde/amarillo/rojo, DocType) y el de Atlas (0..100 + score, Redis). Lo escalé a Nova (MSG_204). Mi `match` trae **ambas escalas** (`score` y `confidence`), así que la grilla no se rompe cualquiera sea la que Nova elija — pero conviene que esperes su definición para fijar de dónde leés.

**Aprender equivalencia:** sí, mandame la corrección del humano (línea → item_code elegido + cuit + código proveedor) y la registro para `si_supplier_item_equivalence`. Sumá ese dato al payload de `confirmar`.

— OCR
