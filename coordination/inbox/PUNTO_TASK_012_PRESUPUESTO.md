# PUNTO_TASK_012 — Generación de presupuesto

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-17  
**Prioridad:** Alta

---

## Contexto

Ya tenemos todo lo necesario para calcular el costo de un pedido:

- `consumed_resources` en la respuesta del `POST /generate` — `material_kg`, `machine_seconds`, `pierce_count` por tipo de panel
- `daily_prices.json` — `precio_segundo_maquina`, `precio_kg_acero_negro`, `precio_kg_galvanizado`, `precio_kg_inoxidable`

Esta tarea cierra la primera rebanada del sistema: **pedido → presupuesto**.

---

## Qué construir

### 1. Cálculo de costo en el backend

En `_run_all_batches()` (o donde se construye la respuesta JSON del generate), después de armar `consumed_resources`, calcular el costo:

```python
def calculate_cost(consumed_resources, material_name, daily_prices):
    """
    consumed_resources: {"material_kg": X, "machine_seconds": Y, "pierce_count": Z}
    material_name: "Galvanizado" | "Acero negro" | "Inoxidable 304"
    daily_prices: dict leído de daily_prices.json
    Retorna: {"costo_material": X, "costo_maquina": Y, "costo_total": Z}
    """
    precio_segundo = float(daily_prices.get("precio_segundo_maquina", 0))
    
    if "galvanizado" in material_name.lower():
        precio_kg = float(daily_prices.get("precio_kg_galvanizado", 0))
    elif "inoxidable" in material_name.lower():
        precio_kg = float(daily_prices.get("precio_kg_inoxidable", 0))
    else:
        precio_kg = float(daily_prices.get("precio_kg_acero_negro", 0))
    
    costo_material = consumed_resources.get("material_kg", 0) * precio_kg
    costo_maquina = consumed_resources.get("machine_seconds", 0) * precio_segundo
    costo_total = costo_material + costo_maquina
    
    return {
        "costo_material": round(costo_material, 2),
        "costo_maquina": round(costo_maquina, 2),
        "costo_total": round(costo_total, 2),
    }
```

Si `daily_prices.json` no existe o tiene precios en cero, incluir igualmente el bloque `cost` en la respuesta (con valores 0.00) y agregar un flag `"prices_missing": true`.

Agregar el resultado como `cost` en cada batch de la respuesta JSON.

### 2. Página `/presupuesto`

Nueva página accesible desde el resultado del generate. Genera un presupuesto imprimible en HTML.

**Cómo llegar:** después de hacer "GENERAR DXF", aparece un botón "Ver presupuesto" que abre `/presupuesto` (puede pasar el job_id o session como parámetro, o simplemente mostrar el último pedido generado guardado en sesión/archivo temporal).

**Contenido del presupuesto:**

```
╔══════════════════════════════════════════════════════════╗
║              NEXTANGO — PRESUPUESTO                      ║
║  Fecha: 17/06/2026          N°: [autoincremental]        ║
╠══════════════════════════════════════════════════════════╣
║  Panel              Mat/Esp   Cant  Costo u.  Subtotal   ║
║  ─────────────────  ────────  ────  ────────  ─────────  ║
║  Subte4             Galv/20   10    $ 1.23    $ 12.30    ║
║  ...                                                     ║
╠══════════════════════════════════════════════════════════╣
║                                    TOTAL: $ XX.XX        ║
╚══════════════════════════════════════════════════════════╝

  Recursos totales:
    Material consumido: X.X kg
    Tiempo de máquina:  X min X s
    Perforaciones:      XXX

  Precios aplicados:
    Acero negro: $ X/kg   Galvanizado: $ X/kg
    Inoxidable:  $ X/kg   Máquina: $ X/s
```

Formato: HTML imprimible (`@media print` con CSS que oculte botones y navegación). El usuario puede imprimir desde el browser para obtener PDF.

**Número de presupuesto:** autoincremental, guardado en `Programas_hechos/Panel Decorativo/presupuesto_counter.json` (`{"last": N}`).

### 3. Guardar el presupuesto

Al generar el presupuesto (cuando se abre `/presupuesto`), guardarlo como JSON en:
`Programas_hechos/Panel Decorativo/presupuestos/PRES_NNNN.json`

Estructura:
```json
{
  "numero": 1,
  "fecha": "2026-06-17",
  "lineas": [
    {
      "patron": "Subte4",
      "material": "Galvanizado",
      "espesor_mm": 1.006,
      "cantidad": 10,
      "consumed_resources": {...},
      "cost": {"costo_material": ..., "costo_maquina": ..., "costo_total": ...}
    }
  ],
  "total": 12.30,
  "precios_aplicados": {...}
}
```

### 4. Link de navegación

Agregar "Presupuestos" al topbar del admin, junto a "Precios diarios" y "Tabla de materiales".

---

## Criterio de aceptación

1. La respuesta del `POST /generate` incluye `cost` por batch con `costo_material`, `costo_maquina`, `costo_total`
2. Si `daily_prices.json` no existe o precios = 0, `cost` aparece con valores 0 y `prices_missing: true`
3. Después de generar, aparece botón "Ver presupuesto" que abre `/presupuesto`
4. `/presupuesto` muestra tabla de líneas, total, recursos totales, precios aplicados
5. La página es imprimible (CSS `@media print` oculta nav y botones)
6. Cada presupuesto queda guardado como JSON en `presupuestos/PRES_NNNN.json`
7. Tests existentes siguen pasando

## Reportar en

`coordination/reports/PUNTO_TASK_012_REPORT.md`
