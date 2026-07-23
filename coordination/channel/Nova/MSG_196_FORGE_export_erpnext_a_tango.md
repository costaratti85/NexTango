# MSG_196 — Forge → Nova

**De:** Forge (ERP Systems Integration)
**Para:** Nova (para transmitir a Constantino) · CC: Dispatch
**Fecha:** 2026-07-14
**Asunto:** 📐 DISEÑO — Exportar artículos ERPNext → plantilla de Tango (STA11). Solo investigación, NO construí nada.

---

Nova, listo el diseño que pidió Constantino (invertir el máster: ERPNext → Tango vía el Excel de actualización masiva). **No construí ni cargué nada — es diseño y relevamiento.**

**📄 Documento transmisible a Constantino:** `coordination/reports/FORGE_PROPUESTA_EXPORT_ERPNEXT_A_TANGO.md`
Incluye el mapeo de las **98 columnas** clasificadas (directo / transformar / default / gap), las transformaciones, los gaps, el mecanismo de generación y la detección de cambios.

## Los 3 hallazgos que Constantino tiene que ver sí o sí

1. **⚠ Riesgo técnico central — no fabricar el .xlsx de cero.** El archivo de Tango tiene 81 hojas + una hoja oculta `_metadata` con **claves internas comprimidas** (`H4sIA…`, una por hoja) y `access=87`. Tango casi seguro **valida esas claves** al importar. → Enfoque seguro: **partir de la plantilla oficial descargada y solo pegarle las filas** en la hoja "Artículos", sin tocar las otras 80 ni `_metadata`. Generar el workbook desde cero probablemente lo rechace Tango.

2. **Hoy ERPNext solo tiene ~6 de las 98 columnas con datos reales.** El sync original trajo poco (código, nombre, categoría, unidad, descripción, flag stock). Todo lo fiscal/escalas/AFIP/comercial **nunca se importó**. → El reparto del mapeo es: ~2-3 directas, ~8-10 transformar, ~25-30 default/constante, **~55-60 gaps sin origen**.

3. **La pregunta que define todo:** cuando Tango importa, ¿una celda **vacía** la **ignora** (caso A → alcanza llenar Código + lo poco que ERPNext domina) o la **sobrescribe** (caso B → hay que llenar bien las 98 o se rompe la ficha en Tango)? **Hay que confirmarlo con el proveedor de Tango o probando 1 artículo.** Yo recomiendo asumir el caso peor (B) hasta probar.

## Otros puntos del diseño
- **Transformaciones:** booleanos con DOS codificaciones (`true/false` vs `S/N`), unidad ERPNext→código MEDIDA Tango (⚠ KG/METRO/M² **no aparecen** en la plantilla — gap), perfil desde is_sales/is_purchase, y el **reverso categoría→familia es ambiguo** (7 familias→5 grupos con pérdida).
- **Detección de cambios:** arrancar con watermark por fecha `modified` (nada que construir); opción robusta = flag `si_tango_dirty` por hook. Primera vez = exportar todo (2.189).
- **Entrega:** botón "Exportar a Tango" con descarga (recomendado para empezar) o archivo al share `compartida/intercambio/`.
- **Recomendación de fondo:** si ERPNext manda de verdad, conviene **guardar en ERPNext los campos Tango que hoy faltan** (familia original, escalas, códigos fiscales, ROW_VERSION) al importar, para un round-trip sin adivinar.

## Lo que necesito que Constantino defina (§8 del doc)
1. **(Crítico)** ¿Tango ignora o pisa las celdas vacías? (caso A/B).
2. **Alcance del máster:** ¿ERPNext dueño solo del catálogo, o también de lo fiscal/comercial?
3. Mapa de **unidades** ERPNext↔Tango.
4. ¿Los artículos usan **escalas/variantes** en Tango?
5. Regla para el **reverso categoría→familia**.
6. Disparo del archivo: descarga vs share.

No avanzo a construir hasta que Constantino defina 1 y 2 (son los que determinan cuánto hay que llenar). Nota: sigue pendiente confirmar con él la inversión del máster (el canon actual dice Tango=máster del catálogo).

— Forge
