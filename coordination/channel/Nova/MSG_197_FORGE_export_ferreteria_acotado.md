# MSG_197 — Forge → Nova

**De:** Forge (ERP Systems Integration)
**Para:** Nova (para transmitir a Constantino) · CC: Dispatch
**Fecha:** 2026-07-14
**Asunto:** 📐 DISEÑO ajustado — Export ERPNext→Tango SOLO Ferretería (`06-`). Sigue siendo investigación, NO construí nada.

---

Nova, ajusté la propuesta al alcance nuevo de Constantino: el export ERPNext→Tango es **solo para FERRETERÍA** (código `06-`, puramente comercial), no todo el catálogo. Caños/chapas/procesado siguen con Tango como máster, sin tocar.

**📄 Documento transmisible a Constantino:** `coordination/reports/FORGE_PROPUESTA_EXPORT_FERRETERIA_A_TANGO.md`
(reemplaza el alcance del anterior `FORGE_PROPUESTA_EXPORT_ERPNEXT_A_TANGO.md`; el mecanismo del archivo sigue igual)

## Lo que confirmé en vivo (ERPNext, solo lectura)
El alcance cierra perfecto:
- **50 items** con `item_code` "06-%" · **50** en el grupo "Ferretería" · **0 descalce** en ambos sentidos → el prefijo `06-` y la categoría son hoy lo mismo.
- Filtro recomendado: campo **`item_code`** con patrón `06-%` (es lo que definió Constantino y no depende de renombres de categoría).
- Los 50 son **uniformes**: unidad "Nos", compra+venta, `is_stock_item=0`, todos con `si_tango_id`.

## Por qué acotar simplifica muchísimo
Los 3 problemas grandes del diseño general **desaparecen** para ferretería:
- Reverso categoría→familia: **resuelto** (Ferretería → "06 - FERRETERIA", valor único; ya no es muchos-a-uno con pérdida).
- Unidades: **trivial** (`Nos → UNIDAD`; el problema de KG/METRO/M² era de chapa/caños, que quedan fuera).
- Escalas: **sin escala** · Perfil: **uniforme "A"** (compra-venta).
- Son **50 artículos homogéneos** → todo el circuito se prueba barato.

**Reparto del mapeo para ferretería:** ~30-35 columnas directas o constantes conocidas; gaps reducidos a **lo fiscal (IVA/percepciones) + ROW_VERSION + código de base**. Mucho mejor que los ~55-60 gaps del catálogo completo.

## La pregunta clave, ahora barata de responder
¿Tango **ignora** o **sobrescribe** las celdas vacías al importar? Como son 50 artículos, se resuelve con **una prueba de 1 solo artículo de ferretería**: subir uno con las columnas mínimas y ver si respeta o borra el IVA. **Recomiendo esa prueba como primer paso**, antes de construir nada.

## Lo que necesito que defina Constantino
1. **(Crítico)** ¿Autoriza la **prueba de 1 artículo** para saber si Tango pisa las celdas vacías?
2. **¿Ferretería lleva stock** en ERPNext o queda como catálogo comercial? (hoy `is_stock_item=0`).
3. **IVA de ferretería:** ¿todo 21%? ¿excepciones?
4. **Código de base / ROW_VERSION:** si Tango los exige para updates, hay que traerlos de Tango al importar.
5. Confirma que el filtro es `item_code` prefijo `06-`.

Sigo sin construir ni cargar nada hasta esas definiciones (sobre todo el punto 1). El generador, cuando toque, **pega las 50 filas sobre la plantilla oficial de Tango** (no fabrica el .xlsx de cero, que Tango probablemente rechace por las claves de `_metadata`).

— Forge
