**De:** Gemu  
**Para:** Nova  
**Fecha:** 2026-07-05  
**Asunto:** GEMU_PAGINA_CORTE_BARRAS + GEMU_MODELO_COMPRA_MIXTO — entregado

---

Ambas tareas completadas. Detallo lo implementado.

## 1. Modelo de compra mixto — `calculate_purchase_plan()` (main a548132)

Extendí `cutting/nest_1d.py` con una nueva función pública:

```python
calculate_purchase_plan(
    bar_len, cuts, price_per_bar, price_per_meter, kerf_mm=2.0
) -> PurchasePlanResult
```

**Algoritmo:** el bin-packing corre sobre todas las piezas como siempre. Luego, para cada bin resultante, se compara:
- Costo de comprar la barra entera: `price_per_bar`
- Costo de comprar las piezas del bin como tramos sueltos: `sum(piezas) / 1000 × price_per_meter`

El bin más barato gana. Los bins "tramos" no se re-paquetan — sus piezas se compran individualmente.

**Verificación del caso de Constantino:**  
7 × 950mm → bin1 = [950, 950, 950, 950, 950, 950] (5700mm, cabe con kerf), bin2 = [950].  
Con price_bar=100, price_metro=20:  
- bin1: tramo = 5.7m × 20 = 114 > 100 → barra entera ✓  
- bin2: tramo = 0.95m × 20 = 19 < 100 → tramo suelto ✓  
- Total: 1 barra + 0.95m, costo = 100 + 19 = 119 ✓

**Tests:** 7 nuevos, 21 totales, 21/21 passing.

## 2. Página Frappe `corte-barras` (erpnext b1b8722)

Archivos creados:
- `sistema_industrial/page/corte_barras/` — HTML/CSS/JS/JSON
- `api/corte_barras.py` — endpoint `calcular()` whitelisted
- `cutting/nest_1d.py` — copiado desde main al worktree erpnext

**UI:**
- Link a Customer (opcional)
- Link a Item filtrado por `01-%` OR `02-%` (usa `or_filters: true` en `get_query`)
- Largo de barra (default 6000, editable), Kerf (default 2), Precio/barra, Precio/metro
- Tabla de piezas editable con filas + / -
- Botón "Calcular" → llama a `sistema_industrial.api.corte_barras.calcular`
- Resultados: KPIs (barras enteras, metros tramo, costo total, eficiencia), desglose de costo, tabla de patrones de corte, chips de tramos sueltos

**Workspace:** shortcut "Corte de Barras" agregado en la sección Herramientas (posición 4, después de Perfiles Plegados).

## 3. Deploy necesario (para Orbit/Forge)

```bash
cd /home/costa/Nextango-erpnext
git pull
bench migrate          # el Page doc es nuevo → lo crea
bench build --app sistema_industrial
# bump_page_cache (si existe el helper de Vega en deploy.py)
supervisorctl restart all
```

La página no tiene DocTypes nuevos — solo el Page doc (creado por bench migrate).

## Preguntas abiertas para Constantino

1. **Precios hardcodeados vs. configurables:** hoy los precios se ingresan manualmente en cada cálculo. ¿Querés que vivan en SI Precios Globales (hay que agregar 2 campos nuevos: `precio_barra_perfiles` y `precio_metro_perfiles`) para que se pre-carguen automáticamente? Si sí, coordino con Punto antes de tocar ese doctype.

2. **Filtro de ítems:** la página filtra `item_code LIKE '01-%' OR '02-%'`. Si hay otros prefijos de perfiles/caños que también deben aparecer, avisame.

3. **El campo `item_code` de Vega:** la página tiene un selector de Item pero **no lo usa para nada más** (no consulta precio, no lo guarda en ningún lado). Depende de Constantino si quiere que se muestre en los resultados como "referencia de la cotización" o si es puramente decorativo por ahora.

— Gemu
