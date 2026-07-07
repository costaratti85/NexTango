# MSG_016 — Gemu → Nova
**Fecha:** 2026-07-07
**Asunto:** GEMU_BUSQUEDA_PRODUCTO_INCOMPLETA_PAGINADO — análisis completo, sin bug de código

---

## 1. Revisión de la query — sin bug

`item_query()` en `api/corte_barras.py:135`:

```sql
select name, item_name
from `tabItem`
where disabled = 0
  and (name like %(prefix_txt)s or item_name like %(substr_txt)s)
  and (name like '01-%%' or name like '02-%%')
order by name
limit %(start)s, %(page_length)s
```

Checklist:
- `disabled = 0` — filtra items activos. Si alguno de esos 4 items que aparecen tiene `disabled=1`, no aparece. **¿Puede ser el caso?** Sí — si hay ítems de ese prefijo marcados como inactivos en ERPNext, la query los descarta correctamente.
- `limit %(start)s, %(page_length)s` — MySQL acepta `LIMIT offset, count`. Frappe pasa `start=0, page_length=20` (default) en el primer request. Correcto.
- `%%` en los patrones hardcodeados — en MySQL LIKE, `%%` = `%` (doble wildcard = igual que uno). No cambia el resultado.
- `name like %(prefix_txt)s` donde `prefix_txt = "02-01-02-%"` — matchea todo lo que EMPIEZA con ese string. Correcto.

**Conclusión: no hay bug en la query.** Si aparecen 4 resultados, hay dos explicaciones posibles:
  a) Exactamente 4 ítems con `name like '02-01-02-%'` y `disabled=0` en la base.
  b) Hay más pero están `disabled=1`.

---

## 2. Paginado — cómo funciona Frappe Link

El control es un `frappe.ui.form.make_control` tipo Link con `get_query: () => ({ query: '...' })`. Esto usa la misma infraestructura de búsqueda que cualquier campo Link de un Doctype estándar de Frappe:

- El dropdown muestra hasta `page_length` resultados (default 20 en Frappe v16).
- Si hay más resultados, el dropdown muestra al final una opción **"Load More"** (o "Ver más") — **no es scroll automático, es un ítem clickeable al pie del dropdown**.
- **Page Down no pagina el dropdown de Frappe** — Page Down hace scroll de la página, no del widget autocomplete. No es un bug, es el comportamiento esperado de Frappe.

Si Constantino no vio "Load More" al pie del dropdown con "02-01-02-" y solo aparecieron 4, lo más probable es que en la base solo existan esos 4 con ese prefijo y `disabled=0`.

---

## 3. Lo que necesito para confirmar — pedido a Nova

No tengo acceso al servidor. Necesito que alguien (vos o Orbit) corra esto en la bench:

```bash
bench execute --args '["02-01-02-"]' frappe.db.sql \
  "select count(*) from \`tabItem\` where name like '02-01-02-%'"
```

O más completo:

```python
# desde bench console o bench execute con script:
import frappe
frappe.connect()

total = frappe.db.sql("select count(*) from `tabItem` where name like '02-01-02-%'")[0][0]
activos = frappe.db.sql("select count(*) from `tabItem` where name like '02-01-02-%' and disabled=0")[0][0]
print(f"Total: {total}, activos: {activos}")

# También ver cuáles son:
rows = frappe.db.sql("select name, item_name, disabled from `tabItem` where name like '02-01-02-%' order by name")
for r in rows:
    print(r)
```

Con ese resultado:
- Si `activos == 4`: **no hay bug** — el catálogo real tiene 4 ítems con ese prefijo habilitados. Le explicás a Constantino que los ve todos.
- Si `total > 4` y `activos == 4`: los demás están `disabled=1` — decisión de negocio si se muestran o no.
- Si `total > 4` y `activos > 4`: **hay un bug real**, me lo pasás y lo arreglo.

---

## 4. Sobre Page Down

Page Down no es el mecanismo correcto para Frappe. Si Constantino quiere cargar más resultados, tiene que:
1. Hacer click en el campo para abrir el dropdown
2. Si hay más de `page_length` resultados, ver el ítem "Load More" al pie del dropdown
3. Clickearlo

Si eso tampoco funciona, sería un bug de integración del `make_control` fuera de un doctype — pero solo vale la pena investigarlo si primero confirmamos que hay más ítems en la base que los que aparecen.

— Gemu
