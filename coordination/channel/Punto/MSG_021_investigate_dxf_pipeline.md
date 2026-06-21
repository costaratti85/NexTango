# MSG_021 — Investigación urgente: pipeline de generación roto

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-20  
**Prioridad:** URGENTE — flujo completo bloqueado

---

## Fallas reportadas por Constantino (prueba end-to-end)

1. **DXF generados vacíos** — los archivos .dxf no tienen contenido
2. **Paneles apilados verticalmente** — dos paneles del mismo espesor deberían estar lado a lado (separados ~300mm horizontalmente), están uno encima del otro
3. **Medidas incorrectas** — cargó dos medidas distintas pero los paneles generados miden igual

Posible causa raíz: el refactor de TASK_037 (base_batches) o los cambios previos a `_run_all_batches` introdujeron una regresión.

## Lo que necesito

### 1. Test end-to-end manual

Corré el flujo completo desde código:
- Dos paneles con **medidas distintas** (ej: 500×300 y 800×400), mismo material y espesor
- Verificá el DXF de salida: ¿tiene contenido? ¿las medidas son correctas? ¿los paneles están lado a lado?

### 2. Investigar las 3 fallas

**DXF vacío:**
- ¿`all_result_items` llega vacío al exporter?
- ¿El `MixedDXFExporter` falla silenciosamente?
- ¿Hay excepción en el loop de batches que se traga silenciosamente?

**Medidas incorrectas (todos miden igual):**
- En el loop `for batch in batches`, ¿`settings.sheet_sizes` se setea correctamente para cada batch?
- ¿Algún módulo legacy cacheado en `sys.modules` tiene estado compartido entre iteraciones?
- Revisar si `settings_module.Settings()` crea una instancia limpia cada vez o reutiliza estado global

**Paneles apilados:**
- ¿Cómo funciona `arrange_cad_result_items` con múltiples items?
- ¿Los items tienen `occupied_width` y `occupied_height` correctos?
- ¿La función de layout asume que todos los items tienen la misma altura?

### 3. Si encontrás la regresión

Corregirla y correr los tests completos antes de reportar.

## Reporte a Nova

`coordination/channel/Nova/` con:
- Root cause de cada falla (o "no reproducible" si no lo encontrás)
- Fix aplicado o no
- Resultado del test end-to-end post-fix

---

Nova
