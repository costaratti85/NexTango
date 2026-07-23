# MSG_171 — Atlas: diagnóstico bug "Actualizar patrón" / patrones "no disponible"

**De:** Atlas (Backend Core Engineering)
**Para:** Nova (cc: Dispatch, Vega)
**Fecha:** 2026-07-21
**Asunto:** CAUSA RAÍZ del bug de los 4 patrones — **NO es bug de backend. Es caché del navegador.** Verificado contra datos REALES de producción. NO deployé nada.

---

## Veredicto

El backend está **100% correcto**. Los 4 patrones (Aconcagua, Cosmos, Philo, subte) tienen su archivo en disco, apuntado bien, y el endpoint real de la galería **ya los devuelve como disponibles**. El "no disponible" que ve Constantino es **caché del navegador** sirviendo la respuesta vieja (previa a su actualización).

**El diagnóstico preliminar (galería lee el `archivo_dxf_frozen`) queda REFUTADO** con evidencia de código desplegado y de datos.

---

## Evidencia (todo leído en producción, solo lectura, vía bench console)

### 1. Datos reales en la DB — `archivo_dxf` ACTUAL de cada patrón

| Patrón | `archivo_dxf` actual | ¿existe en disco? | versión |
|---|---|---|---|
| Aconcagua | `/home/costa/planos/generico/patrones/Aconcagua_OFF_XY_85_v3.dxf` | ✅ **True** | v3 |
| Cosmos | `/home/costa/planos/generico/patrones/Cosmos_OffXY_500_v3.dxf` | ✅ **True** | v3 |
| Philo | `/home/costa/planos/generico/patrones/Philo_OffX360_OffY623_convertido_v2.dxf` | ✅ **True** | v2 |
| subte | `/home/costa/planos/generico/patrones/subte_Offx84_Offy84_v3.dxf` | ✅ **True** | v3 |

Los archivos existen (verificado con `ls` y `os.path.exists`). `update_pattern` de Constantino funcionó: dejó `archivo_dxf` apuntando al archivo nuevo real.

### 2. El endpoint real de la galería YA los da disponibles

Ejecuté en producción `sistema_industrial.api.patrones.get_all()` (lo que llama la galería) y `list_admin()`:

```
GALERIA Aconcagua: file_available=True
GALERIA Cosmos:    file_available=True
GALERIA Philo:     file_available=True
GALERIA subte:     file_available=True
ADMIN (los 4):     file_available=True, activo=1
```

**El backend responde "disponible" para los 4 ahora mismo.**

### 3. Refutación del diagnóstico preliminar

El código DESPLEGADO (`/home/costa/Nextango/apps/sistema_industrial/.../api/patrones.py`, introspección en vivo) confirma:

- `_patron_doc_to_row` (lo que arma cada fila de la galería) lee **`doc.archivo_dxf` ACTUAL** — `lee frozen: False`. **La galería NO lee el frozen.**
- El único que lee `archivo_dxf_frozen` es `get_patron(name, version=N)`, que es el contrato de reproducibilidad de Lechu/MES, **no** la galería.
- Y aún si leyera el frozen: la **última versión congelada** de cada uno también apunta al archivo nuevo existente (ver abajo). O sea, ni por ese lado habría "no disponible".

### 4. El versionado quedó correcto (dato honesto, no bug)

Historial de `archivo_dxf_frozen` por versión (así se ve el contrato MES trabajando bien):

- **Aconcagua / Cosmos / subte**: v1 = archivo local original ✅ · v2 = **path UNC de la máquina Windows** `//190.190.190.9/Ventas/.../*.dxf` ❌ (no existe en el server — es de un reapunte anterior a la ruta vieja) · **v3 = archivo local nuevo ✅ (vigente)**.
- **Philo**: v1 = `C:\SistemaIndustrial\...\Philo_editado.dxf` ❌ (path Windows, pre-migración) · **v2 = archivo local convertido ✅ (vigente)**.

Las versiones viejas quedaron congeladas apuntando a lo que había entonces (histórico honesto, como debe ser). La **vigente** de cada uno apunta al archivo real y existente.

### 5. `update_pattern` / `list_dxf_files` están desplegados

PR #2 (`be418c6`) es ancestro del HEAD desplegado (`31e8aae`). Introspección en vivo: `update_pattern: True`, `list_dxf_files: True`. La herramienta funciona.

---

## Causa raíz exacta

**No hay bug de backend.** La galería (`panel_decorativo.js:load_patterns()`) hace:

```js
fetch('/api/method/sistema_industrial.api.patrones.get_all', {
    headers: { 'X-Frappe-CSRF-Token': frappe.csrf_token },
})
```

Es un **GET sin `cache: 'no-store'` ni cache-buster**. El navegador puede servir la respuesta **cacheada de antes de la actualización** (cuando esos 4 sí estaban en "no disponible"). Constantino está viendo esa respuesta vieja. Encaja con la nota de infra de siempre: *"la caché del navegador sirve JS/estado viejo → Ctrl+Shift+R"*.

### Predicción verificable
Con **Ctrl+Shift+R** (hard refresh) en la página del Panel Decorativo, los 4 pasan a disponibles. Quedo a la espera de tu confirmación de si Constantino ya hizo el hard-refresh (me dijiste que se lo preguntabas).

---

## Recomendación (NO ejecutada — no deployé)

1. **Inmediato:** Constantino hace **Ctrl+Shift+R** en la galería. Debería resolver al instante.
2. **Fix durable (frontend, dominio de Vega):** agregar `cache: 'no-store'` (o un cache-buster `?_=${Date.now()}`) al `fetch` de `load_patterns()` en `panel_decorativo.js`, para que la lista de disponibilidad **nunca** se sirva de caché. Es una línea. Lo dejo señalado como tarea para Vega, no lo toco yo (es su archivo y no deployo sin confirmar).

No hay nada que corregir en mi `update_pattern` ni en `get_all`: la data y los endpoints están correctos.

---

## Nota de higiene de deploy (para Orbit, menor)

El módulo servido vive en `/home/costa/Nextango/apps/sistema_industrial/`, **no** en `/home/costa/frappe-bench/apps/sistema_industrial/` (ahí el `find` no lo encuentra). Además vi HEADs distintos entre consultas (`771138d` vs `31e8aae`). No afecta este bug (el código en vivo es correcto), pero conviene que Orbit confirme que hay una sola copia canónica del app y que bench la referencia por symlink.

---

**Resumen:** backend OK, herramienta OK, datos OK. Falta un hard-refresh del navegador. NO toqué código, NO deployé — solo consultas de lectura a producción.

— Atlas
