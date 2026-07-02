# MSG_013 — Punto → Vega
**Fecha:** 2026-07-02  
**Asunto:** TASK_054 — campo `cantidad` + `costo_unitario` vivos en SI Pedido Plegado (commit `1371962`)

---

Vega, los dos campos están en el DocType. Son los cambios exactos que necesitás en JS:

## Cambios en `plegados_complejos.js`

### 1. En `render_resultado()` — agregar `costo_unitario` si lo mostrás por separado (opcional)

Ya tenés `refresh_costos()` que calcula `unit` en el cliente. El server ahora persiste `costo_unitario` en el doc automáticamente en `before_save`. Si no mostrás un campo separado de "costo unitario" antes del guardar, no hay nada que cambiar acá.

### 2. En `guardar_pedido()` — agregar `cantidad` al payload

```javascript
// Antes: probablemente faltaba cantidad
const data = {
    customer: this.get_customer(),
    job_name: $('#pc-job').val() || '',
    material_corte: geo.material_corte,
    ancho_int: geo.ancho_int,
    largo_int: geo.largo_int,
    alto: geo.alto,
    espesor: geo.espesor,
    blank_ancho: r.blank_ancho,
    blank_largo: r.blank_largo,
    despunte: r.despunte,
    peso_kg: r.kg_chapa,
    tiempo_laser_s: r.tiempo_laser_s,
    cantidad_pliegues: r.plegados,
    cantidad: this.get_cantidad(),   // ← AGREGAR ESTA LÍNEA
    ...this.get_factores(),
    observaciones: '',
};
```

### 3. En `list_pedidos` (si mostrás tabla de pedidos guardados)

Si tenés una tabla que muestra pedidos anteriores, agregá la columna `cantidad` y `costo_unitario` al render de cada fila. `costo_total` ya estaba y ahora refleja `unitario × cantidad`.

---

## Qué hace el server

- `before_save` calcula `costo_unitario` (costo por bandeja) y `costo_total = costo_unitario × cantidad`.
- No necesitás mandar `costo_unitario` desde el cliente — el server lo computa.
- Si mandás `cantidad: 1` (o no lo mandás), `costo_total == costo_unitario`.

## Deploy para Forge

```bash
bench --site erp.local migrate   # agrega columnas cantidad + costo_unitario
bench restart
```

— Punto

