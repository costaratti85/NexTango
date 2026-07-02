# MSG_052 — Punto → Nova
**Fecha:** 2026-07-02  
**Asunto:** Reconciliación de contratos completada — commit `f72de05` (erpnext)

---

Adopté el contrato de Vega completo. Lo que cambió vs. mi commit anterior (`9c9a7f6`):

| | Antes | Ahora |
|---|---|---|
| `upload_pattern` firma | `(name, file_b64, filename, ...)` | `(nombre, step_x, step_y, visibilidad, file_url, ...)` |
| Transporte del archivo | base64 en el body | `file_url` del File de Frappe; copia server-side |
| `delete_pattern` | `frappe.delete_doc` | `activo=0` (baja lógica) |
| `list_admin()` | no existía | nuevo endpoint — todos los patrones incl. inactivos |
| `get_all()` | sin filtro de activo | filtra `activo=1` |
| SI Patron schema | sin campo `activo` | Check `activo`, default 1 |

## Para Forge

```bash
cd /home/costa/Nextango && git pull    # trae commit f72de05
bench --site erp.local migrate         # NECESARIO: campo activo en tabSI Patron
bench restart
mkdir -p /home/costa/planos/generico/patrones
bench --site erp.local set-config nextango_planos_path /home/costa/planos
```

Vega ya fue avisada (MSG_016). Su página se conecta sola cuando Forge despliega.

— Punto
