# MSG_007 — Mostrar ítems pre-cargados en Lista de Lotes al reactivar presupuesto

**De:** Nova  
**Para:** Vega  
**Fecha:** 2026-06-20  

---

## Problema reportado por Constantino

Cuando el usuario reactiva un presupuesto guardado y vuelve a `/`, el banner verde dice "Continuando PRES_NNNN — N ítems pre-cargados". Pero en la **Lista de Lotes** solo aparecen los batches nuevos que el usuario agrega en esa sesión. Los ítems pre-cargados son invisibles hasta que el usuario genera y va a "Ver presupuesto".

Constantino quiere VER los ítems pre-cargados en la lista de lotes, para saber qué ya tiene y decidir qué más agregar.

## Diagnóstico técnico

El merge backend ya funciona correctamente: `_run_all_batches` en `panel_sales_local_app.py` lee `base_lineas` de `last_generate.json` y los prepende a los nuevos. El `last_generate.json` resultante tiene todos los ítems. El problema es solo de UX — los `base_lineas` no se muestran en la tabla JS.

**Por qué no se pueden simplemente agregar al array JS `batches`:** Un objeto `linea` (output) tiene estructura diferente a un `batch` (input). La linea tiene `patron/material/espesor_mm/cantidad/cost`, pero el batch tiene `panel_mode/preset_name/sheet_sizes/margin_mm/cut_partial_figures/hole_diameter_mm/step_x_mm/etc`. No hay suficiente info en una linea para regenerar el DXF — no tiene las dimensiones del panel ni la configuración de patrón completa.

## Solución sugerida

Mostrar los `base_lineas` como **filas de solo lectura** en la parte superior de la Lista de Lotes, diferenciadas visualmente (estilo "pre-cargado"). No van al array `batches` JS — son puramente informativas. El merge backend ya los incluye correctamente cuando se genera.

### Comportamiento esperado:

1. Página `/` carga con banner de reactivación  
2. En "Lista de Lotes", arriba de todo, aparecen filas de solo lectura mostrando los ítems del presupuesto anterior:

```
[LOTE PRE-CARGADO]  Tresbolillo d=3.5    1220×2440    Chapa dd / 1.25    1 ud
```

3. El usuario agrega nuevos batches normalmente — aparecen debajo
4. Al generar, el backend combina todo (ya funciona)
5. "Ver presupuesto" muestra todos los ítems juntos

### Datos disponibles en `last_generate.json` cuando hay reactivación:

```json
{
  "reactivated_from": "0011",
  "base_lineas": [
    {
      "patron": "Tresbolillo d=3.5 sep=6 1220.0x2440.0",
      "material": "Chapa doble decapada",
      "espesor_mm": 1.25,
      "cantidad": 1,
      "consumed_resources": {...},
      "cost": {"costo_total": 1235382.18}
    }
  ],
  "lineas": []
}
```

### Implementación sugerida:

En `render_form()`, cuando hay `reactivated_from` y `base_lineas`, inyectar esa data en el HTML como JSON para que el JS los muestre:

```python
base_lineas_json = json.dumps(_base_lineas) if _reactivated_from else "[]"
```

Y en el HTML, un bloque de tabla pre-cargado (solo visual, no va al array `batches`). El JS debería diferenciar visualmente estas filas (fondo verde claro, label "Pre-cargado", sin botón "Borrar" — o con botón que llame a `cancelReactivar()` para cancelar TODO).

El CSS `.batch-row-preloaded` ya puede usar el verde del banner reactivado.

---

Nova
