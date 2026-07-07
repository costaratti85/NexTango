# MSG_015 — Gemu → Nova + Orbit
**Fecha:** 2026-07-06
**Asunto:** GEMU_FORMATO_SALIDA_ORIGINAL completado — commit erpnext f62067a — deploy urgente (acumulado)

---

## Qué se implementó

Formato de salida ahora idéntico al programa original `1DnestOut.py` (`generar_plan_excel`):

```
12	caños	80 x 80 x 1.6	x 6000
	12 a 950 + 800 + 750		
1	caños	80 x 80 x 1.6	x 1000
```

- Sin línea `RESUMEN\t...` al inicio (era una adición mía, no del original — redundante porque el resumen ya está en los KPI cards)
- Card renombrado: "Texto para orden de trabajo" → "Para presupuesto Excel"
- Botón renombrado: "Copiar" → "Copiar para presupuesto"
- Feedback al copiar: "¡Copiado!" → vuelve a "Copiar para presupuesto"

**Commit erpnext:** `f62067a`

---

## Para Orbit — deploy acumulado urgente

Cuatro commits pendientes desde último deploy:

| Commit | Qué hace |
|---|---|
| `329027d` | Fix bool angular + búsqueda prefijo (CRÍTICO ya arreglado) |
| `fd64971` | Autocompletar tipo_material/medida desde item_name |
| `5657196` | Sync nest_1d.py (CRÍTICO — sin esto, TypeError en todos los cálculos) |
| `f62067a` | Formato salida presupuesto Excel (este) |

Pasos:
```bash
cd /home/costa/frappe-bench
git -C apps/sistema_industrial pull origin erpnext
bench build --app sistema_industrial
# bench migrate NO requerido — sin DocTypes nuevos
supervisorctl restart all
```

`bench build` requerido por cambios en `.html` y `.js` de la page.

— Gemu
