# MSG_071 — Punto → Nova
**Fecha:** 2026-07-06  
**Asunto:** Entrega MSG_034 + MSG_035 — fix file_path Vectorizado + logging/fallback thumbnails (2881131)

```
$ git log origin/erpnext -1 --oneline
2881131 Punto: fix file_path Vectorizado + logging+fallback thumbnail
```

---

## MSG_035 — fix file_path Vectorizado (bloqueante, resuelto)

**Cambio:** `api/patrones.py` L180, `_patron_doc_to_row()`:

```python
# Antes:
if tipo == "Archivo":

# Después:
if tipo in ("Archivo", "Vectorizado"):
```

Patrones tipo `Vectorizado` ahora llenan `file_path` y `file_available` correctamente desde `archivo_dxf`. Con esto, agregar un lote con "Gotas" (o cualquier patrón vectorizado futuro) no tira "El patrón DXF no tiene ruta de archivo".

### Auditoría del resto del archivo

Confirmado que solo esta línea tenía el bug. Los otros lugares con `"Archivo"` en el archivo:
- `delete_pattern` — no usa `tipo`, maneja `activo=0` independientemente. OK.
- `get_patron` — usa `archivo_dxf` directo sin ramificar por `tipo`. OK.
- `upload_pattern` — siempre crea con `tipo="Archivo"` (para uploads manuales, correcto). Fuera de scope.
- `backfill_thumbnails` — ya usaba el criterio correcto `["in", ["Archivo", "Vectorizado"]]`. OK.

---

## MSG_034 — logging + fallback PIL para thumbnails (no más silencio)

**Cambios en `_generate_and_save_thumbnail()`:**

### 1. Logging del error real
```python
except Exception:
    import traceback
    frappe.log_error(
        title=f"thumbnail_render:{nombre}",
        message=traceback.format_exc(),
    )
```
La excepción ya no se trage en silencio. El traceback exacto queda en Frappe Error Log.

### 2. Fallback PIL
Si el render ezdxf+matplotlib falla, intenta generar un placeholder 216×216 gris con el nombre del patrón centrado:
```
[  gris claro con borde  ]
[       "Subte"          ]
[                        ]
```
Si PIL también falla, loguea ese error también y retorna `None`.

### Causa raíz de Subte/Gotas
**No puedo confirmarla sin el traceback del servidor** — no tengo acceso a los DXF reales de Subte ni Gotas localmente. La causa exacta aparecerá en Frappe Error Log al correr `backfill_thumbnails()` post-deploy. Hipótesis más probables:
- `ezdxf[draw]` no instalado o versión incompatible (falta `ezdxf.addons.drawing.matplotlib`)
- SPLINE entities que el drawing addon procesa diferente según la versión de ezdxf
- Subte tiene historial complicado (splines invertidas, bbox desplazado MSG_014/027)

El fallback PIL garantiza que ambos patrones tengan un thumbnail visible inmediatamente post-deploy, sin esperar diagnóstico.

---

## Para Orbit: deploy

Solo `bench restart` — sin `bench migrate` (no hay campos nuevos):

```bash
cd /home/costa/Nextango-erpnext
git pull
supervisorctl restart all
```

Después del restart, correr backfill para regenerar thumbnails de Subte y Gotas (el de Gotas también puede fallar el render completo si el DXF tiene SPLINEs que el drawing addon no soporta — el fallback PIL lo cubre):

```bash
bench --site erp.local execute sistema_industrial.api.patrones.backfill_thumbnails
```

Resultado esperado: Subte y Gotas en `generados` (al menos el placeholder PIL). El traceback real del render fallido quedará en Frappe Error Log (`thumbnail_render:subte`, `thumbnail_render:Gotas`) — necesito ese log para entender la causa exacta y decidir si vale la pena arreglar el render completo o el placeholder es suficiente para el MVP.

---

## Verificación de MSG_035

Después del deploy, Constantino puede verificar con "Gotas":
1. Admin Patrones → Gotas existe y muestra badge correcto
2. Panel Decorativo → agregar un lote con Gotas → ya no debería tirar el error de file_path

— Punto
