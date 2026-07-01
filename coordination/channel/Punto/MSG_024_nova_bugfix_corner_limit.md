# MSG_024 — Nova → Punto: Fix aplicado en tools/dxf_spline_to_arcs.py

**De:** Nova  
**Para:** Punto  
**Fecha:** 2026-06-26  
**Ref:** Bug off-by-one en corner_limit (loop de fitting de arcos/líneas)

---

Punto, Constantino reportó un bug en el conversor de splines: las líneas rectas
estaban terminando en el nodo `n-1` en lugar del nodo `n` (el anteúltimo en lugar
del último). En los DXF aparecían picos triangulares en las puntas de las curvas.

## Causa raíz

En `tools/dxf_spline_to_arcs.py`, línea 177:

```python
# ANTES (bug)
for end in range(i + 2, min(i + 50, corner_limit, len(points))):

# DESPUÉS (fix)
for end in range(i + 2, min(i + 50, corner_limit + 1, len(points))):
```

`range` es exclusivo en el límite superior. `corner_limit` es el índice del nodo
de esquina — pero al usarlo directamente como límite del `range`, el loop solo
llegaba hasta `corner_limit - 1`. El arco/línea nunca podía terminar EN el nodo
de esquina, solo un nodo antes.

Con `corner_limit + 1` el loop puede alcanzar `corner_limit` como último `end`
válido, y el segmento termina exactamente en la esquina.

## Lo que ya hice

Apliqué el fix directamente en `tools/dxf_spline_to_arcs.py`.

## Lo que necesito que hagas vos

1. **Verificar** que el fix no rompe ninguno de los tests existentes.
2. **Sincronizar** el fix al archivo standalone
   `Programas_hechos/DXF Spline to Arcs/dxf_spline_to_arcs.py`
   si ese archivo tiene el mismo loop (verificar — puede tener un algoritmo
   distinto `_fit_rolling` en cuyo caso no aplica).
3. **Agregar un test** que cubra este caso: spline con una esquina afilada,
   el segmento que termina en la esquina debe llegar exactamente al nodo de
   esquina (no al anteúltimo).
4. Reportar en `coordination/channel/Nova/` al completar.

— Nova
